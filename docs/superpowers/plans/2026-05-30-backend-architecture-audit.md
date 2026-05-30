# Backend Architecture Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a formal backend architecture audit track that inventories layering risks, adds lightweight documentation guardrails, and prepares later low-risk cleanup phases without changing API behavior.

**Architecture:** Treat this as a documentation-and-boundary phase first. The official project plan and audit inventory live under `docs/plans/`, durable guidance stays in `docs/guides/backend-guidelines.md`, and tests only verify that the audit artifacts remain present and structurally usable. No production backend code is moved in this phase.

**Tech Stack:** Python, pytest, FastAPI project structure, Markdown project plans, existing CampusEnergySystem Five Role documentation workflow.

---

### Task 1: Open the Backend Architecture Audit Topic

**Files:**
- Create: `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Create the official PLAN document**

Create `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md` with this content:

```markdown
# PLAN-20260530 Backend Architecture Layering Audit

## 目标

在不改变现有 API 契约、不移动生产代码的第一阶段，完成后端分层架构审计库存，明确 `api / application / services / domain / integrations` 的职责边界、风险文件和后续整改顺序。

## 范围

- 审计 `app/api/endpoints/`、`app/application/`、`app/services/`、`app/domain/`、`app/integrations/`。
- 建立后端架构审计库存文档。
- 补充后端规范中的审计分类口径。
- 增加轻量文档护栏测试，确保审计文档不丢失关键分类。
- 保持园区综合能源管理系统产品方向。

## 非目标

- 不修改公开 API 路径、请求参数、响应模型或状态码。
- 不迁移数据库、MQTT topic、环境变量、容器名或运行时兼容标识。
- 不做全量 service 重构。
- 不把本轮扩成前端改造。
- 不扩张煤矿专属建模或术语。
- 不移动生产代码；生产代码整理必须进入后续分阶段任务。

## 分层口径

- `api/endpoints`：HTTP 参数、依赖注入、响应模型、状态码和极薄异常翻译。
- `application`：用户意图和系统工作流编排、访问前置、审计、默认值和多 service 协作。
- `services`：稳定业务能力、资源读写、状态变化和查询聚合。
- `domain`：纯规则、profile 解析、payload 归一和确定性计算。
- `integrations`：MQTT、厂商协议、外部系统和边界字段映射。

## 审计分类

- `keep`：已符合目标分层，或是明确兼容层。
- `watch`：当前可接受，但不应继续扩大职责。
- `split_candidate`：存在明确职责泄漏、文件膨胀或测试困难，后续可小步整理。
- `plan_required`：风险高或影响面大，必须单独建 PLAN 后再改生产代码。

## 第一阶段交付物

- `docs/plans/backend-architecture-audit-inventory.md`
- `docs/guides/backend-guidelines.md` 的审计分类补充
- `tests/test_backend_architecture_audit_docs.py`

## 验收标准

- 审计库存覆盖主要后端分层目录。
- 每个候选文件都有分类、原因、建议落点和下一步。
- 文档明确禁止第一阶段移动生产代码。
- 轻量 pytest 文档护栏通过。
- 现有 endpoint/application 边界测试仍通过。

## 推荐验证

- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q`
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q`
```

- [ ] **Step 2: Update current status for the new topic**

Replace `docs/plans/current-status.md` with this current-topic snapshot:

```markdown
# Current Status

## 当前总目标
- 当前主主题：`后端架构分层审计与规范整理`
- 当前总目标：在不改变 API 契约、不移动生产代码的第一阶段，完成后端分层审计库存和规范护栏，为后续小步代码整理提供执行依据。
- 当前执行依据：
  - `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
  - `docs/superpowers/specs/2026-05-30-backend-architecture-audit-design.md`

---

## 当前阶段
- [ ] 建立正式后端架构分层审计 PLAN。
- [ ] 建立后端架构审计库存。
- [ ] 补充后端规范中的审计分类口径。
- [ ] 增加轻量文档护栏测试。
- [ ] 执行最小验证并给出阶段验收判断。

## 当前阻塞
- 当前无代码阻塞。

## 当前待办
- [ ] 确认第一阶段只做文档与护栏测试，不移动生产代码。
- [ ] 审计 `api / application / services / domain / integrations` 主要文件职责。
- [ ] 将高风险生产代码整理候选标为 `plan_required`。

## 当前验证结论
- 待执行。

## 当前验收判断
- 待验收。

## 当前剩余风险
- 当前只做架构审计，不解决既有厚 service 或大 endpoint 的具体代码债。
- 若后续进入代码移动，必须按候选文件另起小步计划和测试闭环。
```

