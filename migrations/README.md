# Database Migrations

本目录用于管理园区综合能源管理系统的正式数据库迁移。数据库 schema 仅由
Alembic 管理；应用启动负责校验 migration 结果，不创建表、不补字段或索引，
也不负责转换 TimescaleDB hypertable。

## 当前迁移基线

- 当前活跃根 revision：`20260716_0001`，`down_revision = None`。
- `migrations/versions/` 只保留当前活跃迁移链。
- 旧 revision `20260325_0001` 至 `20260515_0011` 已退出活跃链，只允许在
  `docs/archive/migrations/legacy-pre-20260716` 中追溯，不得作为新库或现有库的
  stamp 目标。

## 启动配置契约

所有环境都必须使用：

```text
DB_AUTO_CREATE_TABLES=False
DB_RUNTIME_SCHEMA_SYNC=False
```

这两个字段只为兼容旧配置而保留。任一字段配置为 `True` 都会被严格启动检查
和数据库启动校验拒绝；不要用运行时自动建表或补 schema 替代 migration。

## 正常建库流程

设置目标新库的 `DATABASE_URL` 后执行：

```bash
alembic upgrade head
```

命令应从空库应用静态根 `20260716_0001`，创建完整业务 schema、TimescaleDB
扩展及 `energydata` hypertable。完成后应用启动只读取并校验结果。

不要用手工 stamp、应用 metadata 建表或人工补表绕过迁移。当前旧开发库的重建
属于后端可靠性阶段 2A 正式计划的 Task 8，必须在三个隔离临时路径全部验证通过
后按该计划执行；本文档不提供提前重建或手工 stamp 指南。

## 目录边界

| 路径 | 用途 |
| --- | --- |
| `env.py` | Alembic online / offline 运行入口 |
| `script.py.mako` | 新迁移文件模板 |
| `versions/` | 当前活跃迁移链；现阶段根为 `20260716_0001` |
| `docs/archive/migrations/legacy-pre-20260716` | 旧链只读追溯材料，不参与 Alembic 加载 |

## 维护原则

- 新 schema 变化必须新增 Alembic revision，并正确连接当前 `head`。
- 不随意改动已验收 revision 的 ID、`down_revision` 或迁移文件名。
- migration 必须同时支持 online 执行与 offline SQL 生成。
- 不把本地缓存、数据库运行目录或其他生成物放入本目录。
- 不允许应用启动行为掩盖 migration 缺口。
