# 规范指南

> 面向长期维护的稳定规则层，约定“什么内容写到哪里、怎么写、谁来维护”。

---

## 适用范围

本目录只保留跨阶段、跨需求、可长期复用的规则文档，例如：

- 文档体系与信息架构
- 计划编写与变更管理
- 协作流程与交付约束
- 角色边界、验收和归档规则

不适合放在这里的内容：

- 一次性方案、专题推进记录：放 `docs/plans/`
- 已完成事项、历史总结、合并来源：放 `docs/archive/`
- 基础使用、部署、接入、培训型说明：默认不再作为正式文档层长期维护；若确有需要，再按当时场景重写

---

## 当前文档

- [文档体系规范.md](./文档体系规范.md)
- [变更计划规范.md](./变更计划规范.md)
- [AI 多角色协作 SOP](./ai-collaboration-sop.md)
- [five-role-vibe-coding-framework.md](./five-role-vibe-coding-framework.md)：本项目 Five Role 适配说明，通用方法见 `five-role-collaboration` skill
- [product-positioning.md](./product-positioning.md)
- [frontend-guidelines.md](./frontend-guidelines.md)
- [backend-guidelines.md](./backend-guidelines.md)
- [device-data-classification.md](./device-data-classification.md)
- [device-monitor-template.md](./device-monitor-template.md)
- [compensation-device-classification.md](./compensation-device-classification.md)
- [mqtt-gateway-protocol.md](./mqtt-gateway-protocol.md)
- [script-guidelines.md](./script-guidelines.md)

---

## 使用顺序

1. 先读 [文档体系规范.md](./文档体系规范.md)，判断文档应该落在哪
2. 再读 [变更计划规范.md](./变更计划规范.md)，判断是否需要正式 `PLAN`
3. 若涉及多角色协作，再读 [AI 多角色协作 SOP](./ai-collaboration-sop.md)
4. 若涉及高频开发、角色切换或并行边界，先按 `five-role-collaboration` skill 判断通用分流，再读 [five-role-vibe-coding-framework.md](./five-role-vibe-coding-framework.md) 确认本项目适配口径
5. 若涉及仓库级执行约束，同时阅读 [AGENTS.md](../../AGENTS.md)

---

## 维护原则

1. 本目录只写稳定规则，不写一次性执行日志
2. 新增规范前，优先更新已有文档，避免并列冲突
3. 规范变更后，应同步检查 [docs/README.md](../README.md) 与 [AGENTS.md](../../AGENTS.md)
4. 若目录结构已变化，必须及时移除失效目录描述，避免规范继续误导执行
