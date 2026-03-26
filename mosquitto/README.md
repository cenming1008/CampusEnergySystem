# mosquitto 目录说明

`mosquitto/` 用来承载项目内置 MQTT Broker 的本地挂载目录。

## 目录职责

- `config/`：Mosquitto 配置文件
- `data/`：Broker 运行时数据目录
- `log/`：Broker 日志目录

## 当前文件

- [mosquitto.conf](/Users/todo/MineEnergySystem/mosquitto/config/mosquitto.conf)：Broker 配置，监听 `1883`，已启用认证（`allow_anonymous false`）
- `config/passwd`：密码文件（由 `scripts/shell/setup_mqtt_auth.sh` 生成，不提交到 Git）

## 认证说明

Mosquitto 已配置为需要用户名/密码认证：

1. 首次部署需生成 passwd 文件：`bash scripts/shell/setup_mqtt_auth.sh`
2. 默认凭证通过 `MQTT_USERNAME` / `MQTT_PASSWORD` 环境变量管理
3. Docker Compose 中 backend 服务会自动从环境变量读取凭证连接 Broker

## 与 Docker 的关系

这些目录会被 Docker Compose 挂载到容器中：

- [docker-compose.yml](/Users/todo/MineEnergySystem/docker-compose.yml)
- [docker-compose.dev.yml](/Users/todo/MineEnergySystem/docker-compose.dev.yml)
- [docker-compose.prod.yml](/Users/todo/MineEnergySystem/docker-compose.prod.yml)

## 使用建议

- 改 MQTT 服务配置：编辑 `config/mosquitto.conf`
- `data/` 和 `log/` 属于运行产物，不提交到 Git
- `config/passwd` 是运行时密码文件，通过 `.gitignore` 排除
