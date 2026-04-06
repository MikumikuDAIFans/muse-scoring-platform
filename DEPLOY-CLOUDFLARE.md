# 🚀 Cloudflare 从零上线指南

> 本文档指导你从 **零开始** 将 Muse Scoring Platform 部署到 Cloudflare 生态并正式上线。
> 预计耗时：**30-45 分钟**（首次操作）

---

## 📋 前置条件

- [ ] 已注册 [Cloudflare](https://dash.cloudflare.com/sign-up) 账号
- [ ] 拥有一个域名并已接入 Cloudflare DNS（或使用 Pages 提供的 `.pages.dev` 子域名）
- [ ] 本地安装了 Git 和 Node.js（≥18）
- [ ] 项目代码已推送到 GitHub 仓库

---

## 总体架构

```
┌─────────────────────────────────────────────────┐
│              Cloudflare 生态                      │
│                                                   │
│  [Pages] 前端 (Vue 3)                             │
│    → muse-scoring.pages.dev                       │
│    → 或你的自定义域名                              │
│                                                   │
│  [Turnstile] 人机验证                             │
│    → 防止脚本批量注册/刷分                         │
│                                                   │
│  [R2] 图片存储                                    │
│    → 存储所有标注图片，零出口费用                   │
│                                                   │
├─────────────────────────────────────────────────┤
│              第三方服务（非 Cloudflare）            │
│                                                   │
│  [Neon / Supabase] PostgreSQL 数据库              │
│  [Upstash / 自建] Redis 缓存                      │
│  [Railway / Render / VPS] FastAPI 后端            │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 第 1 步：创建 R2 图片存储 (5 分钟)

### 1.1 创建 Bucket

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单 → **R2**
3. 点击 **Create Bucket**
4. Bucket name 填 `muse-images`
5. 点击 **Create Bucket**

### 1.2 创建 API Token

1. R2 页面 → 左侧 **Manage R2 API Tokens**
2. 点击 **Create API Token**
3. 填写：
   - Token name: `muse-scoring-upload`
   - Permissions: **Object Read & Write**
   - Bucket: `muse-images`
4. 点击 **Create API Token**
5. ⚠️ **立即复制** Access Key ID 和 Secret Access Key（只显示一次！）

### 1.3 记录 Account ID

在 Cloudflare Dashboard 右侧边栏找到你的 **Account ID**，复制保存。

---

## 第 2 步：创建 Turnstile 人机验证 (2 分钟)

1. Cloudflare Dashboard → 左侧 **Turnstile**
2. 点击 **Add Site**
3. 填写：
   - Site name: `Muse Scoring Platform`
   - Domain: 你的域名（如 `muse.yourdomain.com`）或 `localhost`（开发用）
   - Widget Mode: **Managed**
4. 记录生成的 **Site Key** 和 **Secret Key**

---

## 第 3 步：创建数据库 (5 分钟)

### 选项 A：Neon（推荐，免费 500MB）

1. 访问 [Neon](https://neon.tech/)，用 GitHub 登录
2. 创建项目，选择 **PostgreSQL 17**
3. 记下连接字符串，格式类似：
   ```
   postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb
   ```
4. 转换为项目所需格式：
   ```
   postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/scoring
   ```

### 选项 B：Supabase（备选，免费 500MB）

1. 访问 [Supabase](https://supabase.com/)，创建项目
2. Project Settings → Database → Connection string → **Direct connection**
3. 复制并转换格式同上

---

## 第 4 步：创建 Redis 缓存 (3 分钟)

### 选项 A：Upstash（推荐，免费 10K 命令/天）

1. 访问 [Upstash](https://upstash.com/)，创建 Redis
2. 选择离用户最近的区域
3. 复制 **Standard** 连接字符串：
   ```
   redis://default:your-password@your-redis.upstash.io:6379
   ```

### 选项 B：自建 Redis

如果你有 VPS，自行安装并设置密码即可。

---

## 第 5 步：部署后端服务 (10 分钟)

以下以 **Railway** 为例（最简单的方式）：

### 5.1 创建 Railway 项目

1. 访问 [Railway](https://railway.app/)，用 GitHub 登录
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 选择你的仓库 `muse-scoring-platform`
4. Railway 会自动识别 `backend/Dockerfile`

### 5.2 配置环境变量

在 Railway 项目的 **Variables** 标签页，逐个添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | 第 3 步获取的连接串 |
| `REDIS_URL` | `redis://default:...` | 第 4 步获取的连接串 |
| `JWT_SECRET` | *(用下方命令生成)* | 64 位随机密钥 |
| `ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `ADMIN_PASSWORD` | *(强密码)* | 管理员密码 |
| `TURNSTILE_SITE_KEY` | `0x4...` | 第 2 步获取 |
| `TURNSTILE_SECRET_KEY` | `0x...` | 第 2 步获取 |
| `R2_ACCOUNT_ID` | *(Account ID)* | 第 1 步获取 |
| `R2_ACCESS_KEY_ID` | *(Access Key)* | 第 1 步获取 |
| `R2_SECRET_ACCESS_KEY` | *(Secret Key)* | 第 1 步获取 |
| `R2_BUCKET` | `muse-images` | R2 Bucket 名称 |
| `R2_PUBLIC_URL` | `https://images.yourdomain.com` | R2 自定义域名或 pub URL |
| `ALLOWED_ORIGINS` | `https://你的pages域名` | 前端域名 |

**生成 JWT_SECRET：**
```powershell
# Windows PowerShell
-join ((65..90)+(97..122)+(48..57)|Get-Random -Count 64|%{[char]$_})

# Linux / macOS
openssl rand -hex 32
```

### 5.3 部署

1. 点击 **Deploy**
2. 等待构建完成（约 2-3 分钟）
3. 记下 Railway 分配的域名，如 `https://muse-backend-production.up.railway.app`

### 5.4 初始化数据库表

Railway 首次部署后，需要创建数据库表。有两种方式：

**方式 A：通过 SQL 编辑器**

1. 在你的数据库平台（Neon/Supabase）打开 SQL 编辑器
2. 执行 `sql/schema.sql` 中的全部 SQL 语句

**方式 B：通过后端自动建表**

项目启动时会自动执行 `Base.metadata.create_all()`，表会自动创建。

### 5.5 导入图片数据

```bash
# 方式 A：在 Railway 控制台打开 Shell
cd /app
python import_images.py

# 方式 B：本地执行（需要先设置环境变量指向云数据库）
cd backend
pip install -r requirements.txt
# 设置所有环境变量后执行：
python import_images.py
```

脚本会将 `images/` 目录的图片上传到 R2，并将 URL 写入数据库。

---

## 第 6 步：部署前端到 Cloudflare Pages (5 分钟)

### 6.1 通过 Dashboard 连接 GitHub

1. Cloudflare Dashboard → **Workers & Pages** → **Pages**
2. 点击 **Connect to Git**
3. 选择 `muse-scoring-platform` 仓库
4. 配置：
   - **Framework preset**: Vue
   - **Build command**: `cd frontend && npm run build`
   - **Build output directory**: `frontend/dist`
   - **Root directory (Advanced)**: `/`（留空即可）
5. 点击 **Save and Deploy**

### 6.2 配置前端环境变量

Pages 项目 → **Settings** → **Environment variables** → **Production** → **Add variable**：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `VITE_TURNSTILE_SITE_KEY` | `0x4...` | 第 2 步获取的 Site Key |
| `VITE_API_BASE_URL` | `https://你的后端域名` | 第 5 步 Railway 分配的域名 |

> ⚠️ **重要**：修改环境变量后需要重新触发部署才会生效。

### 6.3 配置 CORS

回到后端（Railway），将 `ALLOWED_ORIGINS` 设置为你的 Pages 域名：
```
ALLOWED_ORIGINS=https://muse-scoring.pages.dev
```
如果有自定义域名也一并加上，逗号分隔。

### 6.4 验证部署

```powershell
# 测试后端健康
curl https://你的后端域名/health

# 测试后端就绪
curl https://你的后端域名/health/ready

# 访问前端
# 浏览器打开 https://你的pages域名.pages.dev
```

---

## 第 7 步：配置自定义域名（可选，3 分钟）

### 前端 Pages 自定义域名

1. Pages 项目 → **Custom domains** → **Set up a custom domain**
2. 输入 `muse.yourdomain.com`
3. Cloudflare 自动添加 DNS 记录
4. 等待 SSL 证书生效（通常 1-5 分钟）

### R2 自定义域名

1. R2 → 你的 Bucket → **Settings** → **Custom Domains** → **Connect Domain**
2. 输入 `images.yourdomain.com`
3. 自动配置 DNS
4. 更新后端 `R2_PUBLIC_URL` 环境变量

### 后端自定义域名

1. Railway → Settings → Domains → **Generate Domain** 或使用自有域名
2. 如果用自有域名，添加 CNAME 记录指向 Railway 域名

---

## 📝 环境变量速查表

### 后端环境变量（Railway / Render / VPS）

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/scoring
REDIS_URL=redis://default:pass@host:6379

# 认证
JWT_SECRET=<64位随机密钥>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<强密码>

# 安全
ALLOWED_ORIGINS=https://你的pages域名

# Turnstile
TURNSTILE_SITE_KEY=0x4...
TURNSTILE_SECRET_KEY=0x...

# R2 存储
R2_ACCOUNT_ID=<Account ID>
R2_ACCESS_KEY_ID=<Access Key>
R2_SECRET_ACCESS_KEY=<Secret Key>
R2_BUCKET=muse-images
R2_PUBLIC_URL=https://images.yourdomain.com
```

### 前端环境变量（Pages Settings）

| 变量名 | 说明 |
|--------|------|
| `VITE_TURNSTILE_SITE_KEY` | Turnstile Site Key（公开） |
| `VITE_API_BASE_URL` | 后端 API 完整 URL |

---

## ✅ 上线检查清单

- [ ] 数据库表已创建（执行 schema.sql 或后端自动建表）
- [ ] 图片已导入（`python import_images.py` 成功执行）
- [ ] 后端 `/health` 返回 `{"status":"ok"}`
- [ ] 后端 `/health/ready` 返回 `{"status":"ok","database":"ok","redis":"ok"}`
- [ ] 前端可以正常访问
- [ ] 注册功能正常（含 Turnstile 验证）
- [ ] 登录功能正常
- [ ] 评分功能正常（图片能正常显示）
- [ ] 管理员面板数据正确显示
- [ ] CORS 配置正确（无跨域错误）
- [ ] JWT_SECRET 已更换为强随机密钥
- [ ] ADMIN_PASSWORD 已更换为强密码

---

## 🔧 故障排查

### 后端启动失败

```bash
# Railway 查看日志
# 或本地调试：
cd backend
pip install -r requirements.txt
python -c "import main; print('OK')"
```

### 前端构建失败

```bash
cd frontend
npm install
npm run build
# 查看错误信息
```

### 图片无法显示

1. 确认 R2 环境变量全部正确
2. 确认 `import_images.py` 已成功执行
3. 检查数据库中 `images.url` 字段是否为有效的 R2 URL

### CORS 跨域错误

1. 确认后端 `ALLOWED_ORIGINS` 包含前端域名
2. 确认前端 `VITE_API_BASE_URL` 正确指向后端
3. 重新部署后端使环境变量生效
