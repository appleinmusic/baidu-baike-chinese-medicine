# 百度百科中医药数据采集工具

这个项目是一个用于从百度百科采集中医药相关数据的工具。

## 功能特性

- 自动采集百度百科中的中医药条目内容
- 支持批量处理多个条目
- 结果保存为JSON格式，方便后续处理
- 支持断点续传，避免重复采集
- 提供数据清洗功能，优化采集结果的质量
- 支持提取并整理关键数据信息

## 安装说明

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd [项目目录]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置API密钥：
   - 复制`baidu-search-env/config.example.ini`为`config.ini`
   - 在config.ini中填入你的百度API密钥

## 使用方法

1. 采集数据：
```bash
python baidu-search-env/collect_books_v2.py
```

2. 搜索百科：
```bash
python baidu-search-env/search_baike.py
```

3. 清洗数据：
```bash
python clean_books_json.py
```

## 目录结构

- `baidu-search-env/`: 主要代码目录
  - `collect_books_v2.py`: 数据采集脚本
  - `search_baike.py`: 百科搜索脚本
  - `config.example.ini`: 配置文件示例
- `books_json/`: 原始采集结果保存目录
- `cleaned_books_json/`: 清洗后的数据保存目录
- `clean_books_json.py`: 数据清洗脚本
- `clean_urls.txt`: URL清理配置文件

## 数据处理流程

1. 使用`collect_books_v2.py`从百度百科采集原始数据
2. 数据存储在`books_json/`目录
3. 运行`clean_books_json.py`进行数据清洗和整理
4. 清洗后的数据保存在`cleaned_books_json/`目录

## 注意事项

- 请确保API密钥配置正确
- 遵守百度API的使用限制和条款
- 建议采集时设置适当的延时，避免请求过频
- API密钥等敏感信息不要提交到代码仓库
- 定期备份重要的采集数据

## License

MIT License
