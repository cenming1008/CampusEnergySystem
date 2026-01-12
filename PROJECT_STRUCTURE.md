# 📁 项目结构说明

> 本文档说明项目的目录结构和文件组织方式

**最后更新**：2026-01-12

---

## 🗂️ 整体结构

```
MineEnergySystem/
├── app/                    # 后端应用代码
├── frontend/               # 前端应用代码
├── scripts/                # 脚本工具集
├── docs/                   # 文档中心
├── logs/                   # 运行日志
├── pg_data/                # PostgreSQL 数据目录
├── mosquitto/              # MQTT 配置和数据
├── backups/                # 备份文件
├── config/                 # 配置文件
├── venv/                   # Python 虚拟环境
├── docker-compose.yml      # Docker 编排配置
├── Dockerfile              # Docker 镜像构建文件
├── requirements.txt        # Python 依赖
├── env.example             # 环境变量模板
├── run.py                  # 后端启动入口
├── quick_start.sh          # 快速启动（快捷方式）
└── README.md               # 项目主文档
```

---

## 📂 核心目录详解

### `app/` - 后端应用
```
app/
├── api/                    # API 层
│   ├── deps.py            # 依赖注入
│   └── endpoints/         # API 端点
│       ├── auth.py        # 认证接口
│       ├── devices.py     # 设备管理
│       ├── telemetry.py   # 遥测数据
│       ├── alarms.py      # 报警管理
│       ├── analysis.py    # 数据分析
│       ├── fdd.py         # 故障诊断
│       ├── reports.py     # 报表导出
│       └── health.py      # 健康检查
├── core/                   # 核心基础设施
│   ├── config.py          # 配置加载
│   ├── database.py        # 数据库连接
│   ├── redis.py           # Redis 客户端
│   ├── security.py        # JWT 认证
│   ├── logger.py          # 日志配置
│   ├── settings.py        # 配置管理
│   ├── socket_manager.py  # WebSocket 管理
│   ├── error_handlers.py  # 异常处理
│   ├── exceptions.py      # 自定义异常
│   └── response.py        # 统一响应格式
├── services/               # 业务逻辑层
│   ├── device_service.py  # 设备业务逻辑
│   ├── alarm_service.py   # 报警业务逻辑
│   ├── analysis_service.py # 分析业务逻辑
│   ├── fdd_service.py     # 故障诊断逻辑
│   ├── data_processor.py  # 数据处理
│   ├── mqtt_worker.py     # MQTT 消息处理
│   └── mqtt_publisher.py  # MQTT 消息发布
├── models/                 # 数据模型
│   └── tables.py          # 数据库表定义
├── main.py                # FastAPI 应用入口
└── README.md              # 后端代码结构说明
```

**设计理念**：
- **分层架构**：API → Service → Core → Model
- **单一职责**：每层只负责自己的职责
- **依赖注入**：使用 FastAPI 的依赖注入系统
- **易于测试**：业务逻辑与框架解耦

**参考文档**：[app/README.md](app/README.md)

---

### `frontend/` - 前端应用
```
frontend/
├── src/
│   ├── api/               # API 请求封装
│   ├── components/        # Vue 组件
│   ├── views/             # 页面视图
│   ├── stores/            # Pinia 状态管理
│   ├── router/            # Vue Router 路由
│   ├── assets/            # 静态资源
│   ├── utils/             # 工具函数
│   └── main.ts            # 入口文件
├── public/                # 公共资源
├── package.json           # npm 配置
├── vite.config.ts         # Vite 配置
└── tsconfig.json          # TypeScript 配置
```

**技术栈**：
- Vue 3 + TypeScript
- Vite（构建工具）
- Pinia（状态管理）
- Element Plus（UI 组件）
- ECharts（数据可视化）

---

