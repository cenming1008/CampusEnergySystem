# Database Migrations

本目录用于管理 MineEnergySystem 的正式数据库迁移。

## 推荐流程

1. 开发环境允许 `DB_AUTO_CREATE_TABLES=True` 和 `DB_RUNTIME_SCHEMA_SYNC=True` 快速迭代。
2. 预发布/生产环境必须关闭这两个开关，并先执行 Alembic migration。
3. 已有旧库接入 migration 时，可先执行：

```bash
alembic stamp 20260325_0001
```

4. 新版本上线前执行：

```bash
alembic upgrade head
```

## 当前基线

- `20260325_0001`：补齐工业化改造新增的关键列和索引
