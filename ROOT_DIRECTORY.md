# 项目根目录结构说明

> 矿区能源管理系统根目录文件和目录说明

## 📁 目录结构

```
MineEnergySystem/
│
├── 📄 核心文档
├── README.md                    # 项目主文档 ⭐
├── CHANGELOG_v2.2.0.md          # 当前版本更新日志
├── DATABASE_STORAGE.md          # 数据库存储说明
├── ROOT_DIRECTORY.md            # 本文件 - 根目录结构说明
├── 项目文件整理总结.md          # 项目整理记录
│
├── 📁 应用代码
├── app/                         # 后端应用代码（FastAPI）
│   ├── api/                    # API 接口
│   ├── core/                   # 核心模块
│   ├── models/                 # 数据模型
│   ├── services/               # 业务服务
│   └── README.md               # 后端代码说明
│
├── frontend/                    # 前端应用代码（Vue 3）
│   ├── src/                    # 源代码
│   ├── public/                 # 静态资源
│   ├── README.md               # 前端项目说明
│   ├── DEVELOPMENT.md          # 前端开发指南
│   └── CHANGELOG.md            # 前端更新日志
│
├── lstm_forecast/               # LSTM 预测模块
│   ├── service.py              # 预测服务
│   ├── version_manager.py      # 版本管理
│   └── README.md               # LSTM 模块说明
│
├── 📁 配置与数据
├── config/                      # 配置文件
│   └── settings.json           # 系统配置
│
├── models/                      # LSTM 模型存储
│   ├── lstm/                   # 模型文件
│   ├── scalers/                # 标准化器
│   ├── versions/               # 版本信息
│   └── README.md               # 模型存储说明
│
├── pg_data/                     # 生产数据库数据（已忽略）
├── pg_data_dev/                 # 开发数据库数据（已忽略）
│
├── 📁 脚本工具
├── scripts/                     # 脚本工具集
│   ├── python/                 # Python 脚本
│   ├── shell/                  # Shell 脚本
│   ├── README.md               # 脚本总览
│   ├── QUICK_REFERENCE.md      # ⚡ 快速参考 ⭐
│   └── CHANGELOG.md            # 脚本整理记录
│
├── bin/                         # 快速启动脚本
│   ├── fast_start.sh           # 快速启动
│   └── run_simulator.sh        # 运行模拟器
│
├── 📁 文档
├── docs/                        # 完整文档目录
│   ├── 01-新手入门/           # 新手指南
│   ├── 02-功能使用/           # 功能文档
│   ├── 03-开发与部署/         # 开发部署
│   ├── 04-故障排查/           # 故障排查
│   ├── 05-架构与设计/         # 架构设计
│   ├── 06-历史记录/           # 历史文档
│   ├── 07-快速参考/           # 快速参考
│   └── README.md               # 文档导航 ⭐
│
├── 📁 部署配置
├── docker-compose.yml           # Docker Compose（默认）
├── docker-compose.dev.yml       # 开发环境配置
├── docker-compose.prod.yml      # 生产环境配置
├── Dockerfile                   # Docker 镜像构建
├── requirements.txt             # Python 依赖
├── run.py                       # 应用启动入口
│
├── 📁 环境配置
├── env.example                  # 环境变量示例（通用）
├── env.local.example            # 本地开发示例
├── env.prod.example             # 生产环境示例
│
└── 📁 其他
    ├── .gitignore              # Git 忽略规则
    ├── mosquitto/              # MQTT 配置
    └── LICENSE                 # 许可证（如有）
```

## 📝 核心文件说明

### 主文档

#### README.md ⭐

**用途**：项目主文档，是了解项目的第一入口

**内容**：
- 项目简介和特性
- 快速开始指南
- 技术栈说明
- 功能概览
- 文档导航

**适用对象**：所有人

---

#### CHANGELOG_v2.2.0.md

**用途**：当前版本（v2.2.0）的更新日志

