# 计划目录

> `docs/plans/` 采用“当前态 + 每日归档”模式：主入口只保留当前执行层文档；每日结束后的状态和交接快照沉淀到 `docs/plans/daily/`；已完成且不再作为执行依据的主题文档应迁入 `docs/archive/plans/`。

---

## 本目录放什么

适合放入本目录的内容：

- 具体需求或重构的实施计划
- 跨模块改动的阶段拆分
- 有明确风险、边界、验收标准的改动方案
- 需要多人或智能体协作的执行文档
- 当前状态面板与当前交接面板
- 每日状态快照与每日交接快照

不适合放入本目录的内容：

- 长期稳定规范 → 放 `docs/guides/`
- 已完成且不再作为执行依据的计划 / 审计 / 迁移分析 → 放 `docs/archive/plans/`
- 功能说明和操作手册 → 放既有主题目录
- 已合并到正式 PLAN 的探索输入 → 优先归档旧输入文档，而不是继续并列堆在 `plans/`
- 不再具有当前行动价值、只剩追溯用途的旧状态块 / 旧交接块 → 放 `docs/plans/daily/`

---

## 文件约定

- 计划文件命名：`PLAN-YYYYMMDD-主题.md`
- 模板文件命名：`TEMPLATE.md`
- 每日状态命名：`daily/YYYY-MM/YYYY-MM-DD-status.md`
- 每日交接命名：`daily/YYYY-MM/YYYY-MM-DD-handoff.md`
- 一个计划只服务一个明确目标，避免混装多个独立事项
- `current-status.md` 只维护“当前阶段正在执行的主主题、状态、风险和验证结论”
- `handoff.md` 只维护“当前阶段线程间仍需交接的执行信息与约束”
- 任意时刻，`current-status.md` 和 `handoff.md` 主区只允许服务一个当前主主题

---

## 四类入口职责

`docs/plans/` 默认只保留以下四类入口：

1. 当前计划入口
   - 正在执行、仍会继续作为实施依据的 `PLAN-*.md`
2. 当前状态入口
   - [current-status.md](./current-status.md)
3. 当前交接入口
   - [handoff.md](./handoff.md)
4. 每日归档入口
   - `daily/YYYY-MM/YYYY-MM-DD-status.md`
   - `daily/YYYY-MM/YYYY-MM-DD-handoff.md`
5. 模板入口
   - [TEMPLATE.md](./TEMPLATE.md)

如果某份文档已经主要承担“历史盘点、一次性探索、已完成迁移分析”职责，应迁入 `docs/archive/plans/`，不要继续停留在当前执行层。

复杂任务在进入实现前，必须先有明确的 `PLAN-*.md` 或等价执行依据；`current-status.md` 和 `handoff.md` 不能替代正式 PLAN。

---

## 推荐工作流

1. 先复制 [TEMPLATE.md](./TEMPLATE.md)
2. 按实际改动填写目标、非目标、范围和验收标准
3. 实施过程中持续更新正式 PLAN 的“进度记录”，并把当天状态同步到 [current-status.md](./current-status.md) / [handoff.md](./handoff.md)
4. 每日结束时，将当天已完成的状态块和交接块迁入 `docs/plans/daily/YYYY-MM/`
5. 每日归档后，主区只保留当前仍需继续推进的最新状态与交接
6. 主题完成后，必须执行一次“是否继续作为执行依据 / 是否迁入 `docs/archive/plans/` / 是否切换下一个主主题”的收口判断

---

## 当前文件

- [TEMPLATE.md](./TEMPLATE.md)：计划模板
- [current-status.md](./current-status.md)：当前阶段状态面板
- [handoff.md](./handoff.md)：线程间交接记录
- `daily/YYYY-MM/YYYY-MM-DD-status.md`：某一天的状态快照
- `daily/YYYY-MM/YYYY-MM-DD-handoff.md`：某一天的交接快照
- `PLAN-*.md`：当前仍在执行或仍作为执行依据的计划文档

已完成计划、一次性审计和历史迁移分析已迁入 `docs/archive/plans/`。

---

## 对 `current-status.md` 和 `handoff.md` 的维护要求

- `current-status.md`
  - 只维护当前仍在推进的当前主主题状态
  - 每天结束后，将已完成或阶段性收口的状态块迁入对应的 `daily/.../YYYY-MM-DD-status.md`
- `handoff.md`
  - 只保留当前阶段仍有行动价值的当前主主题交接块
  - 每天结束后，将已完成或只剩追溯价值的交接块迁入对应的 `daily/.../YYYY-MM-DD-handoff.md`

---

## Daily 与 PLAN 的区别

- `PLAN-*.md`
  - 保存主题级正式计划、范围、非目标、风险、验收标准和进度记录
  - 按主题维护，不按天堆日志
- `daily/*.md`
  - 保存某一天结束后的状态快照和交接快照
  - 主要服务按日期审查，不替代正式 PLAN

`handoff.md` 负责行动，不负责长期存史；长期追溯优先查看 `daily/` 和 `docs/archive/plans/`。

查看某一天的历史记录时，优先进入对应月份目录，例如 `docs/plans/daily/2026-03/`，再按 `YYYY-MM-DD-status.md` / `YYYY-MM-DD-handoff.md` 查找。

---

## 命名补充

- 正式计划统一使用 `PLAN-YYYYMMDD-主题.md`
- 探索输入若只是为正式计划服务，优先在正式计划中沉淀摘要，避免长期保留多个同主题并列文件
- 审计类文档若已完成使命，应迁入 `docs/archive/plans/`
- 历史主题不应继续在 `plans` 主入口长期堆积；若只剩追溯价值，应尽快下沉到 `daily/` 或 `docs/archive/plans/`

---

## 相关文档

- [变更计划规范](../guides/变更计划规范.md)
- [AI 多线程协作 SOP](../guides/ai-collaboration-sop.md)
- [文档体系规范](../guides/文档体系规范.md)
- [docs 主目录](../README.md)
