# 计划目录

> `docs/plans/` 只保留当前执行层文档。当前态看主区，历史快照进 `daily/`，已完成且不再作为执行依据的主题进 `docs/archive/plans/`。

---

## 目录职责

本目录只承担“当前执行层”职责，适合放：

- 当前主主题的正式计划
- 当前主主题的状态面板
- 当前主主题的交接面板
- 当天结束后的状态快照与交接快照
- 计划模板

以下内容不应继续留在本目录主入口：

- 长期稳定规范
  - 放 `docs/guides/`
- 已完成且不再作为执行依据的计划、审计、迁移分析
  - 放 `docs/archive/plans/`
- 只剩追溯价值的旧状态块、旧交接块
  - 放 `docs/plans/daily/`

---

## 五类入口

### 1. 当前态入口

- [current-status.md](./current-status.md)

用途：

- 只维护当前主主题的状态、阻塞、待办、验证结论和风险

维护纪律：

- 任意时刻只服务一个当前主主题
- 不按日期堆日志
- 已完成或仅剩追溯价值的内容必须迁入 `daily/`

### 2. 当前交接入口

- [handoff.md](./handoff.md)

用途：

- 只维护当前主主题下仍有行动价值的交接

维护纪律：

- 任意时刻只服务一个当前主主题
- 只写下一步仍会执行的信息
- 不承担长期存史职责

### 3. 正式 PLAN

- `PLAN-YYYYMMDD-主题.md`

用途：

- 作为当前主题的正式执行依据
- 承担目标、非目标、范围、实施步骤、风险、验收标准和进度记录

硬规则：

- 复杂任务进入实现前，必须先有明确的 `PLAN-*.md` 或等价执行依据
- `current-status.md` 和 `handoff.md` 不能替代正式 PLAN
- 一个 PLAN 只服务一个明确主题

### 4. Daily 归档

- `daily/YYYY-MM/YYYY-MM-DD-status.md`
- `daily/YYYY-MM/YYYY-MM-DD-handoff.md`

用途：

- 保存某一天结束时的状态快照和交接快照
- 供按日期追溯

维护纪律：

- 每天任务结束后归档
- 归档后主区必须同步收轻
- `daily/` 负责保留历史，不替代正式 PLAN

### 5. Archive 归档

- `docs/archive/plans/*`

用途：

- 保存已完成且不再作为执行依据的主题计划、审计和专题分析

维护纪律：

- 只承担追溯职责
- 不再作为当前执行入口引用

---

## 当前态、PLAN、Daily 的区别

### `current-status.md`

- 回答“当前主题现在处于什么状态”
- 面向当前推进

### `handoff.md`

- 回答“当前主题下一步由谁做什么”
- 面向当前行动

### `PLAN-*.md`

- 回答“当前主题为什么做、做什么、不做什么、怎么验收”
- 面向主题级执行依据

### `daily/*.md`

- 回答“某一天结束时留下了什么状态和交接”
- 面向按日期追溯

### `docs/archive/plans/*`

- 回答“哪些主题已经完成，只保留历史价值”
- 面向长期归档

---

## 推荐工作流

1. 复杂任务先建立或确认正式 `PLAN-*.md`
2. 执行过程中只在主区维护当前主主题的最新状态与交接
3. 当天结束后，将状态和交接快照归档到 `daily/YYYY-MM/`
4. 归档后清理主区，只保留仍需继续推进的内容
5. 主题完成后，判断是否仍作为执行依据；若否，迁入 `docs/archive/plans/`

---

## 当前文件

- [TEMPLATE.md](./TEMPLATE.md)：计划模板
- [current-status.md](./current-status.md)：当前主主题状态面板
- [handoff.md](./handoff.md)：当前主主题交接面板
- `PLAN-*.md`：当前仍作为执行依据的正式计划
- `daily/YYYY-MM/YYYY-MM-DD-status.md`：每日状态快照
- `daily/YYYY-MM/YYYY-MM-DD-handoff.md`：每日交接快照

---

## 相关文档

- [变更计划规范](../guides/变更计划规范.md)
- [AI 多角色协作 SOP](../guides/ai-collaboration-sop.md)
- [CampusEnergySystem 五角色项目适配说明](../guides/five-role-vibe-coding-framework.md)
- [文档体系规范](../guides/文档体系规范.md)
- [docs 主目录](../README.md)
