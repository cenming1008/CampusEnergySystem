# 文档索引

## 📚 主要文档

### ⚡ 快速开始（新手必读）
- **[快速启动指南.md](./快速启动指南.md)** ⭐ **首次使用必读**
  - 3 分钟快速启动系统
  - Docker 一键启动教程
  - 本地开发环境配置
  - 启动问题排查
  - 常用管理命令

### 📦 安装和配置
- **[INSTALL.md](./INSTALL.md)** - 完整安装指南（Docker + 本地开发）⭐
- **[installation_guide.md](./installation_guide.md)** - Python环境安装和依赖管理
- **[fix_venv_issue.md](./fix_venv_issue.md)** - 虚拟环境问题修复指南

### 🚀 LSTM预测功能
- **[LSTM完整使用指南.md](./LSTM完整使用指南.md)** ⭐ **AI功能必读**
  - 从入门到高级的完整LSTM使用指南
  - 包含环境准备、数据准备、模型训练、使用、高级功能等所有内容
  - 适合所有用户，从新手到高级用户

### 📊 功能指南
- **[forecast_guide.md](./forecast_guide.md)** - 预测功能总体指南（包含简单算法和LSTM）
- **[DOCKER_SCRIPTS.md](./DOCKER_SCRIPTS.md)** - Docker 脚本完整使用指南 🐳
- **[GIT_IGNORE_GUIDE.md](./GIT_IGNORE_GUIDE.md)** - Git 文件管理指南

## 📁 文档归档

旧的LSTM相关文档已归档到 `archive/lstm_docs/` 目录，内容已整合到 [LSTM完整使用指南.md](./LSTM完整使用指南.md) 中：

- `lstm_forecast_guide.md` - 基础LSTM使用指南（已整合）
- `lstm_advanced_features.md` - 高级功能指南（已整合）
- `lstm_implementation_summary.md` - 实现总结（已整合）
- `quick_start_training.md` - 快速开始指南（已整合）
- `data_generation_guide.md` - 数据生成指南（已整合）

## 🎯 快速导航

### 🆕 首次使用（零基础）
1. **阅读** [快速启动指南.md](./快速启动指南.md) - 一键启动系统 ⭐
2. **验证** 访问 http://localhost:8088/docs 确认启动成功
3. **登录** 使用默认账号 admin/123456 测试 API
4. **运行** 设备模拟器生成测试数据

### 🔧 开发环境配置
1. 查看 [快速启动指南.md](./快速启动指南.md) 的"本地开发模式"
2. 阅读 [installation_guide.md](./installation_guide.md) 安装 Python 依赖
3. 查看 [../INSTALL.md](../INSTALL.md) 了解完整安装流程

### 🤖 使用 LSTM 预测功能
1. 确保系统已启动（参考快速启动指南）
2. 阅读 [LSTM完整使用指南.md](./LSTM完整使用指南.md) 的"快速开始"部分
3. 按照指南生成训练数据
4. 训练第一个 LSTM 模型
5. 使用模型进行预测

### 📈 进阶使用
1. 阅读 [LSTM完整使用指南.md](./LSTM完整使用指南.md) 的"高级功能"部分
2. 学习模型版本管理和性能对比
3. 掌握超参数优化技巧
4. 配置定时训练任务

### 🔍 故障排查
1. **启动问题**: 查看 [快速启动指南.md](./快速启动指南.md) 的"启动问题排查"
2. **虚拟环境**: 查看 [fix_venv_issue.md](./fix_venv_issue.md) 解决 Python 环境问题
3. **LSTM 功能**: 查看 [LSTM完整使用指南.md](./LSTM完整使用指南.md) 的"故障排查"部分
4. **通用问题**: 查看 [../README.md](../README.md) 的"故障排查"章节

## ⚡ 快速命令参考

```bash
# 快速启动系统（推荐）
./quick_start.sh

# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 停止服务
docker compose down

# 访问 API 文档
open http://localhost:8088/docs
```

## 📝 文档更新

- **最后更新**: 2026-01-13
- **主要变更**: 
  - 新增 [快速启动指南.md](./快速启动指南.md) - 3分钟快速上手 ⭐
  - 更新安装文档，增加 Docker 快速启动方式
  - 整合所有 LSTM 相关文档为一个完整指南
  - 优化文档索引和导航结构