- [ ] **Step 3: Update handoff for the new topic**

Replace `docs/plans/handoff.md` with this handoff snapshot:

```markdown
# Handoff

## 当前主题
- 当前主主题：`后端架构分层审计与规范整理`
- 当前执行依据：
  - `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
  - `docs/superpowers/specs/2026-05-30-backend-architecture-audit-design.md`

---

## 阶段结论
- 已确认本主题第一阶段定位为后端架构审计与规范护栏。
- 第一阶段不移动生产代码，不改变 API 契约。
- 审计分类固定为 `keep / watch / split_candidate / plan_required`。

## 下一棒
- 规则/预判角色：
  - 建立 `docs/plans/backend-architecture-audit-inventory.md`。
  - 按分层目录给出候选文件分类、原因、建议落点和下一步。
- 后端角色：
  - 仅在审计文档和护栏测试范围内执行。
  - 不在本阶段拆 service、不改 endpoint 行为。
- 验收角色：
  - 核对文档是否覆盖主要后端分层。
  - 核对测试是否能防止审计文档关键字段丢失。

## 已验证
- 待执行。

## 剩余风险
- 审计文档会暴露后续整理候选，但不等于批准一次性重构。
- 若发现影响 API 契约的整理需求，必须升级为单独 PLAN。
```

- [ ] **Step 4: Review the topic switch**

Run:

```bash
rg -n "当前主主题|后端架构分层审计|设备监控统一模板" docs/plans/current-status.md docs/plans/handoff.md docs/plans/PLAN-20260530-backend-architecture-layering-audit.md
```

Expected: `current-status.md` and `handoff.md` mention `后端架构分层审计与规范整理` as the current main topic, and the new PLAN contains the backend audit title.

- [ ] **Step 5: Commit the topic-opening docs**

```bash
git add docs/plans/PLAN-20260530-backend-architecture-layering-audit.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: open backend architecture audit topic"
```

### Task 2: Create the Backend Architecture Audit Inventory

**Files:**
- Create: `docs/plans/backend-architecture-audit-inventory.md`

- [ ] **Step 1: Write the audit inventory**

Create `docs/plans/backend-architecture-audit-inventory.md` with this content:

```markdown
# Backend Architecture Audit Inventory

> 第一阶段库存只做事实归类，不批准批量移动生产代码。

## 分类口径

| 分类 | 含义 | 后续动作 |
| --- | --- | --- |
| `keep` | 已符合目标分层，或是明确兼容层 | 保持现状，后续避免无意义改动 |
| `watch` | 当前可接受，但不应继续扩大职责 | 新增逻辑时优先寻找更清晰落点 |
| `split_candidate` | 存在明确职责泄漏、文件膨胀或测试困难 | 后续小步计划中处理一个具体泄漏点 |
| `plan_required` | 风险高或影响面大 | 单独建立 PLAN 后再动生产代码 |

