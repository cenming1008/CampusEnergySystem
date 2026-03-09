# 📚 MineEnergySystem 文档中心

> 完整、清晰、易查找的项目文档

**最后更新**：2026-03  
**文档结构**：v2.1（目录与索引已整理）

---

## ⚡ 快速导航

| 我想... | 查看文档 | 预计时间 |
|---------|---------|---------|
| 快速启动系统 | [新手入门 → 快速启动指南](./01-新手入门/快速启动指南.md) | 3 分钟 |
| 管理设备和数据 | [功能使用 → 统一设备管理指南](./02-功能使用/统一设备管理指南.md) | 5 分钟上手 |
| 了解系统架构 | [架构与设计 → 统一架构重构说明](./05-架构与设计/统一架构重构说明.md) | 10 分钟 |
| 详细安装配置 | [新手入门 → 安装配置完整指南](./01-新手入门/安装配置完整指南.md) | 15 分钟 |
| 使用多能源功能 | [功能使用 → 多能源管理指南](./02-功能使用/多能源管理指南.md) | 10 分钟 |
| 使用 AI 预测 | [功能使用 → LSTM 预测完整指南](./02-功能使用/LSTM预测完整指南.md) | 5 分钟上手 |
| 设备分组管理 | [功能使用 → 设备分组快速开始](./02-功能使用/设备分组快速开始.md) | 5 分钟 |
| 设备维护管理 | [功能使用 → 设备维护管理指南](./02-功能使用/设备维护管理指南.md) | 10 分钟 |
| 配置 Git/SSH | [开发部署 → Git 完整指南](./03-开发与部署/Git完整指南.md) | 10 分钟 |
| 企业生产部署 | [开发部署 → 企业部署完整指南](./03-开发与部署/企业部署完整指南.md) | 30 分钟 |
| 了解数据库设计 | [架构与设计 → 数据表说明](./05-架构与设计/DeviceData与EnergyData表说明.md) | 10 分钟 |
| 解决启动问题 | [故障排查 → README](./04-故障排查/README.md) | 立即 |

---

## 📂 文档结构

```
docs/
├── 01-新手入门/               ← 新用户从这里开始
│   ├── README.md
│   ├── 快速启动指南.md
│   ├── 安装配置完整指南.md
│   ├── 本地开发环境配置.md
│   └── 全新系统初始化指南.md
│
├── 02-功能使用/               ← 学习系统功能
│   ├── README.md
│   ├── 统一设备管理指南.md
│   ├── 多能源管理指南.md
│   ├── 多能源管理功能实现说明.md
│   ├── LSTM预测完整指南.md
│   ├── 设备分组快速开始.md
│   ├── 设备维护管理指南.md
│   ├── 数据清理功能说明.md
│   └── 数据自动清理功能说明.md
│
├── 03-开发与部署/             ← 开发和运维
│   ├── README.md
│   ├── Git完整指南.md
│   ├── DOCKER_SCRIPTS.md
│   ├── DATABASE_STORAGE.md
│   ├── OPTIMIZATION_RECOMMENDATIONS.md
│   ├── 系统启动完整指南.md
│   ├── 企业部署完整指南.md
│   ├── 企业部署快速参考.md
│   ├── 日志管理指南.md
│   └── Docker清理与本地运行指南.md
│
├── 04-故障排查/               ← 遇到问题
│   ├── README.md
│   ├── fix_venv_issue.md
│   ├── 控制台警告问题排查.md
│   ├── 数据清理功能故障排查.md
│   ├── 多能源管理问题修复说明.md
│   ├── 紧急修复-重启服务.md
│   ├── 立即修复-操作步骤.md
│   ├── 前端登录问题说明.md
│   ├── 网络连接问题排查报告.md
│   ├── CORS配置修复说明.md
│   ├── 前端BUG修复报告.md
│   └── 项目问题分析报告.md
│
├── 05-架构与设计/             ← 技术文档
│   ├── README.md
│   ├── 统一架构重构说明.md
│   ├── 后端功能实现详解.md
│   ├── 后端调用流程图.md
│   ├── DeviceData与EnergyData表说明.md
│   ├── DeviceService与EnergyService对比说明.md
│   ├── 多对多关系详解.md
│   ├── 枚举设计说明.md
│   ├── 设备层级管理需求分析.md
│   ├── 前后端功能对比分析.md
│   ├── 配置阈值优化报告.md
│   └── 后端代码分析报告.md
│
├── 06-历史记录/               ← 历史与变更记录
│   ├── README.md
│   ├── 根目录整理总结.md
│   ├── 项目文件整理总结.md
│   ├── 全新系统部署总结.md
│   ├── README_全新系统.md
│   ├── CHANGELOG_设备分组功能.md
│   ├── CHANGELOG_维护功能.md
│   ├── 3D矿区场景升级说明.md
│   ├── 矿区场景仿真升级说明.md
│   └── MyEMS资源调研与3D模型建议.md
│
├── 07-快速参考/               ← 速查
│   ├── README.md
│   ├── 本地开发快速参考.md
│   ├── 开始使用-执行清单.md
│   ├── 快速参考-统一设备管理.md
│   └── 清除多能源管理页面数据指南.md
│
└── README.md                  ← 您在这里
```

