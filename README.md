# TTS-Server-Web

tts-server-android 的 Web 版本，提供基于 Web 的文本转语音服务。

## 技术栈

- **前端**: Next.js 15 + React 18 + shadcn/ui + Tailwind CSS
- **后端**: FastAPI + SQLAlchemy + Alembic
- **数据库**: SQLite

## 快速开始

### 安装依赖

```bash
# 安装前端依赖
pnpm install

# 安装后端依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动后端服务
pnpm api

# 启动前端服务（新终端）
pnpm dev
```

## 访问地址

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 生产构建

生产环境只需启动后端服务，后端会托管前端静态文件。

### 1. 构建前端

```bash
# 构建前端静态文件到 dist 目录
pnpm build
```

### 2. 数据库迁移

```bash
# 应用所有数据库迁移
alembic upgrade head
```

### 3. 启动服务

```bash
# 使用 pnpm 启动
pnpm start
```

服务启动后访问 `http://your-server:8000` 即可。