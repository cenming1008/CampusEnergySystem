# 📚 文档导航

欢迎来到煤矿综合能源管理系统文档中心！

---

## 🚀 快速开始

### 我是新用户，想快速上手
👉 **直接阅读项目根目录的 [`README.md`](../README.md)**

推荐阅读顺序：
1. **项目简介** → 了解系统功能
2. **快速开始** → 一键启动系统
3. **API 文档** → 查看可用接口

### 我遇到问题了
👉 查看 [`README.md` - 故障排查章节](../README.md#-故障排查)

常见问题：
- 容器启动失败
- 数据库连接失败
- WebSocket 连接失败
- 启动速度慢

### 我想参与开发
👉 查看以下文档：
1. [`README.md` - 开发指南](../README.md#-开发指南)
2. [`app/README.md`](../app/README.md) - 代码结构说明

---

## 📖 主要文档

### [`README.md`](../README.md) ⭐ 主文档
**这是唯一需要阅读的文档！** 包含：
- ✅ 项目简介和功能特性
- ✅ 完整的技术栈说明
- ✅ 快速开始指南（一键启动）
- ✅ 系统架构和数据流向
- ✅ API 文档和使用示例
- ✅ 开发指南（添加新功能）
- ✅ 运维管理（部署、备份、监控）
- ✅ 故障排查（常见问题解决）
- ✅ 项目路线图（已完成和计划中）

**长度**: 约 600 行  
**结构**: 10 个主要章节  
**更新**: 持续维护，保持最新

---

## 📂 其他文档

### [`app/README.md`](../app/README.md)
**代码结构说明** - 开发者必读
- 后端代码目录结构
- 各层职责说明（API/Service/Core）
- 模块依赖关系

### [`docs/archive/`](archive/)
**归档文档** - 历史参考
- 包含项目早期的详细文档
- 不再更新，仅供参考
- 查看 [`README_ARCHIVE.md`](archive/README_ARCHIVE.md) 了解详情

### [`DOCS_CONSOLIDATION.md`](../DOCS_CONSOLIDATION.md)
**文档整合报告** - 了解文档演进
- 整合前后对比
- 整合效果和收益
- 维护策略说明

---

## 🎯 按场景查找

### 场景 1: 首次部署系统
```bash
# 阅读文档
1. README.md → 快速开始
2. README.md → 验证服务

# 执行命令
docker compose up -d --build
docker compose ps
curl http://localhost:8088/health
```

### 场景 2: 开发新功能
```bash
# 阅读文档
1. README.md → 开发指南
2. app/README.md → 代码结构
3. README.md → 系统架构

# 开发流程
1. 创建 Service 层
2. 创建 API 端点
3. 注册路由
4. 测试功能
```

### 场景 3: 排查故障
```bash
# 阅读文档
1. README.md → 故障排查

# 诊断命令
docker compose ps
docker compose logs backend
curl http://localhost:8088/health
```

### 场景 4: 生产部署
```bash
# 阅读文档
1. README.md → 运维管理 → 生产环境部署
2. README.md → 配置说明

# 部署步骤
1. 修改环境变量
2. 配置 Nginx
3. 启用 HTTPS
4. 配置防火墙
```

---

## 🔍 查找特定信息

| 想了解... | 查看文档 | 章节 |
|-----------|---------|------|
| 项目有哪些功能 | README.md | 功能特性 |
| 如何快速启动 | README.md | 快速开始 |
| 系统架构设计 | README.md | 系统架构 |
| API 接口列表 | README.md | API 文档 |
| 如何添加新功能 | README.md | 开发指南 |
| 如何部署到生产 | README.md | 运维管理 |
| 遇到问题怎么办 | README.md | 故障排查 |
| 项目后续计划 | README.md | 项目路线图 |
| 代码目录结构 | app/README.md | - |
| 历史详细文档 | docs/archive/ | 各归档文档 |

---

## 📝 文档维护

### 当前维护策略
- **主文档** (`README.md`) - 持续更新，保持最新
- **代码文档** (`app/README.md`) - 与代码同步更新
- **归档文档** (`docs/archive/`) - 不再更新，仅作参考

### 如何更新文档
1. 所有功能更新都在 `README.md` 中进行
2. 代码结构变化更新 `app/README.md`
3. 不要创建新的独立功能文档
4. 保持单一真实来源（Single Source of Truth）

---

## 💡 推荐阅读路径

### 路径 1: 快速上手（15 分钟）
```
README.md
├─ 项目简介 (3 分钟)
├─ 快速开始 (5 分钟)
└─ API 文档 (7 分钟)
```

### 路径 2: 深入了解（1 小时）
```
README.md
├─ 项目简介 (5 分钟)
├─ 技术栈 (10 分钟)
├─ 功能特性 (10 分钟)
├─ 系统架构 (20 分钟)
└─ 开发指南 (15 分钟)
```

### 路径 3: 全面掌握（2-3 小时）
```
README.md (完整阅读)
├─ 所有章节
└─ 实践操作

app/README.md
└─ 代码结构

docs/archive/
└─ 感兴趣的归档文档
```

---

## ❓ 常见问题

### Q: 为什么只有一个主文档？
**A**: 我们整合了所有文档到 `README.md`，提升可维护性和用户体验。旧文档已归档到 `docs/archive/`。

### Q: 归档文档还有用吗？
**A**: 有用！它们包含详细的历史信息和实现细节，可作为深入参考。但优先阅读 `README.md`。

### Q: 如何找到某个功能的详细信息？
**A**: 
1. 先在 `README.md` 中查找
2. 如需更多细节，查看 `docs/archive/` 中的归档文档
3. 如需代码级信息，查看 `app/README.md` 和代码注释

### Q: 我想贡献文档，应该修改哪个文件？
**A**: 直接修改 `README.md` 相应章节。如果是代码结构变化，更新 `app/README.md`。

---

## 🔗 相关链接

### 在线文档
- **API 文档** (Swagger): http://localhost:8088/docs
- **API 文档** (ReDoc): http://localhost:8088/redoc

### 项目链接
- **GitHub**: https://github.com/your-repo/MineEnergySystem
- **问题反馈**: https://github.com/your-repo/MineEnergySystem/issues

### 外部资源
- [FastAPI 官方文档](https://fastapi.tiangolo.com)
- [Vue3 官方文档](https://vuejs.org)
- [TimescaleDB 文档](https://docs.timescale.com)
- [Docker 文档](https://docs.docker.com)

---

## 📞 获取帮助

### 文档问题
如果文档不清楚或有错误：
1. 提交 Issue: https://github.com/your-repo/MineEnergySystem/issues
2. 或直接修改后提交 Pull Request

### 技术问题
遇到技术问题：
1. 先查看 [`README.md` - 故障排查](../README.md#-故障排查)
2. 搜索已有 Issues
3. 提交新 Issue 并附上详细信息

---

**最后更新**: 2026-01-12  
**维护者**: 项目团队  
**版本**: v2.0.0

---

**祝你使用愉快！** 🚀