---

## 🎯 按角色查找文档

### 🆕 新手用户（首次使用）

**目标**：快速启动系统，了解基本功能

1. **阅读**：[快速启动指南](./01-新手入门/快速启动指南.md) ⭐
2. **执行**：`./scripts/shell/start.sh`
3. **访问**：http://localhost:8088/docs
4. **登录**：admin / 123456
5. **下一步**：学习 LSTM 预测功能

**预计耗时**：10 分钟

---

### 💻 开发者（开发新功能）

**目标**：配置开发环境，了解代码结构

1. **架构理解**：[统一架构重构说明](./05-架构与设计/统一架构重构说明.md)
2. **数据库设计**：[数据表说明](./05-架构与设计/DeviceData与EnergyData表说明.md)
3. **安装配置**：[安装配置完整指南](./01-新手入门/安装配置完整指南.md)
4. **Git 配置**：[Git 完整指南](./03-开发与部署/Git完整指南.md)
5. **Docker 管理**：[DOCKER_SCRIPTS](./03-开发与部署/DOCKER_SCRIPTS.md)
6. **性能优化**：[OPTIMIZATION_RECOMMENDATIONS](./03-开发与部署/OPTIMIZATION_RECOMMENDATIONS.md)

**预计耗时**：1 小时

---

### 🤖 数据科学家（使用 AI 功能）

**目标**：训练和使用 LSTM 预测模型

1. **阅读**：[LSTM 预测完整指南](./02-功能使用/LSTM预测完整指南.md) ⭐
2. **生成数据**：使用数据生成 API
3. **训练模型**：调用训练接口
4. **评估优化**：对比模型版本
5. **生产部署**：配置定时任务

**预计耗时**：从 5 分钟（快速上手）到 1 天（生产部署）

---

### 🏗️ 架构师/技术负责人

**目标**：了解系统设计，规划技术方案

1. **架构概览**：[统一架构重构说明](./05-架构与设计/统一架构重构说明.md) ⭐
2. **数据库设计**：[数据表说明](./05-架构与设计/DeviceData与EnergyData表说明.md)
3. **关系设计**：[多对多关系详解](./05-架构与设计/多对多关系详解.md)
4. **枚举规范**：[枚举设计说明](./05-架构与设计/枚举设计说明.md)
5. **需求分析**：[设备层级管理需求分析](./05-架构与设计/设备层级管理需求分析.md)

**预计耗时**：2 小时

---

### 🔧 运维人员（部署维护）

**目标**：部署系统，监控运行，处理问题

1. **快速部署**：[快速启动指南](./01-新手入门/快速启动指南.md)
2. **企业部署**：[企业部署完整指南](./03-开发与部署/企业部署完整指南.md)
3. **Docker 管理**：[DOCKER_SCRIPTS](./03-开发与部署/DOCKER_SCRIPTS.md)
4. **性能优化**：[OPTIMIZATION_RECOMMENDATIONS](./03-开发与部署/OPTIMIZATION_RECOMMENDATIONS.md)
5. **故障排查**：[故障排查](./04-故障排查/README.md)

**关键命令**：
```bash
./scripts/shell/test_health.sh   # 系统健康检查
./scripts/shell/status.sh        # 服务状态
docker compose logs -f           # 实时日志
```

---

## 🚀 快速开始（3步）

1. **启动**：`./bin/fast_start.sh` 或 `./scripts/shell/start.sh`
2. **验证**：打开 http://localhost:8088/docs 或 `curl http://localhost:8088/health`
3. **登录**：admin / 123456（生产环境请修改）

**详细说明与问题排查**：[快速启动指南](./01-新手入门/快速启动指南.md)

---

## 💡 常用命令速查

### Docker 管理

```bash
docker compose up -d    # 启动
docker compose ps       # 状态
docker compose logs -f backend   # 日志
docker compose down     # 停止
```

更多命令与说明见 [开发与部署 → README](./03-开发与部署/README.md)、[DOCKER_SCRIPTS](./03-开发与部署/DOCKER_SCRIPTS.md)。