## API Endpoint 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/api/endpoints/devices/` | `keep` | 已按设备主域拆分为 management/data/monitoring/ingestion_health/补偿/储能等职责文件 | 继续作为复杂 endpoint 域目录样板 | 新增设备接口优先复用该分层 |
| `app/api/endpoints/energy/shared.py` | `split_candidate` | `shared.py` 名称容易继续吸收 schema、serializer 和 helper | `energy/schemas.py`、`energy/serializers.py` 或局部 helper | 后续第一轮 endpoint cleanup 优先审计 |
| `app/api/endpoints/campus.py` | `watch` | 文件较大，但已有 `app/application/campus.py` 承接聚合 use case | 保持 endpoint 极薄，新增聚合进 application | 新增前先查是否已有 use case |
| `app/api/endpoints/locations.py` | `watch` | 文件较大，但已有 `app/application/locations.py` | 位置树裁剪和统计优先放 application | 只在出现具体泄漏时拆 |
| `app/api/endpoints/inspection.py` | `watch` | 历史较厚，但 application convergence 已完成一轮 | application/inspection.py | 不回头重做，新增动作优先 use case |
| `app/api/endpoints/maintenance.py` | `watch` | 历史较厚，但 application convergence 已完成一轮 | application/maintenance.py | 不回头重做，新增动作优先 use case |
| `app/api/endpoints/users.py` | `keep` | 已有 users use case 收口关键写操作 | application/users.py | 避免 auth/session 越界 |

## Application 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/application/README.md` | `keep` | 已清晰说明 application/use case 职责 | 持续作为分层说明入口 | 新增 use case 后同步 |
| `app/application/device_monitoring.py` | `keep` | 承接设备监控 overview 主流程 | 保持 HTTP overview 优先入口 | 不把监控分发重新堆回 endpoint |
| `app/application/energy_management.py` | `keep` | 承接能源 overview 多 service 编排 | 保持聚合查询入口 | 与 energy endpoint cleanup 配套审计 |
| `app/application/inspection.py` | `watch` | 文件较大，但是已通过专题收口的 workflow 层 | 保持 workflow 价值，避免空壳扩张 | 只在新增巡检主流程时调整 |
| `app/application/reporting.py` | `watch` | 文件较大但职责集中在报表与 CSV payload | reporting use case | 非报表导出逻辑不要加入 |

## Service 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/services/alarm_service.py` | `split_candidate` | 告警生命周期、平台规则触发和设备族判断可能继续膨胀 | 纯规则进入 `domain`，生命周期留 service | 后续单独锁定一个规则泄漏点 |
| `app/services/device_service.py` | `split_candidate` | 设备主档、profile/default、统计和兼容能力集中 | profile/default 归一可进入 domain 或设备子服务 | 后续按一个具体职责拆 |
| `app/services/campus_service.py` | `split_candidate` | 驾驶舱聚合计算与查询能力较集中 | 纯聚合计算 helper 可下沉 domain/application | 后续先补聚合行为测试 |
| `app/services/location_service.py` | `split_candidate` | 位置树、统计、设备归属能力集中 | workflow 进 application，纯树计算可进 domain | 后续按位置树或统计单点处理 |
| `app/services/inspection_service.py` | `plan_required` | 文件大且已被 previous convergence 处理过，贸然拆容易回头重做 | 需先复核现有 application 边界 | 单独 PLAN 后处理 |
| `app/services/maintenance_service.py` | `plan_required` | 文件大且涉及状态流转与统计 | 需先复核现有 application 边界 | 单独 PLAN 后处理 |
| `app/services/devices/compensation/monitor_service.py` | `split_candidate` | 补偿监控专属能力较厚 | 设备族 service package | 按补偿监控单一职责小步整理 |
| `app/services/devices/compensation/capacitor_bank/control_command_service.py` | `plan_required` | 控制命令链路风险高，涉及现场控制语义 | 保持设备族服务，任何拆分必须有控制链测试 | 单独 PLAN 后处理 |

## Domain 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/domain/alarm_rule_profiles.py` | `keep` | 规则 profile 解析样板清晰 | 继续承接平台规则 profile | 新设备族规则优先补这里或相邻 domain |
| `app/domain/alarm_rules.py` | `watch` | 文件较大但属于纯规则集合 | 后续可转 package | 只有增长压力明确时再拆 |
| `app/domain/energy_rules.py` | `watch` | 文件较大但属于能源规则 | 后续可转 package | 保持无 DB/HTTP |
| `app/domain/analysis_rules.py` | `watch` | 文件较大但属于分析规则 | 后续可转 package | 保持无 DB/HTTP |
| `app/domain/device_payloads.py` | `keep` | payload 归一职责明确 | 继续作为接入 payload 规则入口 | 新协议 alias 不直接塞 endpoint |

