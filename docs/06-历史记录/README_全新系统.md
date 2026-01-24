# 全新系统快速启动 🚀

> **5 分钟快速部署指南** - 适用于无历史数据的全新系统

---

## 📋 前提条件

- ✅ Docker 和 Docker Compose 已安装
- ✅ Python 3.9+ 已安装（如果本地运行）
- ✅ 8088 和 5432 端口可用

---

## 🚀 5 分钟部署

### 步骤 1: 克隆项目

```bash
git clone <repository-url>
cd MineEnergySystem
```

### 步骤 2: 启动服务

```bash
# Docker 环境（推荐）
docker-compose up -d

# 等待服务启动（约 30 秒）
docker-compose logs -f backend
# 看到 "✨ 系统就绪" 即可 Ctrl+C 退出
```

### 步骤 3: 初始化数据库

```bash
# 创建干净的数据库 + 演示数据
docker exec mine_backend python scripts/python/rebuild_database.py --confirm --demo-data
```

### 步骤 4: 访问系统

```bash
# API 文档
open http://localhost:8088/docs

# 登录信息
# 用户名: admin
# 密码: 123456
```

**完成！** 🎉

---

## 🎯 接下来做什么？

### 1. 查看演示设备

```bash
curl http://localhost:8088/devices/
```

您会看到 7 个预创建的设备（电力、水、气、热、冷）

### 2. 查看支持的设备类型

```bash
curl http://localhost:8088/devices/types
```

系统支持 11 种设备类型

### 3. 创建您的第一个设备

```bash
curl -X POST http://localhost:8088/devices/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的设备",
    "sn": "MY001",
    "device_type": "water_meter"
  }'
```

### 4. 上报数据

```bash
curl -X POST http://localhost:8088/devices/1/data \
  -H "Content-Type: application/json" \
  -d '{
    "consumption": 10.5,
    "flow_rate": 2.3,
    "pressure": 0.3
  }'
```

### 5. 查看碳排放

```bash
# 获取当前时间的碳排放汇总
curl "http://localhost:8088/energy/carbon/summary?start_time=2024-01-01T00:00:00&end_time=2024-12-31T23:59:59"
```

---

## 📚 学习资源

### 必读文档

1. **[统一设备管理指南](docs/02-功能使用/统一设备管理指南.md)** ⭐⭐⭐⭐⭐
   - 完整的使用指南
   - API 示例
   - 最佳实践

2. **[快速参考卡片](快速参考-统一设备管理.md)** ⭐⭐⭐⭐⭐
   - 3 分钟速查
   - 常用命令
   - API 示例

3. **[全新系统初始化指南](docs/01-新手入门/全新系统初始化指南.md)** ⭐⭐⭐⭐
   - 详细的初始化步骤
   - 故障排查
   - 生产环境配置

### 进阶文档

- [统一架构重构说明](docs/统一架构重构说明.md) - 了解系统架构
- [多能源管理指南](docs/02-功能使用/多能源管理指南.md) - 深入多能源功能
- [LSTM预测指南](docs/02-功能使用/LSTM预测完整指南.md) - AI 预测功能

---

## 🧪 运行演示

系统提供了完整的演示脚本：

```bash
# Docker 环境
docker exec mine_backend python scripts/python/demo_unified_system.py

# 本地环境
python scripts/python/demo_unified_system.py
```

演示内容：
- ✅ 创建 8 种不同类型的设备
- ✅ 统一接口上报数据
- ✅ 查询和统计数据
- ✅ 碳排放计算
- ✅ 设备筛选

---

## 🎯 核心特性

### 1. 智能设备创建

只需 3 个字段，系统自动配置其他所有字段：

```json
{
  "name": "1号水表",
  "sn": "WATER001",
  "device_type": "water_meter"
}
```

自动配置：
- ✅ `energy_type`: "water"
- ✅ `device_category`: "water_meter"
- ✅ `unit`: "m³/h"
- ✅ `rated_capacity`: 50.0

### 2. 统一数据上报

所有设备类型使用同一个接口：

```
POST /devices/{id}/data
```

支持：电力、水、燃气、热力、冷气、蒸汽

### 3. 自动碳排放计算

数据上报时自动计算并记录碳排放，无需额外操作。

### 4. 11 种设备类型

- ⚡ 电力：用电设备、光伏、风电、储能、充电桩
- 💧 水系统：水表
- 🔥 燃气系统：燃气表
- 🌡️ 热力系统：热量表、蒸汽表
- ❄️ 制冷系统：冷量表

### 5. 配置化扩展

添加新设备类型只需编辑配置文件，无需修改代码。

---

## 🔧 开发环境

### 本地运行（不使用 Docker）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp env.example .env
vim .env

# 3. 启动后端
python run.py

# 4. 初始化数据库
python scripts/python/rebuild_database.py --confirm --demo-data
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

---

## 📊 系统架构

```
┌─────────────────────────────────────────┐
│         统一 API 层 (FastAPI)            │
│  - 智能设备创建                          │
│  - 统一数据上报                          │
│  - 自动碳排放计算                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      设备服务层 (DeviceService)          │
│  - 设备类型注册表                        │
│  - 字段自动配置                          │
│  - 数据验证和路由                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       数据存储层 (TimescaleDB)           │
│  - EnergyData (统一能源数据)            │
│  - CarbonEmission (碳排放)              │
│  - Device (设备信息)                     │
└─────────────────────────────────────────┘
```

---

## 💡 最佳实践

### 1. 生产环境部署

- 修改默认密码
- 配置 HTTPS
- 设置防火墙规则
- 定期备份数据库
- 配置日志轮转

### 2. 设备命名

- 使用有意义的名称
- 包含位置信息
- 统一命名规范

### 3. 序列号管理

- 格式：`{类型}{编号}`
- 示例：`WATER001`, `SOLAR-A01`
- 保持唯一性

### 4. 数据上报

- 选择合适的频率
- 电力设备：1-5 分钟
- 其他设备：5-30 分钟

---

## 🐛 故障排查

### 服务启动失败

```bash
# 查看日志
docker-compose logs backend

# 重启服务
docker-compose restart backend
```

### 数据库连接失败

```bash
# 检查数据库
docker-compose ps
docker-compose logs timescaledb

# 重启数据库
docker-compose restart timescaledb
```

### 端口被占用

```bash
# 修改 docker-compose.yml 中的端口
# 8088 -> 8089
# 5432 -> 5433
```

---

## 📞 获取帮助

- 📖 查看文档：`docs/` 目录
- 🐛 提交 Issue
- 💬 技术讨论

---

## 🎉 恭喜！

您已经成功部署了一个**现代化的、统一的**能源管理系统！

**特点**：
- ✅ 架构简洁
- ✅ 易于使用
- ✅ 功能强大
- ✅ 易于扩展

开始您的能源管理之旅吧！🚀

---

**版本**: v2.2.0  
**更新**: 2026-01-24  
**适用**: 全新系统部署