### `scripts/` - 脚本工具集
```
scripts/
├── shell/                 # Shell 脚本
│   ├── start.sh          # 🚀 启动所有服务
│   ├── stop.sh           # 🛑 停止所有服务
│   ├── status.sh         # 📊 查看服务状态
│   ├── restart_backend.sh # 🔄 重启后端
│   ├── rebuild_backend.sh # 🔨 重新构建
│   ├── fix_db.sh         # 🔧 修复数据库
│   ├── test_health.sh    # 🏥 测试健康检查
│   ├── check_websocket.sh # 🌐 测试 WebSocket
│   ├── check_mac_env.sh  # 🍎 检查 Mac 环境
│   └── start_frontend.sh # 💻 启动前端
├── python/                # Python 脚本
│   ├── create_admin.py   # 👤 创建管理员
│   ├── init_devices.py   # 📱 初始化设备
│   ├── reset_system.py   # 🔄 重置系统
│   ├── check_config.py   # ⚙️ 检查配置
│   ├── clear_db.py       # 🗑️ 清空数据库
│   ├── simulator.py      # 🎮 数据模拟器
│   └── stress_test.py    # 💪 压力测试
└── README.md              # 脚本使用指南
```

**使用规范**：
- 所有脚本从项目根目录执行
- Shell 脚本用于运维操作
- Python 脚本用于数据和系统管理

**参考文档**：[scripts/README.md](scripts/README.md)

---

### `docs/` - 文档中心
```
docs/
├── README.md              # 文档导航
├── DOCS_CONSOLIDATION.md  # 文档整合报告
└── archive/               # 归档文档
    ├── README_ARCHIVE.md  # 归档说明
    ├── CHANGELOG_MAC.md
    ├── STARTUP_FLOW.md
    ├── TROUBLESHOOTING.md
    ├── WEBSOCKET_FIX.md
    ├── HEALTH_CHECK_GUIDE.md
    ├── HEALTH_CHECK_IMPLEMENTATION.md
    ├── NEXT_STEPS.md
    ├── PROJECT_ROADMAP.md
    ├── README_SCRIPTS.md
    └── 项目架构分析.md
```

**文档策略**：
- **主文档**：`README.md` - 持续更新
- **归档文档**：`archive/` - 只读参考
- **单一来源**：避免信息重复

---

### `config/` - 配置文件
```
config/
└── settings.json          # 报警阈值等配置
```

**配置管理**：
- 业务配置：`config/settings.json`
- 环境变量：`.env` 文件（从 `env.example` 复制）
- Docker 配置：`docker-compose.yml`

---

### `logs/` - 运行日志
```
logs/
├── ems_app_YYYY-MM-DD.log    # 应用日志（按天）
└── ems_error_YYYY-MM-DD.log  # 错误日志（按天）
```

**日志策略**：
- 按日期分割
- 自动清理（保留最近 7 天）
- 分级记录：DEBUG / INFO / WARNING / ERROR

---

### `pg_data/` - 数据库数据
```
pg_data/
└── (PostgreSQL 数据文件)
```

**⚠️ 重要**：
- 不要手动修改此目录
- 需要定期备份
- `.gitignore` 已排除此目录

---

### `mosquitto/` - MQTT 配置
```
mosquitto/
├── config/
│   └── mosquitto.conf     # MQTT 配置文件
├── data/                  # MQTT 持久化数据
└── log/                   # MQTT 日志
```

---

### `backups/` - 备份文件
```
backups/
└── *.tar.gz               # 数据库备份文件
```

**备份策略**：
- 定期备份数据库
- 命名格式：`pg_data_backup_YYYYMMDD_HHMMSS.tar.gz`
- 建议保留最近 30 天的备份

---

## 📄 根目录文件说明

### 核心配置文件

| 文件 | 说明 | 是否必需 |
|------|------|---------|
| `docker-compose.yml` | Docker 服务编排配置 | ✅ 必需 |
| `Dockerfile` | 后端 Docker 镜像构建 | ✅ 必需 |
| `requirements.txt` | Python 依赖列表 | ✅ 必需 |
| `run.py` | 后端启动入口 | ✅ 必需 |
| `env.example` | 环境变量模板 | ✅ 建议 |
| `.env` | 实际环境变量配置 | 🔒 不提交 |

### 文档文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目主文档 |
| `PROJECT_STRUCTURE.md` | 本文档 |

