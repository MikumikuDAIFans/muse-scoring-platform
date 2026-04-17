# Muse Scoring Platform

一个用于图片双维度人工标注的 Web 平台。普通用户可以对图片进行打分，管理员可以查看进度和基础统计。

## 功能

- 用户注册、登录
- 图片双维度评分
  - 美学表现
  - 细节完成度
- 管理员统计面板
- 图片批量导入
- 评分结果直接入库

## 技术栈

- 前端：Vue 3、Vite、Pinia、Axios
- 后端：FastAPI、SQLAlchemy、asyncpg
- 数据库：PostgreSQL

## 项目结构

```text
frontend/    前端代码
backend/     后端 API、鉴权、异步落库逻辑
images/      本地图片目录（导入脚本读取这里）
sql/         数据库初始化 SQL
README.md
```

## 本地开发

1. 安装依赖

```powershell
cd frontend
npm install

cd ..\backend
pip install -r requirements.txt
```

2. 准备环境变量

项目根目录提供了 `.env.example` 可作为参考。后端至少需要：

```env
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=
R2_PUBLIC_URL=
```

3. 启动前后端

前端：

```powershell
cd frontend
npm run dev
```

后端：

```powershell
cd backend
granian --interface asgi --host 0.0.0.0 --port 8000 main:app
```

## 图片导入

将待标注图片放入项目根目录的 `images/` 后，执行：

```powershell
cd backend
python import_images.py
```

导入脚本会：

- 上传图片到配置好的 R2
- 将图片 URL 写入 `images` 表

## 评分流转

1. 用户请求待标注图片任务
2. 前端提交评分到 `/api/tasks/{task_id}/submit` 或兼容接口 `/api/score`
3. 后端直接写入 PostgreSQL

## 管理端可见信息

- 总图片数
- 已标注图片数
- 总评分数
- 今日评分数
- 活跃用户数
- 当前待落库数量固定为 0（已移除 Redis 队列）

## 说明

- `README.md` 仅保留项目说明与开发信息
- 部署与上线操作请使用单独文档，不在本 README 中展开
