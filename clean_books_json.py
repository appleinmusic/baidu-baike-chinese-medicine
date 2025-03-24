import json
import os
import re
import time
from typing import Dict, Any
import requests
import logging

class BookJsonCleaner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://qianfan.bj.baidubce.com/v2/chat/completions"
        self.max_retries = 3
        self.retry_delay = 2  # 秒

    def extract_year(self, text: str) -> str:
        """提取年代中的数字"""
        year_match = re.search(r'(\d{3,4})', text)
        return year_match.group(1) if year_match else text

    def extract_info_from_text(self, text: str) -> Dict[str, str]:
        """从文本中提取书籍信息"""
        info = {
            "书名": None,
            "朝代": None,
            "年代": None,
            "作者": None
        }
        
        # 使用严格的模式匹配书名（必须在"书名："后面，且被《》或""包围）
        book_name_match = re.search(r'书名[：:]\s*[《"](.*?)[》"]', text)
        if book_name_match:
            info["书名"] = book_name_match.group(1).strip()

        # 查找作者信息（各种格式）
        author_patterns = [
            # 匹配"作者："后的信息
            r'作者[：:]\s*([^，。\n（(]*?[^，。\n（(\s])',
            # 匹配"朝·作者名"格式
            r'([前后东西南北]?[秦汉晋南北朝隋唐五代宋元明清][·•][\w]+)',
            # 匹配括号中的作者信息
            r'作者[：:][^）]*?[（(]([\w]+)[）)]'
        ]
        
        for pattern in author_patterns:
            author_match = re.search(pattern, text)
            if author_match:
                info["作者"] = author_match.group(1).strip()
                break

        # 查找朝代信息（优先使用明确标记的朝代信息）
        dynasty_match = re.search(r'([前后东西南北]?[秦汉晋南北朝隋唐五代宋元明清])(?:[·•]|(?:朝)|(?:代))', text)
        if dynasty_match:
            info["朝代"] = dynasty_match.group(1) + "代"

        # 查找年代信息（优先提取阿拉伯数字年份）
        # 首先尝试直接匹配括号中的年份
        year_matches = re.finditer(r'(?:[（(].*?)?(\d{3,4})(?:年)?(?:[）)]|$)', text)
        for match in year_matches:
            year = match.group(1)
            if 1000 <= int(year) <= 2025:  # 合理的年份范围
                info["年代"] = year
                break

        return info

    def clean_book_data(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        # 首先尝试从主要思想和原文中提取信息
        extracted_info = {"书名": None, "朝代": None, "年代": None, "作者": None}
        
        for field in ["主要思想", "原文"]:
            if book_data.get(field):
                info = self.extract_info_from_text(book_data[field])
                for key, value in info.items():
                    if value and not extracted_info[key]:
                        extracted_info[key] = value
        
        # 如果成功提取到所有信息，直接返回
        if all(extracted_info.values()):
            for key, value in extracted_info.items():
                if value:
                    book_data[key] = value
                    logging.info(f"从原文提取{key}: {value}")
            return book_data

        # 如果无法从原文提取完整信息，则使用API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Qianfan-App-ID": "app-yWnkbgGR"
        }
        
        # 获取参考信息
        reference_text = ""
        if book_data.get("主要思想"):
            reference_text += book_data["主要思想"] + "\n"
        if book_data.get("原文"):
            reference_text += book_data["原文"]

        # 构建提示文本
        prompt = f"""请根据以下参考信息，提供准确的书籍信息：
参考信息：
{reference_text}

请提供：
1. 准确的书名（不要包含书名号《》）
2. 朝代（如果有，不要包含"朝"或"代"字）
3. 具体年代（只需提供阿拉伯数字年份）
4. 作者名字（尽量简短，不要包含朝代和简介）

请只返回四行信息，每行一个值，格式如下：
书名
朝代
年份数字
作者姓名

示例输出：
杂病源流犀烛
清
1773
沈金鳌"""

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json={
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "model": "ernie-4.5-8k-preview",
                    "stream": False,
                    "temperature": 0.1,
                    "system": "你是一个专业的中医典籍整理专家"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    logging.debug(f"模型返回内容: {content}")

                    # 分行处理返回的内容
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    if len(lines) >= 4:  # 确保有足够的行数
                        # 更新书籍信息
                        book_data["书名"] = lines[0].strip('《》""')
                        book_data["朝代"] = lines[1]
                        # 处理年代，只保留数字
                        year_match = re.search(r'(\d{3,4})', lines[2])
                        if year_match:
                            book_data["年代"] = year_match.group(1)
                        # 处理作者，去除括号内容和朝代信息
                        author = lines[3].split('，')[0].split('（')[0].strip()
                        book_data["作者"] = author

                        logging.info(f"已更新：{book_data}")
                    else:
                        logging.error(f"返回内容格式不正确: {content}")
            else:
                logging.error(f"API请求失败: {response.status_code} - {response.text}")
                
                # 如果是认证错误，可以休眠一段时间后重试
                if response.status_code == 401:
                    time.sleep(self.retry_delay)
                    return self.clean_book_data(book_data)
                    
        except requests.exceptions.RequestException as e:
            logging.error(f"请求异常: {str(e)}")
        except Exception as e:
            logging.error(f"处理时出错: {str(e)}")

        return book_data

    def process_directory(self, directory_path: str):
        files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        total_files = len(files)
        success_count = 0
        error_files = []
        
        logging.info(f"开始处理，共发现 {total_files} 个JSON文件")
        
        for idx, filename in enumerate(files, 1):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        book_data = json.load(f)
                    
                    # 清洗数据
                    cleaned_data = self.clean_book_data(book_data)
                    
                    # 创建输出目录
                    output_directory = "cleaned_books_json"
                    os.makedirs(output_directory, exist_ok=True)
                    
                    # 根据更新后的书名生成新的文件名
                    new_filename = filename
                    if cleaned_data.get("书名"):
                        new_filename = cleaned_data["书名"].strip('《》') + ".json"
                    
                    # 如果有年代，只保留数字
                    if cleaned_data.get("年代"):
                        year_match = re.search(r'(\d{3,4})', cleaned_data["年代"])
                        if year_match:
                            cleaned_data["年代"] = year_match.group(1)
                    
                    # 保存更新后的数据到新目录
                    output_path = os.path.join(output_directory, new_filename)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                    
                    if new_filename != filename:
                        logging.info(f"已处理: {filename} -> {new_filename}")
                    else:
                        logging.info(f"已处理: {filename}")
                    
                    success_count += 1
                except Exception as e:
                    error_files.append(filename)
                    logging.error(f"处理 {filename} 时出错: {str(e)}")

        logging.info(f"处理完成！成功：{success_count}/{total_files}")
        if error_files:
            logging.info(f"处理失败的文件：{', '.join(error_files)}")

def main():
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # API密钥 - ModelBuilder权限
    api_key = "bce-v3/ALTAK-ALLGFgjnUaTnSWL5T87ks/ae415fb38cd32d4f7687e1dfa83e4778fe6ad077"
    
    logging.info("初始化清洗器...")
    cleaner = BookJsonCleaner(api_key)
    
    # 处理books_json目录下的所有JSON文件
    books_directory = "books_json"
    cleaner.process_directory(books_directory)

if __name__ == "__main__":
    main()
