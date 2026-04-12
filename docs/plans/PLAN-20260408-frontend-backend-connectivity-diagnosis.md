# PLAN-20260408-frontend-backend-connectivity-diagnosis

> 状态：最小修复完成，待验收 | 负责人：预判 / 后端角色 | 更新时间：2026-04-08

---

## 背景

项目当前主区此前处于“待锁定下一个主主题”状态。用户反馈“项目启动之后前后端连不上”，并怀疑可能是后端 Docker 调整后，前端没有同步修改。

本轮已核对：

- `docker-compose.yml`
- `docker-compose.dev.yml`
- `scripts/shell/start_dev_env.sh`
- `bin/fast_start_dev.sh`
- `frontend/vite.config.ts`
- `frontend/src/utils/request.ts`
- `run.py`
- 当前本机 Docker 容器状态
- 本地 `http://127.0.0.1:8088` 健康检查与登录接口最小验证

---

## 目标

- 明确当前“前后端连不上”断在 Docker、后端运行、前端代理，还是接口契约层。
- 锁定是否属于“后端改了 Docker，但前端未同步”问题。
- 为后续前端角色 / 后端角色 / 验收角色提供最小交接依据。

## 非目标

- 本轮不直接重构 Docker 编排。
- 不顺手修改前端请求封装或 Vite 代理。
- 不顺手改后端接口契约、字段返回或鉴权逻辑。
- 不处理 MQTT worker 独立运行带来的更深层运行时设计问题。

## 范围

- 启动链路：`docker-compose.yml`、`docker-compose.dev.yml`、`scripts/shell/start_dev_env.sh`、`bin/fast_start_dev.sh`
- 前端接口消费：`frontend/vite.config.ts`、`frontend/src/utils/request.ts`
- 后端本地入口：`run.py`
- 运行态验证：本机 Docker 容器与 `127.0.0.1:8088`

## 关键结论

1. 当前机器上只运行了开发环境中间件容器：
   - `campus_energy_db_dev`
   - `campus_redis_dev`
   - `campus_mqtt_dev`
   - 没有运行中的 `campus_backend` 或本地 8088 监听进程
2. 前端当前仍然通过相对路径请求 API：
   - `frontend/src/utils/request.ts` 中 `axios.create({ baseURL: '' })`
   - `frontend/vite.config.ts` 把 `/auth`、`/devices`、`/health`、`/ws` 等代理到 `http://127.0.0.1:8088`
3. `docker-compose.dev.yml` 已不是“全栈启动”模式：
   - 它只负责数据库、Redis、MQTT
   - `scripts/shell/start_dev_env.sh` 也明确写明 Backend 和 Frontend 需要手动启动
4. 本地直接执行 `./venv/bin/python run.py` 后：
   - `http://127.0.0.1:8088/health/live` 正常返回
   - `POST /auth/login` 可成功登录
   - 说明前端“连不上”不是因为前端代理地址写错，也不是后端接口主路由改坏
5. 因此当前最小根因判断为：
   - 运行模式已切到“开发中间件 Docker + 本地后端/前端”
   - 但实际只启动了开发中间件，没有启动本地 backend
   - 前端代理仍然指向 `127.0.0.1:8088`，于是自然全部请求失败
6. 当用户实际运行 `bin/fast_start_dev.sh` 时，又发现了更具体的脚本层根因：
   - `logs/backend_dev.log` 显示 `./bin/fast_start_dev.sh: line 53: python: command not found`
   - `logs/mqtt_ingest_worker_dev.log` 显示 `./bin/fast_start_dev.sh: line 79: python: command not found`
   - 说明脚本虽然打印“后端将在后台运行”，但 backend / worker 实际没有成功启动
7. 已完成最小实现修复：
   - `bin/fast_start_dev.sh` 改为直接调用 `./venv/bin/python`
   - backend 等待超时后会直接退出并报错，不再伪装成“开发环境已启动”

## 实施步骤

### 1. 预判角色

- [x] 核对 Docker 编排、前端代理和后端入口
- [x] 用最小运行验证确认 `run.py` 可正常提供 8088 服务
- [x] 判断根因是否属于接口契约失配

### 2. 规则角色

- [ ] 决定本专题是否继续作为独立主主题推进
- [ ] 决定默认开发入口是否统一收口到 `bin/fast_start_dev.sh`

### 3. 前端 / 后端角色（如继续）

- [x] 已修复 `bin/fast_start_dev.sh` 对 `python` 命令的脆弱依赖
- [x] 已补充 backend 启动失败时的显式退出
- [ ] 若要进一步降低误用风险，补齐启动入口提示或开发态联调说明

### 4. 验收角色

- [ ] 验证“重新运行 `bin/fast_start_dev.sh` 后，前端不再出现 `ECONNREFUSED 127.0.0.1:8088`”
- [ ] 验证登录后 WebSocket 可正常握手
- [ ] 判断本专题是否阶段收口

## 风险与回滚

- 风险：若继续沿用 `start_dev_env.sh` 但用户预期它会启动完整开发栈，仍会重复出现“前端连不上”的误判。
- 风险：当前 `/health` 会因为 `mqtt_worker` 未运行而返回 `unhealthy`，但这不等于 HTTP API 不可访问，排查时容易混淆。
- 风险：WebSocket 在未登录或 token 失效时仍会握手失败；这与本轮脚本问题不同，验收时需要分开判断。
- 回滚边界：本轮仅修改本地开发入口脚本，无接口契约和业务代码回滚需求。

## 验收标准

- 已明确当前断点不在前端代理地址修改，而在后端 8088 实例未启动。
- 已明确 `docker-compose.dev.yml` 只负责中间件，不自动提供 backend。
- 已通过本地最小验证证明 `python run.py` 后前端依赖的 HTTP 主链路可访问。
- 已明确 `bin/fast_start_dev.sh` 旧版本会因 `python: command not found` 导致 backend / worker 实际未启动。
- 已完成 `bin/fast_start_dev.sh` 的最小修复，使其直接使用 `./venv/bin/python`。
- 已把结论写回主区文档，供后续线程直接接棒。

## 进度记录

- `2026-04-08`：预判角色完成运行态核对与最小验证，结论为“开发编排模式切换后，仅启动了中间件，未启动本地 backend；前端无需为接口地址做额外修正”。
- `2026-04-08`：用户补充“已运行 `fast_start_dev` 但仍然 WebSocket 失败”；进一步定位到 `bin/fast_start_dev.sh` 使用 `python` 启动 backend / worker，实际日志报 `python: command not found`。已改为直接使用 `./venv/bin/python`，并在 backend 未就绪时显式退出。