### Python 环境

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python run.py
```

### Git 操作

```bash
# 提交代码
git add .
git commit -m "feat: 新功能"
git push
```

SSH 配置与推送优化请参考：[开发部署 → Git 完整指南](./03-开发与部署/Git完整指南.md)

### 系统检查

```bash
./scripts/shell/test_health.sh   # 完整检查
./scripts/shell/status.sh        # 容器状态
```

---

## 🔍 常见问题快速解决

| 问题 | 解决方案 | 详细文档 |
|------|---------|---------|
| Docker 未启动 | `open /Applications/Docker.app` | [故障排查](./04-故障排查/README.md#问题1docker-未安装或未启动) |
| 端口被占用 | `docker compose down` | [故障排查](./04-故障排查/README.md#问题2端口被占用) |
| pip 不可用 | `python3 -m pip install ...` | [虚拟环境问题](./04-故障排查/fix_venv_issue.md) |
| Git push 慢 | 查看 Git 优化章节 | [Git 优化](./03-开发与部署/Git完整指南.md#2-git-推送优化) |
| TensorFlow 未安装 | `pip install tensorflow` | [LSTM 指南](./02-功能使用/LSTM预测完整指南.md#问题1tensorflow未安装) |
| 数据库连接失败 | `sleep 20 && docker compose restart db` | [故障排查](./04-故障排查/README.md#问题2数据库连接失败) |

---

## 📊 文档整理说明

### v2.0 更新（2026-01-13）

**主要改进**：
- ✅ 创建分类目录结构（新手入门/功能使用/开发部署/故障排查）
- ✅ 合并重复文档（安装指南、LSTM 文档、Git 文档）
- ✅ 为每个目录创建导航文档
- ✅ 归档临时说明文档
- ✅ 优化文档查找体验

**文档对比**：
- 根目录文档：19个 → 5个（-73%）
- 重复内容：消除 80%
- 查找时间：从"翻找"到"定位"
- 新手友好度：大幅提升

**说明**：文档已按目录分层整理，优先从导航和目录 README 查找。

---

## 🎓 学习路径推荐

### 路径1：快速体验（15分钟）

1. 阅读 [快速启动指南](./01-新手入门/快速启动指南.md)（3分钟）
2. 启动系统 `./scripts/shell/start.sh`（3-5分钟）
3. 访问 API 文档（2分钟）
4. 测试登录和基本 API（5分钟）

### 路径2：深入学习（2小时）

1. 完整阅读 [安装配置完整指南](./01-新手入门/安装配置完整指南.md)（20分钟）
2. 配置本地开发环境（30分钟）
3. 学习 [LSTM 预测功能](./02-功能使用/LSTM预测完整指南.md)（60分钟）
4. 训练第一个模型（10分钟）

### 路径3：生产部署（1天）

1. 学习 Docker 部署（1小时）
2. 配置 Git 和 SSH（30分钟）
3. 学习性能优化（1小时）
4. 配置 LSTM 定时任务（2小时）
5. 测试和监控（剩余时间）

---

## 📞 获取帮助

### 1. 查看文档

按优先级查找：
1. 本 README 的快速导航
2. 各子目录的 README
3. 具体问题的详细文档
4. 归档文档（如果需要）

### 2. 运行诊断

```bash
# 系统健康检查
./scripts/shell/test_health.sh

# 查看日志
docker compose logs -f backend

# 查看服务状态
docker compose ps
```

### 3. 查看示例

- API 文档：http://localhost:8088/docs
- API 测试：使用 Swagger UI 的 "Try it out"

### 4. 常见问题

查看 [故障排查](./04-故障排查/README.md)

---

## 🔗 外部资源

### 技术文档

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [Docker](https://docs.docker.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [TensorFlow](https://www.tensorflow.org/)

### 相关工具

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [VS Code](https://code.visualstudio.com/)
- [Postman](https://www.postman.com/)

---

## 💬 反馈建议

如果您发现文档问题或有改进建议：

1. 在项目中提 Issue
2. 提交 Pull Request
3. 联系维护团队

---

## 📝 文档维护

### 更新记录

- **2026-03**：整理目录索引，补全各分类下的文档列表（v2.1）
- **2026-01-13**：完成文档结构重组（v2.0）
- **2026-01-13**：新增 LSTM 完整使用指南、Git 完整指南，合并重复文档

### 维护原则

- ✅ 保持文档最新
- ✅ 消除重复内容
- ✅ 清晰的分类结构
- ✅ 新手友好
- ✅ 快速查找

---

**🎉 感谢使用 MineEnergySystem！**

如有任何问题，请先查看对应的文档分类，大部分问题都能找到解决方案。