## Integrations 层

| 文件/目录 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/integrations/mqtt/` | `keep` | MQTT 边界职责明确 | 保持协议/传输边界 | 业务规则不要倒灌 |
| `app/integrations/jkwf_lcd/` | `keep` | 厂商协议解码边界明确 | 保持 vendor adapter | 工程值规则与业务告警分离 |

## 第一批建议执行顺序

1. `energy/shared.py` 命名和职责审计，若确有复用压力再拆 `schemas.py` / `serializers.py`。
2. `alarm_service.py` 中一个纯规则泄漏点迁入 `domain`。
3. `device_service.py` 中一个 profile/default 归一职责拆出。
4. `campus_service.py` 聚合计算 helper 的可测试性整理。

## 第一阶段禁止项

- 禁止批量移动 service。
- 禁止调整公开接口契约。
- 禁止借审计整理运行时命名。
- 禁止把已完成的 application convergence 专题回头重做。
```

- [ ] **Step 2: Check inventory has all classification tokens**

Run:

```bash
rg -n "`keep`|`watch`|`split_candidate`|`plan_required`" docs/plans/backend-architecture-audit-inventory.md
```

Expected: all four classification tokens appear in the classification section and table rows.

- [ ] **Step 3: Commit the inventory**

```bash
git add docs/plans/backend-architecture-audit-inventory.md
git commit -m "docs: add backend architecture audit inventory"
```

### Task 3: Add Durable Backend Guideline Guardrails

**Files:**
- Modify: `docs/guides/backend-guidelines.md`

- [ ] **Step 1: Add an architecture audit classification section**

Append this section after the existing `schemas.py / serializers.py` section and before `命名规则`:

```markdown
### 后端架构审计分类

进行后端架构整理时，先把候选文件归入以下分类，不直接开始搬代码：

| 分类 | 判断口径 | 允许动作 |
| --- | --- | --- |
| `keep` | 已符合当前分层，或属于明确兼容层 | 保持现状，只补必要测试或说明 |
| `watch` | 当前可接受，但继续扩张会造成职责混杂 | 新增逻辑时优先落到更清晰的 use case、domain 或 serializer |
| `split_candidate` | 已出现明确职责泄漏、文件膨胀或测试困难 | 后续按一个具体泄漏点小步整理 |
| `plan_required` | 影响控制链、权限、数据结构、接口契约或历史专题边界 | 必须单独建立或更新 `PLAN-*.md` 后再动生产代码 |

审计结论必须说明：

- 文件路径
- 当前分类
- 分类原因
- 建议落点
- 下一步动作

第一阶段架构审计默认只产出计划、库存和护栏测试；除非 PLAN 明确批准，不移动生产代码。
```

- [ ] **Step 2: Add a shared.py guardrail**

In the existing `schemas.py / serializers.py` section, after this sentence:

```markdown
- 不再使用“不断膨胀的 shared.py”承载所有内容；若已有 `shared.py`，后续整理优先拆分为更明确的 `schemas` / `serializers`
```

Add:

```markdown
- 若历史上已经存在 `shared.py`，不得继续把 schema、serializer、业务 helper 混合塞入；新增内容前必须先判断它属于契约、轻量转换还是 use case/domain 规则。
```

- [ ] **Step 3: Review the inserted sections**

Run:

```bash
rg -n "后端架构审计分类|shared.py|plan_required" docs/guides/backend-guidelines.md
```

Expected: the new classification section appears once, `plan_required` appears in that section, and the `shared.py` guardrail appears near the existing schemas/serializers rules.

- [ ] **Step 4: Commit the guideline update**

```bash
git add docs/guides/backend-guidelines.md
git commit -m "docs: add backend architecture audit guardrails"
```

### Task 4: Add Lightweight Documentation Guardrail Tests