**内容**：
- 新增功能
- 功能改进
- Bug 修复
- 破坏性变更

**更新频率**：每个版本发布时

---

#### DATABASE_STORAGE.md

**用途**：数据库存储目录说明

**内容**：
- `pg_data/` 和 `pg_data_dev/` 的区别
- 数据库管理指南
- 备份恢复方法

**适用场景**：
- 数据库管理
- 环境切换
- 数据备份

---

#### 项目文件整理总结.md

**用途**：记录项目文件整理工作

**内容**：
- Frontend 整理记录
- Models 整理记录
- Database 整理记录
- Scripts 整理记录

**适用场景**：了解项目结构优化历史

---

## 📁 核心目录说明

### app/ - 后端应用

**技术栈**：FastAPI + SQLModel + PostgreSQL

**主要内容**：
- `api/` - RESTful API 接口
- `core/` - 核心功能（数据库、安全、日志等）
- `models/` - 数据库模型
- `services/` - 业务逻辑

**详细文档**：[app/README.md](./app/README.md)

---

### frontend/ - 前端应用

**技术栈**：Vue 3 + TypeScript + Vite + Three.js

**主要内容**：
- `src/api/` - API 接口层
- `src/views/` - 页面组件
- `src/stores/` - 状态管理
- `src/three/` - 3D 可视化

**详细文档**：[frontend/README.md](./frontend/README.md)

---

### docs/ - 完整文档

**结构清晰**，按主题分类：

1. **01-新手入门** - 快速上手
2. **02-功能使用** - 功能详解
3. **03-开发与部署** - 开发部署
4. **04-故障排查** - 问题解决
5. **05-架构与设计** - 技术架构
6. **06-历史记录** - 历史文档
7. **07-快速参考** - 快速查询

**详细导航**：[docs/README.md](./docs/README.md)

---

### scripts/ - 脚本工具

**两类脚本**：
- **Python脚本** (12个) - 数据管理、功能演示
- **Shell脚本** (19个) - 服务管理、运维工具

**快速参考**：[scripts/QUICK_REFERENCE.md](./scripts/QUICK_REFERENCE.md) ⚡

**详细文档**：[scripts/README.md](./scripts/README.md)

---

### models/ - LSTM 模型

**用途**：存储 LSTM 机器学习模型

**子目录**：
- `lstm/` - 模型文件 (.h5)
- `scalers/` - 标准化器 (.pkl)
- `versions/` - 版本元数据

**详细说明**：[models/README.md](./models/README.md)

---

## 🚀 快速开始

### 新手用户

```bash
# 1. 阅读主文档
cat README.md

# 2. 查看快速启动指南
cat docs/01-新手入门/快速启动指南.md

# 3. 启动系统
./scripts/shell/start.sh
```

### 开发人员

```bash
# 1. 配置开发环境
cat docs/01-新手入门/本地开发环境配置.md

# 2. 启动开发环境
./scripts/shell/start_dev_env.sh

# 3. 查看脚本快速参考
cat scripts/QUICK_REFERENCE.md
```

### 运维人员

```bash
# 1. 查看部署指南
cat docs/03-开发与部署/企业部署完整指南.md

# 2. 查看数据库说明
cat DATABASE_STORAGE.md

# 3. 备份数据
./scripts/shell/backup.sh
```

---

## 📚 文档导航

### 按角色

**新手**：
- [README.md](./README.md) - 项目概览
- [快速启动指南](./docs/01-新手入门/快速启动指南.md)

**开发者**：
- [app/README.md](./app/README.md) - 后端代码
- [frontend/README.md](./frontend/README.md) - 前端代码
- [scripts/QUICK_REFERENCE.md](./scripts/QUICK_REFERENCE.md) - 脚本命令

**运维**：
- [DATABASE_STORAGE.md](./DATABASE_STORAGE.md) - 数据库管理
- [企业部署指南](./docs/03-开发与部署/企业部署完整指南.md)

### 按场景

