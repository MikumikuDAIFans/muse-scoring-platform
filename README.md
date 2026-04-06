# Muse Scoring Platform

一个基于 FastAPI + Vue 3 的图片评分管理平台，支持用户注册登录、图片打分、后台管理和数据导出功能。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus
- **后端**: FastAPI + SQLAlchemy (async) + asyncpg
- **数据库**: PostgreSQL 17 + PgBouncer (连接池)
- **缓存**: Redis 7
- **反向代理**: Nginx
- **容器化**: Docker Compose

## 功能特性

- **用户系统**: 注册、登录、JWT 认证、账户锁定机制
- **图片打分**: 美观度与完整性双维度评分（1-10分）
- **后台管理**: 用户管理、图片管理、查看统计信息
- **数据导出**: 支持 CSV/JSONL 格式，可按时间范围、用户ID筛选
- **异步架构**: 使用 Redis 队列处理耗时操作，PgBouncer 连接池优化并发

## 快速开始

### 前置要求

- Docker & Docker Compose
- Node.js 18+（仅开发模式需要）

### 启动服务

```bash
# 克隆仓库
git clone <your-repo-url>
cd MuseProject

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 修改密钥等配置

# 启动所有服务
docker compose up -d --build

# 查看服务状态
docker compose ps
```

服务启动后：
- 前端访问: http://localhost:8080
- 后端 API: http://localhost:8000

### 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123456 |

> **首次部署**: 系统会自动创建管理员账户，请登录后立即修改密码。

### 导入图片

将图片放入 `images/` 目录后执行：

```bash
docker compose exec fastapi python import_images.py
```

## 项目结构

```
├── backend/           # FastAPI 后端
│   ├── main.py        # 应用入口
│   ├── routes.py      # 用户路由（打分相关）
│   ├── auth_routes.py # 认证路由
│   ├── admin_routes.py# 管理后台路由
│   ├── export_routes.py # 数据导出路由
│   ├── models.py      # SQLAlchemy 模型定义
│   ├── schemas.py     # Pydantic 请求/响应模型
│   ├── auth.py        # JWT 与密码工具
│   ├── database.py    # 数据库连接
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── views/     # 页面组件
│   │   ├── api/       # API 调用封装
│   │   └── App.vue
│   └── package.json
├── sql/               # 数据库脚本
│   ├── schema.sql     # 建表 DDL
│   └── import_test_data.sql
├── images/            # 本地图片存储（需导入后使用）
├── docker-compose.yml # 服务编排
├── nginx.conf         # Nginx 配置
└── .env               # 环境变量（不提交到 Git）
```

## API 文档

启动服务后访问 http://localhost:8000/docs 查看 Swagger UI 自动生成的 API 文档。

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/register | 用户注册 |
| POST | /api/login | 用户登录 |
| GET | /api/next-image | 获取下一张待打分图片 |
| POST | /api/score | 提交评分 |
| GET | /api/admin/users | 获取用户列表（管理员） |
| GET | /api/export | 导出评分数据（管理员） |

### 数据导出示例

```bash
# 获取 JWT Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}' | jq -r '.access_token')

# CSV 全量导出
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/export?format=csv -o scores.csv

# 按时间范围导出
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/export?start=2026-04-01&end=2026-04-07" -o scores.csv

# 按用户导出
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/export?user_id=3" -o user_scores.csv
```

## 数据库 Schema

- **users**: 用户账户（用户名、密码哈希、角色、锁定状态）
- **images**: 图片记录（URL、打分次数、软删除标记）
- **scores**: 评分记录（关联用户和图片、美观度分数、完整性分数）
- **audit_exports**: 审计日志（记录管理员导出操作）

详见 [sql/schema.sql](sql/schema.sql)。

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接字符串 | postgresql+asyncpg://postgres:postgres@postgres:5432/scoring |
| REDIS_URL | Redis 连接字符串 | redis://redis:6379 |
| JWT_SECRET | JWT 签名密钥 | （需自行设置强密钥） |
| ADMIN_USERNAME | 初始管理员用户名 | admin |
| ADMIN_PASSWORD | 初始管理员密码 | admin123456 |
| TURNSTILE_SITE_KEY | Cloudflare Turnstile 站点密钥 | （用于人机验证） |
| TURNSTILE_SECRET_KEY | Cloudflare Turnstile 密钥 | （用于人机验证） |

## 生产部署建议

1. 修改 `.env` 中的 `JWT_SECRET` 为强随机密钥
2. 修改默认管理员密码
3. 配置真实的 Cloudflare Turnstile 密钥
4. 使用 HTTPS（通过 Nginx 配置 SSL 证书）
5. 定期备份 PostgreSQL 数据库

## License

MIT