**Files:**
- Create: `tests/test_backend_architecture_audit_docs.py`

- [ ] **Step 1: Write failing tests for required audit artifacts**

Create `tests/test_backend_architecture_audit_docs.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_architecture_plan_declares_non_goals_and_layers():
    content = read_doc("docs/plans/PLAN-20260530-backend-architecture-layering-audit.md")

    assert "不修改公开 API 路径" in content
    assert "不移动生产代码" in content
    for layer in ["api/endpoints", "application", "services", "domain", "integrations"]:
        assert layer in content


def test_backend_architecture_inventory_contains_all_classifications():
    content = read_doc("docs/plans/backend-architecture-audit-inventory.md")

    for classification in ["`keep`", "`watch`", "`split_candidate`", "`plan_required`"]:
        assert classification in content

    for path in [
        "app/api/endpoints/energy/shared.py",
        "app/services/alarm_service.py",
        "app/services/device_service.py",
        "app/domain/alarm_rule_profiles.py",
        "app/integrations/mqtt/",
    ]:
        assert path in content


def test_backend_guidelines_include_audit_guardrails():
    content = read_doc("docs/guides/backend-guidelines.md")

    assert "后端架构审计分类" in content
    assert "第一阶段架构审计默认只产出计划、库存和护栏测试" in content
    assert "不得继续把 schema、serializer、业务 helper 混合塞入" in content
```

- [ ] **Step 2: Run the new test**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q
```

Expected: pass with `3 passed`.

- [ ] **Step 3: Run existing boundary tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q
```

Expected: pass. These tests confirm the existing endpoint/application and layer export assumptions still hold.

- [ ] **Step 4: Commit the guardrail tests**

```bash
git add tests/test_backend_architecture_audit_docs.py
git commit -m "test: guard backend architecture audit docs"
```

### Task 5: Record Verification and Phase Acceptance

**Files:**
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update current status verification**

In `docs/plans/current-status.md`, mark the completed checklist items and replace the verification and acceptance sections with:

```markdown
## 当前验证结论
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。

## 当前验收判断
- 第一阶段可判定：后端架构分层审计主题已建立正式 PLAN。
- 第一阶段可判定：审计库存已覆盖主要后端分层目录，并明确 `keep/watch/split_candidate/plan_required` 分类。
- 第一阶段可判定：本轮未移动生产代码，未改变 API 契约。
- 第一阶段可判定：后续生产代码整理必须按单一泄漏点小步执行，必要时单独建立 PLAN。
```

- [ ] **Step 2: Update handoff verification**

In `docs/plans/handoff.md`, replace `已验证` and `剩余风险` with:

```markdown
## 已验证
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。

## 剩余风险
- 本阶段只完成架构审计和文档护栏，不解决厚 service 或大 endpoint 的具体代码债。
- `energy/shared.py`、`alarm_service.py`、`device_service.py`、`campus_service.py` 等候选项需要按后续小步计划处理。
- 涉及控制链、权限、接口契约或历史专题边界的整理必须进入 `plan_required` 路径。
```

- [ ] **Step 3: Review final status docs**

Run:

```bash
rg -n "通过|第一阶段可判定|剩余风险|plan_required" docs/plans/current-status.md docs/plans/handoff.md
```

Expected: verification commands and acceptance statements are present in both status documents.

- [ ] **Step 4: Commit verification docs**

```bash
git add docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record backend architecture audit acceptance"
```

### Task 6: Final Verification Sweep

**Files:**
- No file changes expected unless verification reveals a problem.

- [ ] **Step 1: Run all planned checks**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Check git status**

Run:

```bash
git status --short
```

Expected: only unrelated pre-existing untracked files remain. In the current workspace, `.understand-anything/` may remain untracked and should not be touched unless the user explicitly asks.

- [ ] **Step 3: Prepare final handoff**

Final response must include:

```text
1. 本次目标
2. 发现的问题
3. 修改文件
4. 验证结果
5. 剩余风险
6. 需要交接给谁
```

Mention that this phase intentionally did not move production backend code.
