# Architecture Decision Record

## 技术栈
- **Web 框架**: 使用 FastAPI | **理由**: 需要异步支持且类型安全 | *2026-06-06*

## 数据存储
- **存储方案**: 使用 SQLite | **理由**: JSON 文件查询太慢 | *2026-06-06*