**首次部署**：
1. [全新系统初始化指南](./docs/01-新手入门/全新系统初始化指南.md)
2. [快速启动指南](./docs/01-新手入门/快速启动指南.md)

**日常开发**：
1. [本地开发快速参考](./docs/07-快速参考/本地开发快速参考.md)
2. [scripts/QUICK_REFERENCE.md](./scripts/QUICK_REFERENCE.md)

**问题排查**：
1. [故障排查目录](./docs/04-故障排查/)
2. [项目问题分析报告](./docs/04-故障排查/项目问题分析报告.md)

---

## 🔧 配置文件说明

### Docker Compose 配置

| 文件 | 用途 | 场景 |
|------|------|------|
| `docker-compose.yml` | 默认配置 | 快速启动 |
| `docker-compose.dev.yml` | 开发环境 | 本地开发 |
| `docker-compose.prod.yml` | 生产环境 | 生产部署 |

### 环境变量

| 文件 | 用途 | 说明 |
|------|------|------|
| `env.example` | 通用示例 | 复制为 `.env` |
| `env.local.example` | 本地开发 | 本地配置参考 |
| `env.prod.example` | 生产环境 | 生产配置参考 |

---

## ⚠️ 注意事项

### 不应提交到 Git 的文件

以下目录/文件已在 `.gitignore` 中：

- `pg_data/` 和 `pg_data_dev/` - 数据库数据
- `models/lstm/*.h5` - LSTM 模型文件
- `models/scalers/*.pkl` - 标准化器
- `logs/` - 日志文件
- `.env` - 环境变量（包含敏感信息）
- `node_modules/` - Node.js 依赖
- `venv/` - Python 虚拟环境

### 重要配置文件

以下文件需要根据环境配置：

- `.env` - 从 `env.example` 复制并修改
- `config/settings.json` - 系统配置

### 数据目录

- `pg_data/` - 生产数据库，**需要备份**
- `pg_data_dev/` - 开发数据库，可随时删除

详细说明见：[DATABASE_STORAGE.md](./DATABASE_STORAGE.md)

---

## 🎯 项目结构设计原则

### 1. 清晰性

- 每个目录职责明确
- 文件命名描述性强
- 结构层次合理

### 2. 可维护性

- 文档与代码同步
- 配置文件集中管理
- 历史记录可追溯

### 3. 易用性

- 新手友好的文档
- 快速参考卡片
- 场景化的指南

### 4. 规范性

- Git 管理规范
- 命名规范统一
- 目录结构标准

---

## 📊 项目规模

| 类型 | 数量 | 说明 |
|------|------|------|
| **代码** | | |
| Python 文件 | 46+ | 后端 + LSTM + 脚本 |
| TypeScript 文件 | 25+ | 前端代码 |
| Vue 组件 | 14+ | 前端页面 |
| **文档** | | |
| Markdown 文档 | 78+ | 完整文档覆盖 |
| 文档目录 | 7 | 按主题分类 |
| **脚本** | | |
| Python 脚本 | 12 | 数据和工具 |
| Shell 脚本 | 19 | 运维管理 |
| **配置** | | |
| Docker 配置 | 3 | 不同环境 |
| 环境变量示例 | 3 | 配置参考 |

---

## 🔗 相关链接

### 主要文档

- [README.md](./README.md) - 项目主文档 ⭐
- [docs/README.md](./docs/README.md) - 文档总导航
- [scripts/QUICK_REFERENCE.md](./scripts/QUICK_REFERENCE.md) - 脚本快速参考 ⭐

### 快速开始

- [快速启动指南](./docs/01-新手入门/快速启动指南.md)
- [全新系统初始化](./docs/01-新手入门/全新系统初始化指南.md)

### 开发文档

- [后端代码说明](./app/README.md)
- [前端开发指南](./frontend/DEVELOPMENT.md)

---

**创建日期**：2026-01-24  
**最后更新**：2026-01-24  
**维护状态**：✅ 活跃维护
