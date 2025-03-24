# API 使用说明

本项目使用百度百科API来采集数据。以下是主要API的使用说明。

## 配置设置

1. 首先需要在百度开发者平台申请API密钥：
   - 访问[百度开发者中心](https://developer.baidu.com/)
   - 创建应用并获取API Key和Secret Key

2. 配置密钥：
   ```ini
   [baidu]
   api_key=your_api_key_here
   secret_key=your_secret_key_here
   ```

## 主要功能模块

### 1. 百科搜索 (search_baike.py)

```python
from baidu-search-env.search_baike import search_baike

# 搜索单个词条
result = search_baike("伤寒论")

# 批量搜索
keywords = ["伤寒论", "金匮要略"]
results = [search_baike(keyword) for keyword in keywords]
```

### 2. 数据采集 (collect_books_v2.py)

```python
from baidu-search-env.collect_books_v2 import collect_book

# 采集单本书籍信息
book_info = collect_book("伤寒论")

# 采集并保存到JSON
book_info.save_to_json("books_json/伤寒论.json")
```

## API限制

1. 请求频率限制：
   - 每个IP每秒不超过10次请求
   - 每个用户每天总请求次数不超过10000次

2. 内容限制：
   - 仅支持采集公开的百科内容
   - 部分词条可能因百度百科政策限制无法访问

## 错误处理

本项目使用tenacity库进行自动重试，主要处理以下错误：
- 网络连接超时
- API调用限制
- 服务器临时错误

错误重试策略：
- 最多重试3次
- 重试间隔呈指数增长
- 特定错误码（如403）不进行重试

## 最佳实践

1. 大批量采集建议：
   - 设置适当的延时（推荐1-2秒）
   - 使用代理IP轮换
   - 分批次进行采集

2. 数据存储：
   - 定期备份JSON文件
   - 采集完成后验证JSON格式完整性
