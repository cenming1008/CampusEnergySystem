# Python 脚本工具集

Python 脚本用于系统初始化、数据管理、功能演示和开发测试。

## 📁 脚本列表

### 🚀 系统初始化与管理

#### `init_complete_system.py` - 完整系统初始化 ⭐

**用途**：初始化完整的系统数据，包括管理员、设备、测试数据等

**使用**：
```bash
python scripts/python/init_complete_system.py
```

**功能**：
- ✅ 创建管理员账户（admin/admin123）
- ✅ 创建多种类型的设备
- ✅ 生成历史能源数据
- ✅ 初始化告警记录
- ✅ 设置设备分组和位置
- ✅ 创建维护记录

**适用场景**：
- 首次部署系统
- 重置开发环境
- 演示准备

---

#### `create_admin.py` - 创建管理员账户

**用途**：单独创建或重置管理员账户

**使用**：
```bash
python scripts/python/create_admin.py
```

**交互式输入**：
- 用户名（默认：admin）
- 密码（默认：admin123）

**适用场景**：
- 忘记管理员密码
- 创建新管理员

---

#### `rebuild_database.py` - 重建数据库 ⚠️

**用途**：删除并重建所有数据库表

**使用**：
```bash
python scripts/python/rebuild_database.py
```

**警告**：
- ❌ 会删除所有数据
- ❌ 不可逆操作
- ❌ 生产环境禁用

**适用场景**：
- 数据库结构变更后
- 开发环境重置
- 清空所有数据

---

#### `check_config.py` - 检查配置

**用途**：验证系统配置和环境变量

**使用**：
```bash
python scripts/python/check_config.py
```

**检查项**：
- ✅ 环境变量完整性
- ✅ 数据库连接
- ✅ Redis 连接
- ✅ MQTT 配置
- ✅ 文件路径有效性

**输出**：彩色配置报告

---

### 🎯 功能演示脚本

#### `demo_unified_system.py` - 统一系统演示

**用途**：演示完整的系统功能

**使用**：
```bash
python scripts/python/demo_unified_system.py
```

**演示内容**：
- 设备管理
- 能源数据采集
- 告警功能
- 数据查询
- 报表生成

**数据**：创建完整的测试数据集

---

#### `demo_device_group.py` - 设备分组演示

**用途**：演示设备分组功能

**使用**：
```bash
python scripts/python/demo_device_group.py
```

**演示内容**：
- 创建设备分组
- 添加设备到分组
- 分组层级管理
- 分组查询和统计

**数据**：
- 3个设备分组
- 多个设备关联

---

#### `demo_location.py` - 位置管理演示

**用途**：演示位置层级管理功能

**使用**：
```bash
python scripts/python/demo_location.py
```

**演示内容**：
- 创建位置层级（区域→车间→设备位置）
- 设备关联到位置
- 位置树形结构
- 位置统计查询

**数据**：
- 矿区 → 东区 → 1号车间 → 设备位置

---

#### `demo_maintenance.py` - 维护管理演示

**用途**：演示设备维护管理功能

**使用**：
```bash
python scripts/python/demo_maintenance.py
```

**演示内容**：
- 创建维护计划
- 维护任务执行
- 维护记录管理
- 维护状态流转

**数据**：
- 多种维护类型（日常、维修、巡检等）
- 不同维护状态

---

### 🔧 开发工具

#### `simulator_unified.py` - 统一设备模拟器 ⭐

**用途**：多能源设备数据模拟器，支持远程控制

**使用**：
```bash
python scripts/python/simulator_unified.py
```

**功能**：
- ✅ 支持多种能源类型（电、水、气等）
- ✅ 支持多种设备类型
- ✅ 更真实的数据波动
- ✅ 异常数据模拟
- ✅ 可配置设备数量和频率

**推荐使用**：开发和演示环境

---

#### `device_gateway.py` - 设备网关采集器

**用途**：从真实设备读取数据并转发到 MQTT，用于接入 Modbus/HTTP 等硬件

**使用**：
```bash
python scripts/python/device_gateway.py
```

**功能**：
- ✅ 支持 Modbus TCP/RTU、HTTP API、串口
- ✅ 可配置多设备与寄存器/字段映射
- ✅ 定时采集并发布到 `mine/telemetry`，与模拟器主题一致

**依赖**：`pip install pymodbus paho-mqtt`（HTTP 需 `requests`）。设备列表与寄存器映射在脚本内 `DEVICE_CONFIG` 中配置。

**适用场景**：生产或测试环境接入真实电表、水表等设备。

---

#### `generate_training_data.py` - 生成训练数据

**用途**：为 LSTM 模型生成训练数据

**使用**：
```bash
python scripts/python/generate_training_data.py
```

**功能**：
- 生成历史能源消耗数据
- 支持多种数据模式（日周期、趋势等）
- 输出符合模型训练要求的格式

**参数**：
- 时间范围：可配置
- 设备数量：可配置
- 数据质量：添加随机噪声

**适用场景**：
- LSTM 模型训练前
- 测试预测功能

---

#### `stress_test.py` - 压力测试工具

**用途**：对系统进行压力测试

**使用**：
```bash
python scripts/python/stress_test.py
```

