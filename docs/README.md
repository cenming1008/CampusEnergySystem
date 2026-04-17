# 文档中心

> 当前 `docs/` 只保留协作规则、执行主区、历史归档和技能流程产物，不再维护基础使用类说明书。

---

## 当前主入口

- 协作与规则：
  - [AGENTS.md](../AGENTS.md)
  - [规范指南](./guides/README.md)
  - [AI 多角色协作 SOP](./guides/ai-collaboration-sop.md)
  - [Codex 五角色 Vibe Coding 框架](./guides/five-role-vibe-coding-framework.md)
- 当前执行：
  - [计划目录](./plans/README.md)
  - [当前状态](./plans/current-status.md)
  - [当前交接](./plans/handoff.md)
- 历史追溯：
  - [归档区](./archive/README.md)

---

## 当前目录结构

```text
docs/
├── guides/                    ← 长期稳定规范与协作规则
├── plans/                     ← 当前主题计划、状态、交接、daily 快照
└── archive/                   ← 极简归档占位目录
```

---

## 使用顺序

### 我要推进当前主题

1. [AGENTS.md](../AGENTS.md)
2. [current-status.md](./plans/current-status.md)
3. [handoff.md](./plans/handoff.md)
4. 当前主题对应 `PLAN-*.md`
5. 再回到对应 guide

### 我要查规则和边界

- [guides/README.md](./guides/README.md)
- [product-positioning.md](./guides/product-positioning.md)
- [frontend-guidelines.md](./guides/frontend-guidelines.md)
- [backend-guidelines.md](./guides/backend-guidelines.md)
- [script-guidelines.md](./guides/script-guidelines.md)

### 我要追历史

- [archive/README.md](./archive/README.md)
- `docs/archive/plans/`
- `docs/plans/daily/`

---

## 清理口径

- `docs/01-新手入门/`、`docs/02-功能使用/`、`docs/03-开发与部署/` 已整体下线，不再作为仓库正式文档层维护。
- 若后续需要启动、部署、接入或使用类说明，按当时实际需求由 AI 重新补写，不默认恢复旧目录。
- `current-status.md` 和 `handoff.md` 主区任意时刻只服务一个当前主主题。
- 已完成专题、旧分析、一次性修复记录统一进入 `archive/`。

---

## 维护建议

清理或新增文档时，至少同步检查：

1. `docs/README.md` 是否仍可导航
2. `docs/guides/` 是否仍与当前目录结构一致
3. `docs/plans/README.md` 是否仍符合主区 / daily / archive 分层
4. 是否误把一次性操作说明重新抬回主入口
