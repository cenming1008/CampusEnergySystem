# mosquitto 目录说明

`mosquitto/` 用来承载项目内置 MQTT Broker 的本地挂载目录。

## 目录职责

- `config/`：Mosquitto 配置文件
- `data/`：Broker 运行时数据目录
- `log/`：Broker 日志目录

## 当前文件

- [mosquitto.conf](/Users/todo/MineEnergySystem/mosquitto/config/mosquitto.conf)：当前基础配置，默认监听 `1883`，允许匿名访问

## 与 Docker 的关系

这些目录会被 Docker Compose 挂载到容器中：

- [docker-compose.yml](/Users/todo/MineEnergySystem/docker-compose.yml)
- [docker-compose.dev.yml](/Users/todo/MineEnergySystem/docker-compose.dev.yml)
- [docker-compose.prod.yml](/Users/todo/MineEnergySystem/docker-compose.prod.yml)

## 使用建议

- 改 MQTT 服务配置：编辑 `config/mosquitto.conf`
- `data/` 和 `log/` 属于运行产物，不提交到 Git
- 如果后面启用认证，可以继续在 `config/` 下增加 `passwd`、`acl` 等文件
