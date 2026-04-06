# Muse Scoring Platform - 图片评分管理平台

> 一个面向大众的图片双维度评分平台，用户可以通过"美学表现"和"细节完成度"两个维度对图片进行打分。

---

## 📖 目录导航

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [技术栈详解](#技术栈详解)
- [环境准备](#环境准备)
- [快速部署](#快速部署)
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

## 环境准备

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

## 快速部署

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