**测试项目**：
- API 并发请求测试
- 数据库查询性能
- WebSocket 连接测试
- 内存和CPU使用率

**输出**：
- 响应时间统计
- 吞吐量报告
- 错误率分析
- 性能瓶颈识别

**适用场景**：
- 性能测试
- 容量规划
- 优化前后对比

---

## 🚀 快速开始

### 首次部署

```bash
# 1. 初始化完整系统（推荐）
python scripts/python/init_complete_system.py

# 2. 启动设备模拟器
python scripts/python/simulator_unified.py
```

### 功能演示

```bash
# 演示完整系统
python scripts/python/demo_unified_system.py

# 演示特定功能
python scripts/python/demo_device_group.py
python scripts/python/demo_location.py
python scripts/python/demo_maintenance.py
```

### 开发测试

```bash
# 模拟设备数据
python scripts/python/simulator_unified.py

# 真实设备采集（需配置 DEVICE_CONFIG）
python scripts/python/device_gateway.py

# 压力测试
python scripts/python/stress_test.py

# 检查配置
python scripts/python/check_config.py
```

### 数据重置

```bash
# 方式1：重建数据库（删除所有数据）
python scripts/python/rebuild_database.py

# 方式2：重新初始化（包含测试数据）
python scripts/python/rebuild_database.py
python scripts/python/init_complete_system.py
```

---

## 📝 脚本依赖

### 环境要求

- Python 3.10+
- 虚拟环境激活

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 必需服务

运行脚本前，确保以下服务正常运行：

- ✅ PostgreSQL/TimescaleDB（数据库）
- ✅ Redis（缓存）
- ✅ MQTT Broker（消息队列）

**检查服务**：
```bash
./scripts/shell/status.sh
```

---

## 🔧 开发规范

### 文件命名

- 小写字母 + 下划线
- 描述性名称
- `.py` 后缀

### 代码结构

```python
#!/usr/bin/env python3
"""
脚本说明
- 功能点1
- 功能点2
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.logger import logger

def main():
    """主函数"""
    logger.info("开始执行...")
    # 业务逻辑
    logger.success("执行完成！")

if __name__ == "__main__":
    main()
```

### 日志规范

使用 `loguru` 记录日志：

```python
from app.core.logger import logger

logger.info("ℹ️ 信息日志")
logger.success("✅ 成功日志")
logger.warning("⚠️ 警告日志")
logger.error("❌ 错误日志")
```

### 错误处理

```python
try:
    # 业务逻辑
    result = do_something()
except Exception as e:
    logger.error(f"❌ 执行失败: {e}")
    sys.exit(1)
```

---

## ⚠️ 注意事项

### 危险操作

以下脚本会删除数据，使用前务必备份：

- ❌ `rebuild_database.py` - 删除所有表和数据

### 执行路径

脚本必须从**项目根目录**执行：

```bash
# ✅ 正确
python scripts/python/init_complete_system.py

# ❌ 错误
cd scripts/python && python init_complete_system.py
```

### 权限问题

如果遇到权限错误：

```bash
# 添加执行权限
chmod +x scripts/python/*.py
```

---

## 🐛 故障排查

### 问题1：ModuleNotFoundError

**原因**：未正确设置 Python 路径

**解决**：
```bash
# 确保从项目根目录执行
cd /path/to/MineEnergySystem
python scripts/python/xxx.py
```

### 问题2：数据库连接失败

**检查**：
```bash
# 查看数据库状态
./scripts/shell/status.sh

# 测试连接
python scripts/python/check_config.py
```

### 问题3：MQTT 连接失败

**检查**：
```bash
# 确保 MQTT 服务运行
docker ps | grep mqtt

# 测试 MQTT
./scripts/shell/check_websocket.sh
```

---

## 📚 相关文档

- [脚本总览](../README.md) - 脚本工具集主文档
- [Shell 脚本](../shell/README.md) - Shell 脚本文档
- [快速启动指南](../../docs/01-新手入门/快速启动指南.md)
- [全新系统初始化指南](../../docs/01-新手入门/全新系统初始化指南.md)

---

## 📊 脚本分类速查

### 按使用频率

**高频使用**：
- ⭐ `init_complete_system.py` - 系统初始化
- ⭐ `simulator_unified.py` - 数据模拟
- `check_config.py` - 配置检查

**中频使用**：
- `demo_*.py` - 功能演示
- `create_admin.py` - 创建管理员
- `device_gateway.py` - 真实设备采集

**低频使用**：
- `rebuild_database.py` - 重建数据库（危险）
- `stress_test.py` - 压力测试
- `generate_training_data.py` - 训练数据生成

### 按用户类型

**新手用户**：
- `init_complete_system.py` - 快速开始
- `demo_unified_system.py` - 了解功能

**开发人员**：
- `simulator_unified.py` - 开发调试
- `device_gateway.py` - 真实设备接入
- `check_config.py` - 环境检查
- `stress_test.py` - 性能测试

**系统管理员**：
- `create_admin.py` - 用户管理
- `rebuild_database.py` - 数据维护

---

**创建日期**: 2026-01-24  
**最后更新**: 2026-01-24  
**维护状态**: ✅ 活跃维护