### 快捷脚本

| 文件 | 说明 |
|------|------|
| `quick_start.sh` | 快速启动（调用 scripts/shell/start.sh） |

---

## 🎯 文件组织原则

### 1. 分类清晰
- **代码**：`app/`, `frontend/`
- **脚本**：`scripts/`
- **文档**：`docs/`
- **配置**：`config/`, `.env`
- **数据**：`pg_data/`, `mosquitto/`
- **临时**：`logs/`, `backups/`

### 2. 职责单一
- 每个目录只负责一类文件
- 避免混合存放不同类型的文件

### 3. 易于查找
- 目录命名清晰明确
- 重要文件放在根目录
- 详细文件放在子目录

### 4. 便于维护
- 临时文件集中管理
- 备份文件单独存放
- 归档文档独立目录

---

## 🔍 快速查找

### 我想...

| 需求 | 文件/目录 |
|------|----------|
| 启动系统 | `quick_start.sh` 或 `scripts/shell/start.sh` |
| 查看文档 | `README.md` |
| 修改后端代码 | `app/` |
| 修改前端代码 | `frontend/` |
| 运行脚本 | `scripts/` |
| 查看日志 | `logs/` |
| 备份数据 | `backups/` |
| 修改配置 | `config/` 或 `.env` |

---

## 📊 项目规模

### 代码统计（估算）
- **后端代码**：~5,000 行 Python
- **前端代码**：~8,000 行 TypeScript/Vue
- **脚本代码**：~1,500 行 Shell/Python
- **文档**：~2,000 行 Markdown

### 文件统计
- **总文件数**：~30 个核心文件（不含依赖和数据）
- **Python 文件**：~25 个
- **Shell 脚本**：~10 个
- **配置文件**：~5 个
- **文档文件**：~10 个

---

## 🚀 开发工作流

### 新功能开发
```
1. 查看需求
   └─ README.md - 项目路线图

2. 设计方案
   └─ docs/ - 参考架构文档

3. 编写代码
   └─ app/ 或 frontend/

4. 测试功能
   └─ scripts/python/simulator.py

5. 更新文档
   └─ README.md
```

### Bug 修复
```
1. 查看日志
   └─ logs/

2. 复现问题
   └─ scripts/python/simulator.py

3. 修改代码
   └─ app/ 或 frontend/

4. 测试验证
   └─ scripts/shell/test_health.sh

5. 重启服务
   └─ scripts/shell/restart_backend.sh
```

---

## 💡 最佳实践

### 文件命名
- **小写 + 下划线**：`my_module.py`
- **描述性**：`create_admin.py` 而非 `admin.py`
- **统一后缀**：`.py` / `.sh` / `.md`

### 代码组织
- **模块化**：功能独立，职责单一
- **层次清晰**：遵循分层架构
- **注释完整**：关键代码都有注释

### 文档维护
- **及时更新**：代码变更后更新文档
- **单一来源**：避免文档重复
- **示例完整**：提供可运行的示例

---

## 🔄 版本控制

### Git 管理
```
.gitignore 排除：
- venv/              # 虚拟环境
- __pycache__/       # Python 缓存
- *.pyc              # 编译文件
- .env               # 环境变量（敏感信息）
- pg_data/           # 数据库数据
- logs/              # 日志文件
- backups/           # 备份文件
- node_modules/      # npm 依赖
- frontend/dist/     # 前端构建产物
```

### 提交规范
```bash
# 功能开发
git commit -m "feat: 添加设备控制功能"

# Bug 修复
git commit -m "fix: 修复 WebSocket 连接问题"

# 文档更新
git commit -m "docs: 更新项目结构说明"

# 代码重构
git commit -m "refactor: 优化数据处理逻辑"
```

---

## 📚 相关文档

- [README.md](README.md) - 项目主文档
- [app/README.md](app/README.md) - 后端代码结构
- [scripts/README.md](scripts/README.md) - 脚本使用指南
- [docs/README.md](docs/README.md) - 文档导航

---

**维护者**：项目团队  
**最后更新**：2026-01-12  
**版本**：v2.0.0
