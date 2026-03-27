# 数据库存储目录说明

本文档说明项目中数据库数据存储目录的用途和区别。

## 📁 目录概览

```
/Users/todo/MineEnergySystem/
├── pg_data/        # 生产环境 PostgreSQL 数据目录
├── pg_data_dev/    # 开发环境 PostgreSQL 数据目录
└── backups/        # 数据库备份目录（可选）
```

## 🔍 详细说明

### 1. pg_data/ - 生产环境数据库

**用途**：存储生产环境的 PostgreSQL/TimescaleDB 数据库文件

**使用场景**：
- ✅ 生产部署（`docker-compose.prod.yml`）
- ✅ 默认部署（`docker-compose.yml`）

**Docker 配置**：

```yaml
# docker-compose.yml 和 docker-compose.prod.yml
services:
  db:
    volumes:
      - ./pg_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # 生产环境使用 5433 端口
```

**特点**：
- 🔒 生产环境使用，数据重要
- 💾 需要定期备份
- 🚫 不应该提交到 Git
- 🔐 包含真实业务数据

### 2. pg_data_dev/ - 开发环境数据库

**用途**：存储开发环境的 PostgreSQL/TimescaleDB 数据库文件

**使用场景**：
- ✅ 本地开发（`docker-compose.dev.yml`）
- ✅ 测试和调试
- ✅ 开发人员个人环境

**Docker 配置**：

```yaml
# docker-compose.dev.yml
services:
  db:
    container_name: mine_energy_db_dev
    volumes:
      - ./pg_data_dev:/var/lib/postgresql/data
    ports:
      - "5432:5432"  # 开发环境使用标准 5432 端口
```

**特点**：
- 🔧 开发环境使用，可以随意重置
- 🧪 用于测试新功能
- 🚫 不应该提交到 Git
- 🔄 可以随时删除重建

## 🔀 主要区别

| 特性 | pg_data（生产） | pg_data_dev（开发） |
|------|----------------|-------------------|
| **用途** | 生产环境 | 开发/测试环境 |
| **Docker Compose** | `docker-compose.yml`<br>`docker-compose.prod.yml` | `docker-compose.dev.yml` |
| **端口映射** | 5433（避免冲突） | 5432（标准端口） |
| **容器名称** | `mine_energy_db_prod` | `mine_energy_db_dev` |
| **数据重要性** | ⚠️ 重要，需备份 | 📝 可随时重建 |
| **大小** | ~72MB | ~75MB |
| **Git 管理** | ❌ 已忽略 | ❌ 已忽略 |
| **可以删除** | ❌ 慎重！ | ✅ 可以随意删除 |

## 🚀 使用指南

### 启动开发环境

```bash
# 使用开发环境配置（pg_data_dev）
docker-compose -f docker-compose.dev.yml up -d

# 本地运行后端（连接到 localhost:5432）
python run.py
```

### 启动生产环境

```bash
# 使用生产环境配置（pg_data）
docker-compose -f docker-compose.prod.yml up -d

# 或使用默认配置
docker-compose up -d
```

### 环境切换

如果需要在开发和生产环境之间切换：

```bash
# 停止当前环境
docker-compose down  # 或 docker-compose -f docker-compose.dev.yml down

# 启动目标环境
docker-compose -f docker-compose.dev.yml up -d  # 开发
# 或
docker-compose -f docker-compose.prod.yml up -d  # 生产
```

## 🔧 数据管理

### 重置开发环境数据库

如果开发环境数据混乱，可以安全地删除重建：

```bash
# 1. 停止容器
docker-compose -f docker-compose.dev.yml down

# 2. 删除开发数据（安全操作）
rm -rf pg_data_dev/

# 3. 重新启动（会自动初始化）
docker-compose -f docker-compose.dev.yml up -d

# 4. 重新初始化数据
python scripts/python/init_complete_system.py
```

### 备份生产数据库

⚠️ **重要**：生产数据需要定期备份！

```bash
# 使用备份脚本
bash scripts/shell/backup.sh

# 或手动备份
docker exec mine_energy_db_prod pg_dump -U admin mine_energy > backup.sql

# 备份整个数据目录
tar -czf pg_data_backup_$(date +%Y%m%d).tar.gz pg_data/
```

### 恢复数据库

```bash
# 从 SQL 文件恢复
cat backup.sql | docker exec -i mine_energy_db_prod psql -U admin -d mine_energy

# 使用恢复脚本
bash scripts/shell/restore.sh backup.sql
```

