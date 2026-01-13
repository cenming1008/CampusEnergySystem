# 📁 项目文件组织说明

> 本文档说明项目文件的组织结构和最近的整理变更

**整理日期**: 2026-01-13  
**整理原因**: 优化根目录结构，提升文件管理清晰度

---

## 📊 整理前后对比

### 整理前（根目录混乱）

```
MineEnergySystem/
├── README.md
├── START_HERE.md
├── INSTALL.md
├── DOCKER_SCRIPTS.md
├── PROJECT_STRUCTURE.md
├── quick_start.sh
├── fast_start.sh
├── start_frontend.sh
├── run_simulator.sh
├── init_devices.sh
├── check_system.sh
├── app/
├── docs/
├── frontend/
└── scripts/
```

### 整理后（清晰有序）✅

```
MineEnergySystem/
├── README.md              # 主文档（保留）
├── START_HERE.md          # 快速开始（保留）
├── PROJECT_STRUCTURE.md   # 项目结构（保留）
│
├── bin/                   # 🆕 可执行脚本目录
│   ├── README.md
│   ├── quick_start.sh
│   ├── fast_start.sh
│   ├── start_frontend.sh
│   ├── run_simulator.sh
│   ├── init_devices.sh
│   └── check_system.sh
│
├── docs/                  # 📚 文档目录（增强）
│   ├── README.md
│   ├── INSTALL.md         # ← 从根目录移动
│   ├── DOCKER_SCRIPTS.md  # ← 从根目录移动
│   ├── 快速启动指南.md
│   ├── LSTM完整使用指南.md
│   └── ...
│
├── app/                   # 后端代码
├── frontend/              # 前端代码
└── scripts/               # Python 脚本
    └── python/
```

---

## 🎯 整理规则

### 根目录保留原则
**只保留最常用的顶级文档**：
- ✅ `README.md` - 项目主文档
- ✅ `START_HERE.md` - 快速入门
- ✅ `PROJECT_STRUCTURE.md` - 项目结构
- ✅ `FILE_ORGANIZATION.md` - 本文档

### bin/ 目录
**存放所有可执行的 shell 脚本**：
- 启动脚本（`quick_start.sh`, `fast_start.sh`）
- 工具脚本（`init_devices.sh`, `run_simulator.sh`）
- 管理脚本（`check_system.sh`）

**优势**：
- ✅ 集中管理
- ✅ 权限统一
- ✅ 易于查找

### docs/ 目录
**存放所有详细文档**：
- 安装指南
- 功能文档
- 开发文档
- 归档文档

**优势**：
- ✅ 文档集中
- ✅ 层次清晰
- ✅ 易于维护

---

## 📝 变更清单

### 移动的文件

#### Shell 脚本（根目录 → bin/）
- `quick_start.sh` → `bin/quick_start.sh`
- `fast_start.sh` → `bin/fast_start.sh`
- `start_frontend.sh` → `bin/start_frontend.sh`
- `run_simulator.sh` → `bin/run_simulator.sh`
- `init_devices.sh` → `bin/init_devices.sh`
- `check_system.sh` → `bin/check_system.sh`

#### 文档（根目录 → docs/）
- `INSTALL.md` → `docs/INSTALL.md`
- `DOCKER_SCRIPTS.md` → `docs/DOCKER_SCRIPTS.md`

### 新增的文件
- `bin/README.md` - 脚本使用说明
- `FILE_ORGANIZATION.md` - 本文档

### 更新的文件
- `README.md` - 更新脚本路径引用
- `START_HERE.md` - 更新脚本和文档路径
- `docs/README.md` - 更新文档索引

---

## 🚀 使用指南

### 运行脚本的新方式

**方式1：从项目根目录**（推荐）
```bash
# 启动系统
./bin/fast_start.sh

# 运行模拟器
./bin/run_simulator.sh

# 检查系统
./bin/check_system.sh
```

**方式2：从 bin 目录**
```bash
cd bin
./fast_start.sh
```

**方式3：使用绝对路径**
```bash
/path/to/MineEnergySystem/bin/fast_start.sh
```

### 查看文档的新方式

```bash
# 安装指南
cat docs/INSTALL.md

# Docker 脚本说明
cat docs/DOCKER_SCRIPTS.md

# 脚本使用说明
cat bin/README.md
```

---

## 🔄 向后兼容

为了保持兼容性，我们可以考虑创建符号链接：

```bash
# 在根目录创建快捷方式（可选）
ln -s bin/fast_start.sh fast_start.sh
ln -s docs/INSTALL.md INSTALL.md
```

**但不推荐这样做**，建议直接适应新结构。

---

## 📚 文档索引

### 根目录文档
- [README.md](./README.md) - 完整项目说明
- [START_HERE.md](./START_HERE.md) - 3分钟快速上手
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) - 详细项目结构

### bin/ 脚本
- [bin/README.md](./bin/README.md) - 脚本使用说明

### docs/ 文档
- [docs/README.md](./docs/README.md) - 文档导航
- [docs/INSTALL.md](./docs/INSTALL.md) - 安装指南
- [docs/DOCKER_SCRIPTS.md](./docs/DOCKER_SCRIPTS.md) - Docker 脚本
- [docs/快速启动指南.md](./docs/快速启动指南.md) - 详细启动教程
- [docs/LSTM完整使用指南.md](./docs/LSTM完整使用指南.md) - AI 预测功能

---

## ✅ 整理效果

### 根目录清爽度对比

| 项目 | 整理前 | 整理后 | 改善 |
|------|--------|--------|------|
| MD 文档 | 5个 | 3个 | ⬇️ 40% |
| Shell 脚本 | 6个 | 0个 | ⬇️ 100% |
| 总文件数 | 11个 | 3个 | ⬇️ 73% |

### 优势总结

✅ **可维护性** - 文件分类清晰，易于管理  
✅ **可发现性** - 按用途组织，易于查找  
✅ **专业性** - 结构清晰，符合开源项目规范  
✅ **扩展性** - 新增文件有明确的位置  

---

## 🔮 未来规划

可能的进一步优化：

1. **tools/** 目录
   - 存放开发工具脚本
   - 如：数据库迁移、代码生成等

2. **config/** 目录增强
   - 集中所有配置文件
   - 按环境分类（dev, prod）

3. **tests/** 目录
   - 单元测试
   - 集成测试
   - 端到端测试

---

**📌 提示**: 所有文档中的路径引用已更新，可以放心使用！

**🆘 问题反馈**: 如果发现路径错误或文档问题，请及时反馈。
