# pg_data 目录说明

`pg_data/` 是默认/生产 Docker Compose 环境使用的 PostgreSQL 数据目录。

## 用途

- [docker-compose.yml](/Users/todo/MineEnergySystem/docker-compose.yml)
- [docker-compose.prod.yml](/Users/todo/MineEnergySystem/docker-compose.prod.yml)

都会把这个目录挂载到数据库容器的 `/var/lib/postgresql/data`。

## 注意事项

- 这里存放的是数据库真实数据文件
- 不应提交到 Git
- 不应手动编辑内部文件
- 如需清理或重建，请先确认是否需要备份

更详细说明见：
- [DATABASE_STORAGE.md](/Users/todo/MineEnergySystem/docs/03-开发与部署/DATABASE_STORAGE.md)