## ⚠️ 重要注意事项

### 1. Git 版本控制

这两个目录都已在 `.gitignore` 中：

```gitignore
# PostgreSQL/TimescaleDB 数据目录（包含实际数据）
pg_data/          # 生产环境数据库数据
pg_data_dev/      # 开发环境数据库数据
```

**原因**：
- 📦 数据文件通常很大（几十 MB 到几 GB）
- 🔐 可能包含敏感信息
- 🔄 每次数据变更都会产生大量 Git diff
- 🚫 不同环境应该有独立的数据

### 2. 端口冲突

**开发环境**（pg_data_dev）：
- 使用标准端口 `5432`
- 方便本地工具连接（如 pgAdmin、DBeaver）

**生产环境**（pg_data）：
- 使用端口 `5433`
- 避免与开发环境冲突
- 可以在同一机器上同时运行两个环境

### 3. 数据隔离

两个目录的数据是**完全独立**的：
- 修改 `pg_data_dev` 不会影响 `pg_data`
- 可以在开发环境测试破坏性操作
- 生产数据始终保持安全

### 4. 磁盘空间

数据库数据会随着使用增长：
- 定期清理旧数据（使用数据清理功能）
- 监控磁盘使用情况
- 考虑设置数据保留策略

## 🔍 故障排查

### 问题1：端口已被占用

```bash
# 错误：port is already allocated
# 解决：停止冲突的容器
docker ps | grep postgres
docker stop <container_id>
```

### 问题2：数据库连接失败

```bash
# 检查容器状态
docker ps | grep db

# 查看数据库日志
docker logs mine_energy_db_dev  # 开发环境
docker logs mine_energy_db_prod # 生产环境

# 检查数据库是否就绪
docker exec mine_energy_db_dev pg_isready -U admin
```

### 问题3：数据目录权限问题

```bash
# 在 macOS/Linux 上，确保目录权限正确
chmod 700 pg_data/
chmod 700 pg_data_dev/

# 如果容器启动失败，查看权限
ls -la pg_data*/
```

### 问题4：数据损坏

**开发环境**（可以安全删除）：
```bash
docker-compose -f docker-compose.dev.yml down -v
rm -rf pg_data_dev/
docker-compose -f docker-compose.dev.yml up -d
```

**生产环境**（需谨慎处理）：
```bash
# 1. 先尝试从备份恢复
bash scripts/shell/restore.sh latest_backup.sql

# 2. 如果无法恢复，联系管理员
# 3. 最后手段：重建（会丢失数据！）
```

## 📊 监控数据库大小

```bash
# 查看数据目录大小
du -sh pg_data pg_data_dev

# 进入数据库查看表大小
docker exec -it mine_energy_db_dev psql -U admin -d mine_energy

# 在 psql 中执行
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🎯 最佳实践

### 开发环境

1. ✅ 定期重置数据（避免累积垃圾数据）
2. ✅ 使用测试数据而不是生产数据
3. ✅ 可以随意实验，不用担心数据损坏
4. ✅ 使用 `init_complete_system.py` 初始化标准测试数据

### 生产环境

1. ✅ 定期备份（每天至少一次）
2. ✅ 监控磁盘空间
3. ✅ 设置数据保留策略（自动清理旧数据）
4. ✅ 永远不要直接删除 `pg_data/` 目录
5. ✅ 升级前先备份

### 团队协作

1. ✅ 每个开发者使用自己的 `pg_data_dev`
2. ✅ 不要共享数据库数据文件
3. ✅ 使用初始化脚本创建一致的开发环境
4. ✅ 文档化数据库变更（迁移脚本）

## 📚 相关文档

- [快速启动指南](../01-新手入门/快速启动指南.md)
- [本地开发环境配置](../01-新手入门/本地开发环境配置.md)
- [Docker 脚本说明](./DOCKER_SCRIPTS.md)
- [数据清理与保留策略](../02-功能使用/数据清理与保留策略.md)
- [备份脚本](../../scripts/shell/backup.sh)
- [恢复脚本](../../scripts/shell/restore.sh)

## 🔗 外部资源

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [TimescaleDB 文档](https://docs.timescale.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)

---

**创建日期**: 2026-01-24  
**最后更新**: 2026-01-24  
**维护者**: MineEnergySystem Team
