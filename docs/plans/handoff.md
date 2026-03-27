# Handoff

## 探索 -> 前端
### 任务
- 已完成：停止把 `scripts/shell/start_frontend.sh` 作为正式入口维护
- 已完成：前端启动统一回到 `frontend/package.json#dev`
- 已完成：`bin/fast_start.sh`、`bin/fast_start_dev.sh` 前端提示已按当前 Vite 配置校对

### 已知信息
- 当前脚本规范要求：前端原生命令优先留在 `frontend/package.json`
- `scripts/shell/start_frontend.sh` 已迁入 `scripts/archive/shell/start_frontend.sh`
- `bin/fast_start.sh` 已改为直接执行 `(cd frontend && npm run dev)`
- 当前 `frontend/vite.config.ts` 默认端口为 `3000`，但根级 `README.md` 与部分开发文档仍写 `5173`

### 建议处理方式
- 前端脚本层已完成收敛，后续优先补根级 README 与开发文档中的前端端口和命令表述
- 若确认无人依赖归档脚本，可再评估是否彻底删除 `scripts/archive/shell/start_frontend.sh`

---

## 探索 -> 后端
### 任务
- 校正 shell 正式脚本与当前后端环境的一致性
- 确认删除候选与归档候选脚本是否还有实际使用者

### 已知信息
- `scripts/shell/status.sh` 目前只覆盖默认 compose 容器名，不覆盖 dev/prod 三套环境
- `scripts/python/rebuild_database.py` 仍保留旧“全新系统删表重建”语义，与当前 Alembic 流程冲突
- `release_readiness.sh`、`pilot_*`、`test_health.sh`、`replay_mqtt_failures.py`、`send_test_alert.py` 仍与当前后端链路相关，属于高优先复核对象

### 建议处理方式
- 先复核高价值正式脚本，再处理归档和删除候选
- 不要直接删脚本；若确认失效，先从文档和清单中降级，再转入归档或删除候选区

---

## 前端 -> 后端
### 当前建议
- 本轮无需后端改代码
- 后续若后端同步更新本地联调文档，请统一采用前端默认地址 `http://localhost:3000`

---

## 后端 -> 前端
### 当前建议
- 本轮仅整理后端脚本与后端文档入口，未改接口契约，前端无需联调
- 若前端后续补根级 README 或排查文档，可沿用新的 `status.sh [auto|default|dev|prod]` 用法与 `python -m alembic upgrade head` 叙事

---

## 后续维护建议

- 正式入口优先收敛到：
  - `frontend/package.json`
  - `bin/`
  - `scripts/shell/`
  - `scripts/python/`
- `demo_*`、`serial_*`、单次接入调试脚本不要继续放在“主入口”叙事里
- 处理删除候选前，必须先确认 README、`scripts/README.md`、`scripts/SCRIPT_LIST.md`、`scripts/QUICK_REFERENCE.md` 是否还在引用
- 新增脚本前继续遵循 `docs/guides/script-guidelines.md`
