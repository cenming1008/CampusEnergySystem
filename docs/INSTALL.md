# MineEnergySystem - 安装与启动指南

> 本文档提供完整的安装和启动说明，包括 Docker 方式和本地开发方式

---

## 📋 目录

- [方式1：Docker 快速启动（推荐）](#方式1docker-快速启动推荐)
- [方式2：本地开发环境](#方式2本地开发环境)
- [依赖安装详解](#依赖安装详解)
- [常见问题](#常见问题)

---

## 方式1：Docker 快速启动（推荐）

### 前置要求

- Docker Desktop 24.0+
- 可用端口：8088、5433、6379、1883

### 一键启动

```bash
# 克隆项目
git clone <your-repo-url>
cd MineEnergySystem

# 一键启动
./quick_start.sh

# 访问系统
# http://localhost:8088/docs
# 默认账号：admin / 123456
```

**就这么简单！** 详细说明请查看 [docs/快速启动指南.md](./docs/快速启动指南.md)

---

## 方式2：本地开发环境

如果需要在本地开发（不使用 Docker 运行后端）：

### 第 1 步：安装系统依赖

#### macOS

```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 PostgreSQL（可选，也可以用 Docker）
brew install postgresql@14

# 安装 Redis（可选）
brew install redis
```

#### Linux (Ubuntu/Debian)

```bash
# 更新包列表
sudo apt update

# 安装 Python
sudo apt install python3 python3-pip python3-venv

# 安装 PostgreSQL（可选）
sudo apt install postgresql-14

# 安装 Redis（可选）
sudo apt install redis-server
```

### 第 2 步：创建 Python 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

# 验证虚拟环境
which python  # 应该指向 venv/bin/python
python --version
```

### 第 3 步：安装 Python 依赖

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 第 4 步：启动基础服务

```bash
# 使用 Docker 启动数据库、Redis、MQTT
docker compose up -d db redis mqtt

# 等待服务就绪（约 10-20 秒）
sleep 15
docker compose ps
```

### 第 5 步：配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件
nano .env

# 修改以下配置（连接 Docker 服务）：
# DATABASE_URL=postgresql://admin:password123@localhost:5433/mine_energy
# REDIS_URL=redis://localhost:6379/0
# MQTT_BROKER=localhost
```

### 第 6 步：启动后端服务

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动后端（支持热重载）
python run.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

### 第 7 步：启动前端（可选）

```bash
# 新开一个终端
cd frontend

# 安装依赖（首次需要）
npm install

# 启动开发服务器
npm run dev

# 访问：http://localhost:5173
```

---

## 依赖安装详解

## 🎯 快速安装

### 方法1：使用安装脚本（推荐）

```bash
cd /Users/todo/MineEnergySystem
./scripts/install_dependencies.sh
```

### 方法2：手动安装

```bash
# 1. 进入项目目录
cd /Users/todo/MineEnergySystem

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 使用 python -m pip 安装（最可靠）
python -m pip install -r requirements.txt

# 或者使用 pip3（如果虚拟环境激活失败）
pip3 install -r requirements.txt
```

### 方法3：不使用虚拟环境（不推荐）

```bash
# 直接使用系统 Python
pip3 install -r requirements.txt

# 或使用模块方式
python3 -m pip install -r requirements.txt
```

## ⚠️ 重要说明

### macOS 上的 Python 命令

在 macOS 上：
- ✅ 使用 `python3` 而不是 `python`
- ✅ 使用 `pip3` 而不是 `pip`
- ✅ 或使用 `python3 -m pip`（最可靠）

### 虚拟环境

项目已有虚拟环境 `venv/`，建议使用：

```bash
# 激活虚拟环境
source venv/bin/activate

# 激活后，可以使用 python 和 pip（不需要3）
python --version
pip --version

# 退出虚拟环境
deactivate
```

## 🔧 如果遇到问题

### 问题：command not found: pip

**解决**：
```bash
# 使用 pip3
pip3 install -r requirements.txt

# 或使用模块方式
python3 -m pip install -r requirements.txt
```

### 问题：虚拟环境激活失败

**解决**：
```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 问题：权限错误

**解决**：
```bash
# 不要使用 sudo！
# 使用虚拟环境或 --user 标志
pip3 install --user -r requirements.txt
```

## 📦 安装 TensorFlow（可选）

TensorFlow 较大，如果安装失败或很慢：

```bash
# 使用国内镜像
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple tensorflow scikit-learn

# 或激活虚拟环境后
source venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple tensorflow scikit-learn
```

## ✅ 验证安装

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查关键包
python -c "import fastapi; print('FastAPI OK')"
python -c "import sqlmodel; print('SQLModel OK')"
python -c "import tensorflow; print('TensorFlow OK')"  # 可选
python -c "import sklearn; print('scikit-learn OK')"    # 可选
```

## 💡 推荐工作流程

```bash
# 每次开发前
cd /Users/todo/MineEnergySystem
source venv/bin/activate

# 现在可以使用 python 和 pip
python run.py
pip install 新包

# 开发完成后（可选）
deactivate
```
