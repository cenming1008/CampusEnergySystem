# pg_data_dev 目录说明

`pg_data_dev/` 是开发环境 Docker Compose 使用的 PostgreSQL 数据目录。

## 用途

- [docker-compose.dev.yml](/Users/todo/MineEnergySystem/docker-compose.dev.yml)

会把这个目录挂载到开发数据库容器的 `/var/lib/postgresql/data`。

## 注意事项

- 这里存放的是开发环境数据库文件
- 不应提交到 Git
- 可以在确认无重要数据时重建
- 不建议手动改内部文件

更详细说明见：
- [DATABASE_STORAGE.md](/Users/todo/MineEnergySystem/docs/03-开发与部署/DATABASE_STORAGE.md)
