# Handoff

## 探索 -> 前端
### 任务
- 决定 `scripts/shell/start_frontend.sh` 是否继续维护
- 如果要收敛前端启动入口，统一以 `frontend/package.json#dev` 为正式入口
- 校对 `bin/fast_start.sh`、`bin/fast_start_dev.sh` 中前端启动与端口提示

### 已知信息
- 当前脚本规范要求：前端原生命令优先留在 `frontend/package.json`
- `scripts/shell/start_frontend.sh` 仍有内容价值，但和 `npm run dev` 明显重复
- `README.md`、`scripts/QUICK_REFERENCE.md`、部分新手文档仍同时提到脚本启动和 package script 启动

### 建议处理方式
- 先改文档入口层级，再决定是否保留包装脚本
- 若保留 `start_frontend.sh`，应把它明确降级为“辅助包装脚本”，不要继续和 `npm run dev` 并列为正式入口

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
- 若前端最终收敛到 `frontend/package.json#dev`，后端需要同步确认快捷脚本中的联动提示是否仍合理
- 若 `bin/fast_start_dev.sh` 继续保留，后端本地启动与健康检查逻辑需要继续可用

---

## 后端 -> 前端
### 当前建议
- 若后端调整 `status.sh`、`test_health.sh` 或试点脚本的环境识别逻辑，前端无需改业务代码，但需要同步修正文档中的启动与排查命令

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
