# Muse Scoring Platform - 图片评分管理平台

> 一个面向大众的图片双维度评分平台，用户可以通过"美学表现"和"细节完成度"两个维度对图片进行打分。

---

## 📖 目录导航

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [技术栈详解](#技术栈详解)
- [🚀 快速上手（从零到上线）](#-快速上手从零到上线)
- [本地开发部署（Windows）](#本地开发部署windows)
- [☁️ 生产环境部署（Cloudflare 生态）](#️-生产环境部署cloudflare-生态)
- [详细操作指南](#详细操作指南)
- [日常运维](#日常运维)
- [故障排查](#故障排查)
- [数据备份](#数据备份)
- [安全加固](#安全加固)
- [常见问题 FAQ](#常见问题-faq)

---

## 项目简介

### 这是什么？

这是一个基于 Web 的图片评分平台，主要功能包括：

- **用户注册登录**：任何人都可以注册账号参与评分
- **双维度打分**：每张图片需要从"美学表现"和"细节完成度"两个维度分别打分（1-10分）
- **后台管理**：管理员可以查看统计信息、用户排行、导出数据
- **数据导出**：支持 CSV 和 JSONL 格式，可按时间范围和用户筛选

### 适用场景

- 图片质量评估和标注
- 众包数据采集
- 机器学习训练集标注
- 图片质量对比研究

---

## 系统架构

### 整体架构图

```
用户浏览器
    ↓
[Nginx] 反向代理（端口 8080）
    ↓ 静态文件 → 前端页面
    ↓ /api/* → FastAPI
    ↓
[FastAPI] 后端服务（端口 8000）
    ↓
[PgBouncer] 连接池（端口 6432）← 保护数据库不被大量连接压垮
    ↓
[PostgreSQL] 数据库（端口 5432）← 存储用户、图片、评分数据
    
[Redis] 缓存（端口 6380）← 临时存储评分数据，批量写入数据库
```

### 五个核心服务说明

| 服务名称 | 作用 | 端口 | 重要程度 |
|---------|------|------|---------|
| postgres | 数据库，存储所有数据 | 5432 | ⭐⭐⭐⭐⭐ 核心 |
| redis | 缓存，加速评分提交 | 6380 | ⭐⭐⭐⭐ 重要 |
| pgbouncer | 连接池，保护数据库 | 6432 | ⭐⭐⭐ 保护 |
| fastapi | 后端服务，处理业务逻辑 | 8000 | ⭐⭐⭐⭐⭐ 核心 |
| nginx | 反向代理，统一入口 | 8080 | ⭐⭐⭐⭐ 重要 |

### 工作流程

1. 用户打开浏览器访问 `http://你的IP:8080`
2. Nginx 返回前端页面
3. 用户注册/登录，获取身份令牌
4. 用户开始评分，评分先存入 Redis（快速响应）
5. 后台自动将 Redis 中的评分批量写入 PostgreSQL（可靠存储）
6. 管理员可以查看统计、导出数据

---

## 技术栈详解

### 后端技术

| 技术 | 版本 | 作用 | 为什么选它 |
|------|------|------|-----------|
| FastAPI | 0.115.x | Web 框架，处理 HTTP 请求 | 性能好，自动生成交互式 API 文档 |
| Granian | 1.7.x | ASGI 服务器，运行 FastAPI | Rust 编写，性能极高 |
| SQLAlchemy | 2.0.x | ORM 框架，操作数据库 | 支持异步操作，代码更优雅 |
| asyncpg | 0.30.x | PostgreSQL 异步驱动 | 比传统驱动快 3-5 倍 |
| python-jose | - | JWT 令牌签发和验证 | 轻量级，易于使用 |
| passlib+bcrypt | - | 密码加密 | 业界标准，安全可靠 |
| httpx | - | HTTP 客户端 | 用于调用外部验证服务 |

### 前端技术

| 技术 | 版本 | 作用 | 特点 |
|------|------|------|------|
| Vue 3 | - | 前端框架 | 响应式，组件化开发 |
| Vite | - | 构建工具 | 极速热更新，打包快速 |
| Pinia | - | 状态管理 | 管理用户登录状态和评分数据 |
| Axios | - | HTTP 客户端 | 自动附加认证令牌 |

### 基础设施

| 技术 | 版本 | 作用 | 优势 |
|------|------|------|------|
| PostgreSQL | 17 | 关系型数据库 | ACID 事务，数据一致性保证 |
| PgBouncer | latest | 连接池 | 防止大量连接压垮数据库 |
| Redis | 7 | 缓存/队列 | 内存操作，速度极快 |
| Docker Compose | - | 容器编排 | 一键启动所有服务 |
| Nginx | alpine | 反向代理 | 统一入口，静态文件服务 |

---

## 🚀 快速上手（从零到上线）

> 📌 **目标**：从 0 开始，将项目部署到 Cloudflare 生态并正式上线
> ⏱️ 预计耗时：30-45 分钟
> 
> 👉 **详细步骤请参考**：[DEPLOY-CLOUDFLARE.md](DEPLOY-CLOUDFLARE.md)

### 快速路线图

```
1. 创建 R2 存储 (5min)     → Cloudflare Dashboard → R2
2. 创建 Turnstile (2min)    → Cloudflare Dashboard → Turnstile
3. 创建数据库 (5min)         → Neon / Supabase（免费）
4. 创建 Redis (3min)         → Upstash（免费）
5. 部署后端 (10min)          → Railway / Render / VPS
6. 部署前端 (5min)           → Cloudflare Pages
7. 导入图片 (2min)           → python import_images.py
8. 验证上线                 → 浏览器访问前端域名
```

### 核心资源速查

| 资源 | 推荐服务 | 免费额度 |
|------|---------|---------|
| 前端托管 | Cloudflare Pages | 无限带宽，500 次构建/月 |
| 图片存储 | Cloudflare R2 | 10GB 存储，100 万次读/月 |
| 人机验证 | Cloudflare Turnstile | 完全免费 |
| 数据库 | Neon | 500MB 存储 |
| Redis | Upstash | 10K 命令/天 |
| 后端托管 | Railway | $5/月免费额度 |

---

## 本地开发部署（Windows）

> 💡 **说明**：本节适用于本地开发和测试。生产环境部署请参考 [☁️ 生产环境部署（Cloudflare 生态）](#️-生产环境部署cloudflare-生态) 章节。

### 第一步：安装 Docker

> 💡 **什么是 Docker？**  
> Docker 就像一个"集装箱"，把你的应用程序和它需要的所有东西（代码、库、配置）打包在一起。这样无论在什么机器上，都能保证运行结果一致。

#### Windows 系统

1. 访问 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop/)
2. 下载 Windows 版本安装包
3. 双击安装包，按照提示完成安装
4. 安装完成后重启电脑
5. 打开 Docker Desktop，等待状态栏显示绿色鲸鱼图标

#### 验证安装

打开 PowerShell，输入：
```powershell
docker --version
docker compose version
```

如果看到类似输出，说明安装成功：
```
Docker version 24.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

### 第二步：获取项目代码

#### 方式一：从 GitHub 克隆（推荐）

```powershell
# 克隆项目到本地
git clone https://github.com/MikumikuDAIFans/muse-scoring-platform.git

# 进入项目目录
cd muse-scoring-platform
```

#### 方式二：直接下载 ZIP

1. 访问项目 GitHub 页面
2. 点击绿色 "Code" 按钮
3. 选择 "Download ZIP"
4. 解压到任意目录
5. 打开 PowerShell，进入解压后的目录

### 第三步：准备配置文件

项目根目录下有一个 `.env.example` 文件，这是配置模板。

```powershell
# 复制模板文件
Copy-Item .env.example .env

# 用记事本打开编辑
notepad .env
```

#### 配置文件详解

打开 `.env` 文件，你会看到以下内容：

```env
# 数据库连接地址
# 格式：postgresql+异步驱动://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/scoring

# Redis 连接地址
# 格式：redis://主机:端口
REDIS_URL=redis://redis:6379

# JWT 签名密钥（用于用户登录认证）
# ⚠️ 生产环境必须修改为随机字符串！
JWT_SECRET=your-secret-key-change-in-production

# 初始管理员账号密码
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456

# Cloudflare Turnstile 人机验证密钥（可选）
# 留空表示关闭验证（开发环境推荐）
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
```

#### 🔑 生成安全的 JWT 密钥

**重要！** 生产环境必须修改 `JWT_SECRET` 为强随机密钥。

**Windows PowerShell 生成方法：**
```powershell
# 生成 64 位随机密钥
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

复制生成的密钥，替换 `.env` 中的 `your-secret-key-change-in-production`。

---

## 快速部署（本地测试）

### 一键启动所有服务

在项目根目录执行：

```powershell
docker compose up -d --build
```

#### 命令解释

| 参数 | 含义 |
|------|------|
| `docker compose` | Docker 编排工具 |
| `up` | 启动服务 |
| `-d` | 后台运行（不占用终端） |
| `--build` | 重新构建镜像 |

#### 预期输出

```
[+] Running 5/5
 ✔ Network museproject_default     Created
 ✔ Container museproject-postgres-1    Started
 ✔ Container museproject-redis-1       Started
 ✔ Container museproject-pgbouncer-1   Started
 ✔ Container museproject-fastapi-1     Started
 ✔ Container museproject-nginx-1       Started
```

### 检查服务状态

```powershell
docker compose ps
```

正常情况应该看到 5 个服务都是 `running` 状态：

```
NAME                    STATUS          PORTS
museproject-fastapi-1   Up (healthy)    0.0.0.0:8000->8000/tcp
museproject-nginx-1     Up              0.0.0.0:8080->80/tcp
museproject-pgbouncer-1 Up              0.0.0.0:6432->6432/tcp
museproject-postgres-1  Up (healthy)    0.0.0.0:5432->5432/tcp
museproject-redis-1     Up (healthy)    0.0.0.0:6380->6379/tcp
```

### 查看服务日志

如果某个服务启动失败，可以查看日志排查问题：

```powershell
# 查看所有服务日志
docker compose logs

# 查看特定服务日志（如 fastapi）
docker compose logs fastapi

# 实时跟踪日志（按 Ctrl+C 退出）
docker compose logs -f fastapi
```

### 访问系统

服务启动成功后：

- **前端页面**：http://localhost:8080
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs （交互式 Swagger UI）

### 默认管理员账号

| 字段 | 值 |
|------|-----|
| 用户名 | admin |
| 密码 | admin123456 |

> ⚠️ **首次登录后请立即修改密码！**

---

## ☁️ 生产环境部署（Cloudflare 生态）

> 💡 **重要说明**：本节介绍如何在 Cloudflare 生态中部署生产环境。Windows Docker Compose 仅用于本地开发和测试。

### 为什么选择 Cloudflare 生态？

| 优势 | 说明 |
|------|------|
| **全球 CDN** | Cloudflare 边缘节点覆盖全球，用户访问速度极快 |
| **免费额度** | Workers、Pages、R2、D1 都有 generous 的免费额度 |
| **自动 HTTPS** | 无需手动配置 SSL 证书，Cloudflare 自动处理 |
| **DDoS 防护** | 内置企业级 DDoS 防护 |
| **Turnstile 验证** | 免费的人机验证，替代 reCAPTCHA |
| **零信任网络** | Cloudflare Tunnel 无需开放端口 |

### 生产架构概览

```
用户浏览器
    ↓
[Cloudflare CDN] 全球加速 + DDoS 防护 + HTTPS
    ↓
[Cloudflare Pages] 前端静态资源托管（Vue 3 构建产物）
    ↓
[Cloudflare Workers] API 路由转发（可选，或直接连接后端）
    ↓
[云服务器/VPS] FastAPI 后端服务（Granian ASGI）
    ↓
[Neon/Supabase] PostgreSQL 云数据库（或自建）
[Upstash] Redis 云缓存（或自建）
```

### 部署方案选择

根据你的预算和技术水平，我们提供两种方案：

| 方案 | 成本 | 复杂度 | 推荐场景 |
|------|------|--------|---------|
| **方案 A：全 Cloudflare 托管** | 极低（接近免费） | 中等 | 中小型项目，追求低成本 |
| **方案 B：混合部署** | 低到中等 | 较低 | 需要更强后端性能 |

---

### 方案 A：全 Cloudflare 托管部署

> 前端使用 Cloudflare Pages，后端使用 Cloudflare Workers + D1/Neon 数据库

#### 前置准备

1. **注册 Cloudflare 账号**
   - 访问 [Cloudflare 官网](https://dash.cloudflare.com/sign-up)
   - 使用邮箱注册并完成验证

2. **绑定域名（可选但推荐）**
   - 将你的域名 DNS 托管到 Cloudflare
   - 在 Cloudflare Dashboard 中添加站点

3. **安装 Wrangler CLI**
   ```powershell
   # 安装 Cloudflare Workers CLI 工具
   npm install -g wrangler
   
   # 登录 Cloudflare
   wrangler login
   ```

#### 第一步：部署前端到 Cloudflare Pages

1. **构建前端产物**

   在你的 Windows 本地执行：
   ```powershell
   cd frontend
   npm install
   npm run build
   ```

   构建完成后，会在 `frontend/dist/` 目录生成静态文件。

2. **通过 Dashboard 部署（推荐新手）**

   - 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
   - 左侧菜单选择 **Workers & Pages** → **Pages**
   - 点击 **Connect to Git**
   - 选择你的 GitHub 仓库 `muse-scoring-platform`
   - 配置构建设置：
     - **Framework preset**: Vue
     - **Build command**: `cd frontend && npm run build`
     - **Build output directory**: `frontend/dist`
     - **Root directory**: `/`（项目根目录）
   - 点击 **Save and Deploy**

3. **通过 Wrangler CLI 部署（推荐开发者）**

   在项目根目录创建 `frontend/wrangler.toml`：
   ```toml
   name = "muse-scoring-frontend"
   compatibility_date = "2025-01-01"
   
   [site]
   bucket = "./dist"
   ```

   然后执行：
   ```powershell
   cd frontend
   npm run build
   wrangler pages deploy dist --project-name=muse-scoring-frontend
   ```

4. **配置 Pages 自定义域名**

   - 在 Pages 项目设置中，点击 **Custom domains**
   - 添加你的域名（如 `app.yourdomain.com`）
   - Cloudflare 会自动配置 DNS 和 SSL

#### 第二步：配置后端数据库

**选项 1：使用 Neon（推荐，免费且易用）**

1. 访问 [Neon 官网](https://neon.tech/)
2. 使用 GitHub 账号登录
3. 创建新项目，选择 PostgreSQL 17
4. 创建数据库 `scoring`
5. 复制连接字符串，格式如下：
   ```
   postgresql://user:password@ep-xxx.region.aws.neon.tech/scoring
   ```

   > 💡 **注意**：Neon 的连接字符串需要转换为本项目使用的格式：
   > ```
   > postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/scoring
   > ```

**选项 2：使用 Supabase（备选）**

1. 访问 [Supabase 官网](https://supabase.com/)
2. 创建新项目
3. 在 Project Settings → Database 中获取连接字符串
4. 使用 Direct connection 模式的连接字符串

**选项 3：自建 PostgreSQL（完全控制）**

如果你有云服务器（VPS），可以自行安装 PostgreSQL：
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-17

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE scoring;
CREATE USER muse WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE scoring TO muse;
\q
```

#### 第三步：配置 Redis 缓存

**选项 1：使用 Upstash（推荐，免费且支持全球访问）**

1. 访问 [Upstash 官网](https://upstash.com/)
2. 创建 Redis 数据库
3. 选择离你用户最近的区域
4. 复制连接字符串（REST API 或 Native 协议）

   > 💡 **注意**：本项目使用 Native Redis 协议，请使用 Standard connection string：
   > ```
   > redis://default:your-password@your-redis.upstash.io:6379
   > ```

**选项 2：自建 Redis（VPS 部署）**

```bash
# Ubuntu/Debian
sudo apt install redis-server

# 配置密码（编辑 /etc/redis/redis.conf）
requirepass your-strong-redis-password

# 重启 Redis
sudo systemctl restart redis-server
```

#### 第四步：部署后端服务

由于 Cloudflare Workers 不支持长时间运行的 Python 进程，后端需要部署在传统服务器上。以下是几种方案：

**方案 A1：使用 Railway（最简单，有免费额度）**

1. 访问 [Railway](https://railway.app/)
2. 使用 GitHub 账号登录
3. 点击 **New Project** → **Deploy from GitHub repo**
4. 选择 `muse-scoring-platform` 仓库
5. Railway 会自动识别 `backend/` 目录的 Dockerfile
6. 在 Variables 标签页中添加环境变量（见下方配置清单）
7. 点击 **Deploy**

**方案 A2：使用 Render（备选）**

1. 访问 [Render](https://render.com/)
2. 点击 **New** → **Web Service**
3. 连接 GitHub 仓库
4. 配置：
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `granian --interface asgi --host 0.0.0.0 --port $PORT main:app`
5. 添加环境变量
6. 点击 **Create Web Service**

**方案 A3：使用 VPS 自建（最灵活）**

1. 购买一台云服务器（推荐 Hetzner、DigitalOcean、Vultr）
2. 安装 Docker
3. 只部署后端服务：
   ```bash
   # 克隆项目
   git clone https://github.com/MikumikuDAIFans/muse-scoring-platform.git
   cd muse-scoring-platform
   
   # 只启动后端服务（不含 Nginx）
   docker compose up -d postgres redis pgbouncer fastapi
   
   # 查看后端地址
   curl http://localhost:8000/health
   ```

#### 第五步：配置环境变量

无论选择哪种后端部署方式，都需要设置以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `postgresql+asyncpg://user:pass@db-host:5432/scoring` |
| `REDIS_URL` | Redis 连接字符串 | `redis://default:pass@redis-host:6379` |
| `JWT_SECRET` | **必须使用强随机密钥** | 用 PowerShell 生成（见下方） |
| `ADMIN_USERNAME` | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | **必须修改默认密码** | `your-very-strong-password` |
| `TURNSTILE_SITE_KEY` | Cloudflare Turnstile 站点密钥 | 见下方获取方法 |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile 密钥 | 见下方获取方法 |
| `R2_ACCOUNT_ID` | **Cloudflare Account ID** | 见下方 R2 配置说明 |
| `R2_ACCESS_KEY_ID` | **R2 Access Key ID** | 从 R2 API Tokens 获取 |
| `R2_SECRET_ACCESS_KEY` | **R2 Secret Access Key** | 从 R2 API Tokens 获取 |
| `R2_BUCKET` | R2 Bucket 名称 | `muse-images`（默认） |
| `R2_PUBLIC_URL` | R2 自定义域名（可选） | `https://images.yourdomain.com` |

**生成 JWT 密钥：**
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

#### 第六步：配置 Cloudflare Turnstile 人机验证

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单选择 **Turnstile**
3. 点击 **Add Site**
4. 填写信息：
   - **Site name**: `Muse Scoring Platform`
   - **Domain**: 你的域名（如 `app.yourdomain.com`）
   - **Widget Mode**: Managed（推荐）
5. 记录生成的 **Site Key** 和 **Secret Key**
6. 填入后端环境变量

#### 第六步半：配置 Cloudflare R2 图片存储（生产环境必需）

生产环境中，图片**必须**存储在 Cloudflare R2 中，而不是本地文件系统。

**步骤 1：创建 R2 Bucket**

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单选择 **R2**
3. 点击 **Create Bucket**
4. 填写信息：
   - **Bucket name**: `muse-images`
   - 其他保持默认
5. 点击 **Create Bucket**

**步骤 2：创建 R2 API Token**

1. 在 R2 页面，点击左侧 **Manage R2 API Tokens**
2. 点击 **Create API Token**
3. 填写信息：
   - **Token name**: `muse-scoring-upload`
   - **Permissions**: 选择 `Object Read & Write`
   - **Bucket**: 选择 `muse-images`
4. 点击 **Create API Token**
5. **立即复制** Access Key ID 和 Secret Access Key（只显示一次！）

**步骤 3：配置自定义域名（可选但推荐）**

1. 在 R2 Bucket 页面，点击你的 Bucket
2. 点击 **Settings** 标签
3. 找到 **Custom Domains**，点击 **Connect Domain**
4. 输入子域名（如 `images.yourdomain.com`）
5. Cloudflare 会自动创建 DNS 记录

**步骤 4：填入环境变量**

将以下变量添加到后端环境变量中：

```env
# Cloudflare R2 配置
R2_ACCOUNT_ID=你的Cloudflare Account ID（在右侧边栏可见）
R2_ACCESS_KEY_ID=刚才创建的 API Token 的 Access Key
R2_SECRET_ACCESS_KEY=刚才创建的 API Token 的 Secret Key
R2_BUCKET=muse-images
R2_PUBLIC_URL=https://images.yourdomain.com  # 如果配置了自定义域名
# 如果没有自定义域名，使用：https://pub-xxxx.r2.dev
```

**步骤 5：导入图片**

配置完成后，运行导入脚本：

```bash
# 本地开发环境
cd backend
pip install -r requirements.txt
python import_images.py

# 生产环境（Railway/Render等）
# 图片会在首次运行时自动上传到 R2
```

#### 第七步：配置前端 API 地址

前端需要知道后端 API 的地址。修改前端 API 配置文件：

编辑 `frontend/src/api/index.js`，将 `baseURL` 改为你的后端地址：

```javascript
const API_BASE_URL = 'https://your-backend-url.railway.app' // 替换为你的后端地址

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

然后重新构建并部署前端：
```powershell
cd frontend
npm run build
wrangler pages deploy dist --project-name=muse-scoring-frontend
```

#### 第八步：导入图片数据

**生产环境（推荐）：使用 Cloudflare R2 存储图片**

已完成 R2 配置后，只需运行导入脚本：

```bash
# 确保环境变量已设置（R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY）
cd backend
python import_images.py
```

脚本会自动：
1. 读取本地 `images/` 目录的图片
2. 上传每张图片到 R2 Bucket
3. 将 R2 公开 URL 存入 PostgreSQL 数据库

**输出示例：**
```
🚀 生产模式: 图片将上传到 Cloudflare R2
Imported 10 images...
Imported 20 images...
...
Done! Total: 1000 images
✅ 所有图片已上传到 R2 Bucket: muse-images
```

**本地开发环境（可选）：使用本地存储**

如果不配置 R2 环境变量，脚本会自动降级到本地模式：
```
⚠️  开发模式: 使用本地 URL (请配置 R2_* 环境变量以启用生产模式)
```

此时图片 URL 会指向 `http://localhost:8080/images/xxx.png`，仅用于本地测试。

#### 第九步：验证部署

1. **访问前端页面**
   ```
   https://你的-pages-url.pages.dev
   ```

2. **测试后端 API**
   ```powershell
   curl https://你的后端地址/health
   curl https://你的后端地址/health/ready
   ```

3. **测试用户注册登录**
   - 在前端页面注册一个新账号
   - 登录并尝试评分

4. **测试管理员功能**
   - 使用管理员账号登录
   - 查看统计信息
   - 尝试导出数据

---

### 方案 B：混合部署（VPS + Cloudflare）

> 如果你有一台 VPS，这是最简单且可控的方案

#### 架构

```
用户浏览器
    ↓
[Cloudflare CDN] DNS + HTTPS + DDoS 防护
    ↓
[Cloudflare Tunnel] 安全隧道（无需开放 VPS 端口）
    ↓
[VPS 上的 Nginx] 反向代理
    ↓
[Docker Compose] 运行所有服务
```

#### 第一步：准备 VPS

1. **购买 VPS**（推荐配置）
   - CPU: 2 核
   - 内存: 4GB
   - 磁盘: 40GB SSD
   - 系统: Ubuntu 22.04 LTS
   - 推荐提供商: Hetzner、DigitalOcean、Vultr

2. **安装 Docker**
   ```bash
   # SSH 登录 VPS
   ssh root@your-vps-ip
   
   # 安装 Docker
   curl -fsSL https://get.docker.com | sh
   
   # 添加当前用户到 docker 组
   usermod -aG docker $USER
   
   # 验证安装
   docker --version
   docker compose version
   ```

#### 第二步：配置 Cloudflare Tunnel

1. **安装 cloudflared**
   ```bash
   # 下载并安装
   sudo curl -L --output /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   sudo chmod +x /usr/local/bin/cloudflared
   ```

2. **创建 Tunnel**
   ```bash
   # 登录 Cloudflare
   cloudflared tunnel login
   
   # 创建 Tunnel
   cloudflared tunnel create muse-scoring
   
   # 这会生成一个凭证文件在 ~/.cloudflared/
   ```

3. **配置 Tunnel 路由**
   
   编辑 `~/.cloudflared/config.yml`：
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: /root/.cloudflared/<tunnel-id>.json
   
   ingress:
     - hostname: app.yourdomain.com
       service: http://localhost:8080
     - service: http_status:404
   ```

4. **配置 DNS**
   ```bash
   # 添加 DNS 记录指向 Tunnel
   cloudflared tunnel route dns muse-scoring app.yourdomain.com
   ```

5. **运行 Tunnel**
   ```bash
   # 前台运行（测试）
   cloudflared tunnel run muse-scoring
   
   # 或作为 systemd 服务（生产）
   cloudflared service install
   sudo systemctl enable cloudflared
   sudo systemctl start cloudflared
   ```

#### 第三步：部署应用到 VPS

1. **克隆项目**
   ```bash
   git clone https://github.com/MikumikuDAIFans/muse-scoring-platform.git
   cd muse-scoring-platform
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   修改以下配置：
   ```env
   # 使用 PgBouncer 作为数据库入口（推荐）
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@pgbouncer:6432/scoring
   REDIS_URL=redis://redis:6379
   JWT_SECRET=<用PowerShell生成的强密钥>
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=<修改为强密码>
   TURNSTILE_SITE_KEY=<你的Turnstile Site Key>
   TURNSTILE_SECRET_KEY=<你的Turnstile Secret Key>
   ```

3. **构建前端**
   ```bash
   # 需要 Node.js
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install -y nodejs
   
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **启动所有服务**
   ```bash
   docker compose up -d --build
   ```

5. **验证部署**
   ```bash
   # 检查所有服务状态
   docker compose ps
   
   # 测试本地访问
   curl http://localhost:8080
   curl http://localhost:8000/health
   ```

6. **导入图片**
   ```bash
   # 上传图片到 VPS 的 images/ 目录
   scp *.jpg root@your-vps-ip:/root/muse-scoring-platform/images/
   
   # 执行导入
   docker compose exec fastapi python import_images.py
   ```

#### 第四步：通过域名访问

完成 Cloudflare Tunnel 配置后，访问：
```
https://app.yourdomain.com
```

Cloudflare 会自动提供 HTTPS 证书，无需额外配置。

---

### 部署检查清单

部署完成后，请逐项检查：

- [ ] 前端页面可以正常访问（HTTPS）
- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] Turnstile 人机验证正常显示
- [ ] 图片加载正常
- [ ] 评分提交成功
- [ ] 管理员可以登录后台
- [ ] 统计数据正确显示
- [ ] 数据导出功能正常
- [ ] JWT_SECRET 已更换为强随机密钥
- [ ] 管理员密码已修改
- [ ] 数据库已配置自动备份

---

### 部署后的运维

#### 更新应用

```powershell
# 拉取最新代码
git pull origin master

# 重新构建前端
cd frontend
npm install
npm run build

# 重新部署前端到 Cloudflare Pages
wrangler pages deploy dist --project-name=muse-scoring-frontend

# 如果使用 VPS，重启后端
docker compose up -d --build fastapi
```

#### 监控和告警

1. **Cloudflare Analytics**
   - 在 Dashboard 中查看访问量、带宽、威胁
   - 设置异常流量告警

2. **数据库监控**
   ```bash
   # 查看数据库连接数
   docker compose exec postgres psql -U postgres -d scoring -c "SELECT count(*) FROM pg_stat_activity;"
   
   # 查看数据库大小
   docker compose exec postgres psql -U postgres -d scoring -c "SELECT pg_database_size('scoring');"
   ```

3. **Redis 监控**
   ```bash
   docker compose exec redis redis-cli INFO memory
   docker compose exec redis redis-cli DBSIZE
   ```

---

## 详细操作指南

### 导入图片数据

系统部署完成后，需要先导入图片才能开始评分。

#### 步骤 1：准备图片

1. 在项目根目录找到 `images` 文件夹
2. 将需要评分的图片放入此文件夹
3. 建议图片命名规范：`001.jpg`, `002.jpg`, `003.png` 等

#### 步骤 2：执行导入

```powershell
docker compose exec fastapi python import_images.py
```

#### 导入过程说明

```
正在扫描 images 目录...
发现 100 张图片
正在导入图片元数据...
导入完成！共导入 100 条记录
```

#### 注意事项

- 图片格式支持：jpg, jpeg, png, gif, webp
- 导入会跳过已存在的图片（不会重复导入）
- 导入完成后可以在管理后台查看统计信息

### 用户操作流程

#### 普通用户

1. **注册账号**
   - 访问 http://localhost:8080
   - 点击"注册"标签
   - 填写用户名和密码（至少8位）
   - 点击注册

2. **登录系统**
   - 输入用户名和密码
   - 点击登录

3. **开始评分**
   - 登录后进入欢迎页
   - 点击"开始评分"
   - 每批显示 10 张图片
   - 对每张图片的两个维度分别打分（1-10分）
   - 完成后自动进入下一批

4. **查看个人统计**
   - 在个人页可以看到自己的评分总数

#### 管理员操作

1. **登录管理后台**
   - 使用管理员账号登录
   - 自动跳转到管理后台

2. **查看统计信息**
   - 总图片数、已评分图片数
   - 总评分数、今日评分数
   - 活跃用户数
   - Redis 队列长度（待入库数据量）

3. **查看用户排行**
   - 按评分数量排序的用户列表
   - 支持分页查看

4. **导出数据**
   - 选择导出格式（CSV 或 JSONL）
   - 可选时间范围筛选
   - 可选特定用户筛选
   - 点击下载

---

## 日常运维

### 服务管理命令

#### 启动服务

```powershell
# 启动所有服务
docker compose up -d

# 启动单个服务（如只启动 nginx）
docker compose up -d nginx
```

#### 停止服务

```powershell
# 停止所有服务
docker compose down

# 停止单个服务
docker compose stop fastapi
```

#### 重启服务

```powershell
# 重启所有服务
docker compose restart

# 重启单个服务（常用）
docker compose restart fastapi
docker compose restart nginx
```

#### 查看服务状态

```powershell
docker compose ps
```

### 日志管理

#### 查看实时日志

```powershell
# 查看所有服务实时日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f fastapi
docker compose logs -f nginx
docker compose logs -f postgres
```

#### 日志清理

```powershell
# 查看日志文件大小
docker system df -v

# 清理无用镜像和容器
docker system prune -f
```

### 资源监控

#### 查看容器资源使用

```powershell
# 实时查看 CPU 和内存使用
docker stats
```

输出示例：
```
CONTAINER           CPU %     MEM USAGE / LIMIT     MEM %
postgres-1          0.50%     150MiB / 2GiB         7.32%
redis-1             0.10%     15MiB / 2GiB          0.73%
fastapi-1           2.00%     200MiB / 2GiB         9.76%
nginx-1             0.05%     5MiB / 2GiB           0.24%
```

### 数据维护

#### 数据库连接测试

```powershell
# 进入 PostgreSQL 容器
docker compose exec postgres psql -U postgres -d scoring

# 执行简单查询
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM images;
SELECT COUNT(*) FROM scores;

# 退出
\q
```

#### Redis 状态检查

```powershell
# 进入 Redis 容器
docker compose exec redis redis-cli

# 查看队列长度
LLEN score_queue

# 查看内存使用
INFO memory

# 退出
exit
```

#### 健康检查

```powershell
# 检查后端健康状态
curl http://localhost:8000/health

# 检查就绪状态（包含数据库和Redis连接）
curl http://localhost:8000/health/ready
```

正常响应示例：
```json
{
  "status": "ok",
  "uptime": 3600.5,
  "database": "connected",
  "redis": "connected"
}
```

---

## 故障排查

### 常见问题及解决方案

#### 1. 端口被占用

**症状**：启动时报错 `port is already allocated`

**解决方法**：
```powershell
# 查看哪个程序占用了端口
netstat -ano | findstr :8080
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# 结束占用端口的进程（替换 PID）
taskkill /PID <进程ID> /F

# 或者修改 docker-compose.yml 中的端口映射
# 例如将 8080:80 改为 8081:80
```

#### 2. 服务启动失败

**症状**：某个服务状态显示为 `Exited` 或 `Error`

**排查步骤**：
```powershell
# 1. 查看该服务的日志
docker compose logs fastapi

# 2. 检查配置文件是否正确
cat .env

# 3. 重新构建并启动
docker compose up -d --build fastapi
```

#### 3. 数据库连接失败

**症状**：后端报错 `could not connect to server`

**解决方法**：
```powershell
# 1. 确认 PostgreSQL 是否正常运行
docker compose ps postgres

# 2. 检查 PgBouncer 是否正常
docker compose logs pgbouncer

# 3. 测试数据库连接
docker compose exec postgres pg_isready

# 4. 重启相关服务
docker compose restart postgres pgbouncer fastapi
```

#### 4. 前端页面空白

**症状**：访问 http://localhost:8080 显示空白或 404

**解决方法**：
```powershell
# 1. 检查前端构建产物是否存在
ls frontend/dist/

# 2. 如果没有 dist 目录，需要构建前端
cd frontend
npm install
npm run build
cd ..

# 3. 重启 Nginx
docker compose restart nginx
```

#### 5. 评分提交失败

**症状**：用户打分后提示错误

**排查步骤**：
```powershell
# 1. 检查 Redis 是否正常
docker compose exec redis redis-cli ping
# 应该返回 PONG

# 2. 检查 Redis 队列
docker compose exec redis redis-cli LLEN score_queue

# 3. 查看后端日志
docker compose logs -f fastapi

# 4. 重启后端服务
docker compose restart fastapi
```

### 紧急恢复

#### 完全重建

如果系统出现严重问题，可以完全重建：

```powershell
# ⚠️ 警告：这将删除所有数据！
# 请先备份数据（见数据备份章节）

# 1. 停止并删除所有容器
docker compose down -v

# 2. 重新构建并启动
docker compose up -d --build

# 3. 重新导入图片
docker compose exec fastapi python import_images.py
```

---

## 数据备份

### 为什么要备份？

- 防止硬件故障导致数据丢失
- 方便迁移到新服务器
- 满足合规要求

### 备份数据库

#### 完整备份

```powershell
# 生成带时间戳的备份文件名
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "backup_$timestamp.sql"

# 执行备份
docker compose exec postgres pg_dump -U postgres scoring > $backupFile

# 验证备份文件
Get-Item $backupFile
```

#### 定时备份（Windows 任务计划）

1. 创建备份脚本 `backup.ps1`：
```powershell
$timestamp = Get-Date -Format "yyyyMMdd"
$backupDir = "E:\backups"
New-Item -ItemType Directory -Force -Path $backupDir
docker compose exec postgres pg_dump -U postgres scoring > "$backupDir\backup_$timestamp.sql"

# 删除 30 天前的备份
Get-ChildItem "$backupDir\*.sql" | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | Remove-Item
```

2. 创建 Windows 任务计划：
   - 打开"任务计划程序"
   - 创建基本任务
   - 设置每天凌晨 2 点执行
   - 操作：启动程序 `powershell.exe`
   - 参数：`-File "E:\MuseProject\backup.ps1"`

### 备份 Redis

```powershell
# 触发 Redis 持久化
docker compose exec redis redis-cli BGSAVE

# 备份数据卷
docker compose cp redis:/data redis_backup_$(Get-Date -Format "yyyyMMdd")
```

### 备份图片

```powershell
# 压缩备份图片目录
Compress-Archive -Path images -DestinationPath "images_backup_$(Get-Date -Format 'yyyyMMdd').zip"
```

### 恢复数据

#### 恢复数据库

```powershell
# 从备份文件恢复
Get-Content backup_20260406_020000.sql | docker compose exec -T postgres psql -U postgres -d scoring
```

#### 恢复 Redis

```powershell
# 停止 Redis
docker compose stop redis

# 恢复数据
docker compose cp redis_backup_20260406 redis:/data

# 启动 Redis
docker compose start redis
```

---

## 安全加固

### 生产环境必做事项

#### 1. 修改默认密码

```powershell
# 登录 PostgreSQL
docker compose exec postgres psql -U postgres -d scoring

-- 修改管理员密码（在 SQL 提示符下执行）
UPDATE users SET password_hash = '新生成的bcrypt哈希' WHERE username = 'admin';

-- 退出
\q
```

#### 2. 修改 JWT 密钥

编辑 `.env` 文件，修改 `JWT_SECRET` 为强随机密钥（生成方法见环境准备章节）。

#### 3. 配置防火墙

```powershell
# 只开放必要端口
New-NetFirewallRule -DisplayName "Muse Platform HTTP" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

# 关闭不必要的端口暴露（修改 docker-compose.yml）
# 移除 postgres 和 redis 的 ports 映射，只保留内部通信
```

#### 4. 配置 HTTPS（推荐）

1. 申请 SSL 证书（Let's Encrypt 免费）
2. 修改 `nginx.conf`：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置保持不变
}
```

3. 挂载证书目录（修改 `docker-compose.yml`）：
```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

#### 5. 开启 Cloudflare Turnstile

1. 访问 [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)
2. 注册并添加站点
3. 获取 Site Key 和 Secret Key
4. 填入 `.env` 文件：
```env
TURNSTILE_SITE_KEY=你的SiteKey
TURNSTILE_SECRET_KEY=你的SecretKey
```

#### 6. 定期更新

```powershell
# 更新 Docker 镜像
docker compose pull

# 重新构建并启动
docker compose up -d --build

# 清理旧镜像
docker image prune -f
```

---

## 常见问题 FAQ

### Q: 我的电脑配置能运行这个项目吗？

**A**: 最低配置要求：
- CPU: 2 核以上
- 内存: 4GB 以上（推荐 8GB）
- 硬盘: 10GB 可用空间
- 操作系统: Windows 10/11, macOS, Linux

### Q: Docker 是什么？必须用 Docker 吗？

**A**: Docker 是一个容器化平台，把应用和其依赖打包在一起。使用 Docker 可以：
- 避免环境配置问题
- 保证开发和生产环境一致
- 一键启动所有服务

对于本项目，强烈建议使用 Docker，因为配置多个服务（数据库、缓存、后端、前端）手动配置很复杂。

### Q: 如何修改前端页面内容？

**A**: 前端代码在 `frontend/src/` 目录下，修改后需要重新构建：
```powershell
cd frontend
npm run build
cd ..
docker compose restart nginx
```

### Q: 如何添加新用户？

**A**: 用户可以通过前端页面注册，也可以通过数据库直接添加：
```sql
INSERT INTO users (username, password_hash, role) 
VALUES ('newuser', 'bcrypt哈希值', 'user');
```

### Q: 评分数据存在哪里？

**A**: 评分数据存储在 PostgreSQL 数据库中。Redis 只是临时缓存，数据会定时写入数据库。

### Q: 如何查看有多少用户注册了？

**A**: 可以通过管理后台查看，或者执行：
```powershell
docker compose exec postgres psql -U postgres -d scoring -c "SELECT COUNT(*) FROM users;"
```

### Q: 系统支持多少并发用户？

**A**: 得益于 Redis 缓冲和 PgBouncer 连接池，系统可以支持数百个并发用户同时评分。

### Q: 如何迁移到另一台服务器？

**A**: 步骤如下：
1. 备份数据库和图片（见数据备份章节）
2. 在新服务器安装 Docker
3. 克隆项目代码
4. 恢复备份数据
5. 启动服务

### Q: 遇到其他问题怎么办？

**A**: 
1. 首先查看日志：`docker compose logs -f`
2. 检查服务状态：`docker compose ps`
3. 查看本文档的故障排查章节
4. 在 GitHub Issues 中提问

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。
