# Memory Court — OpenAI Build Week 参赛应用设计规格

- 日期：2026-07-18
- 状态：已完成交互式设计确认，等待书面规格复核
- 应用边界：`/Users/bill/game/hackathon/` 下的独立参赛应用
- 部署：Vercel 前端 + Railway FastAPI
- 模型：GPT-5.6

## 1. 产品目标

Memory Court 是一个可审计的自主记忆干预演示。GPT-5.6 自主调查病例、提出结构化记忆干预，`sonuv-guard` 对干预状态进行 COMMIT、REPAIR、REJECT 或 FORGET 裁决。评委能够在一个页面内看到模型为何采取行动、参数是否有效、Guard 实际应用了什么，以及状态如何变化。

产品不宣称 Guard 审查 GPT-5.6 的自然语言，也不宣称 Guard 验证探索动作。Guard 的准确边界是：验证结构化记忆状态干预并控制状态提交。

## 2. 与既有项目的边界

参赛应用独立于 `palace-cleaner-demo`：

- 不导入或修改 `palace-cleaner-demo/server.py`。
- 不复用旧游戏的全局 session。
- 复用现有 `sonuv-guard` Python 包的精确快照，但不修改其上游源码；公开参赛目录中的 vendored 快照必须注明来源 commit 和赛前资产属性。
- 可复用一个既有病例作为兼容性样例，并在提交材料中标为赛前资产。
- 新增比赛期内创建的病例 `silent_lifeboat`。
- 自主 agent、审计协议、前后端、回放、部署和参赛材料均属于比赛期新增内容。

## 3. 系统结构

```text
hackathon/
├── frontend/          # React + TypeScript + Vite，部署到 Vercel
├── backend/           # FastAPI，部署到 Railway
├── cases/             # 独立病例数据
├── replay/            # 明确标记的离线演示轨迹
├── docs/              # 设计、提交文案、视频脚本、验证报告
└── scripts/           # 本地启动和提交前检查
```

Vercel 只托管静态前端。Railway 保存 OpenAI API key、通过 OpenAI Python SDK 的异步 Responses API 调用 GPT-5.6，并执行动作校验、Guard 裁决、限流和会话管理。为使公开的 `hackathon` 子树可独立构建，后端 vendoring `sonuv-guard` commit `62157c5` 的运行时包快照，并在 provenance 文档中明确它是赛前资产。Docker 只使用公开参赛目录作为构建上下文。

## 4. 自主循环

GPT-5.6 每轮只能选择一个结构化动作：

1. `inspect_memory(memory_id)`：读取一段证据并写入审计轨迹，不经过 Guard。
2. `propose_intervention(patch, rationale)`：提出结构化状态修改；后端先做 schema、字段白名单和范围校验，再调用 `sonuv-guard`。
3. `finalize(outcome, rationale)`：终止案件并给出伦理判断。

后端执行动作后，将真实结果交还 GPT-5.6，再进入下一轮。循环限制为每个会话最多 8 个模型调用、最多 8 个执行步骤、最多 3 次干预提案；每次模型调用最多输出 600 tokens。达到结局、任一上限或连续两次无效动作时终止。

单次模型请求超时为 30 秒；超时或 429 退避后重试一次。重试仍失败时停止实时会话，并向用户提供明确标记的回放模式。

## 5. API 契约

```text
GET  /api/health
GET  /api/cases
POST /api/sessions
POST /api/sessions/{id}/step
POST /api/sessions/{id}/run
GET  /api/sessions/{id}
GET  /api/replays/{case_id}
```

`POST /api/sessions/{id}/step` 每次返回一个审计事件。核心字段为：

```json
{
  "mode": "live",
  "step": 3,
  "model": "gpt-5.6",
  "model_action": "propose_intervention",
  "rationale": "Increase acceptance gradually while preserving trust.",
  "validation": {"accepted": true, "errors": []},
  "guard": {
    "action": "REPAIR",
    "reason": "Distress reduction exceeded the safe transition limit.",
    "requested_patch": {"acceptance": 68, "distress": 45},
    "applied_patch": {"acceptance": 68, "distress": 54}
  },
  "state_diff": {
    "acceptance": {"before": 22, "after": 68},
    "distress": {"before": 74, "after": 54}
  },
  "terminal": false
}
```

探索和终止事件的 `guard` 字段为 `null`，避免误导用户认为这些动作经过 Guard。

`POST /api/sessions/{id}/run` 在同一请求中顺序执行 step，直到产生 terminal 事件或命中限制，并返回完整事件数组；它不使用后台任务或流式连接。

## 6. 病例

首版包含两个病例：

- `last_birthday`：复用并注明为赛前资产的 Palace Cleaner 丧亲病例，用来证明自主循环能驱动既有 `sonuv-guard` 规则。
- `silent_lifeboat`：比赛期内编写的太空救生艇伦理病例。任务指挥官保留一段保护性错误记忆，以回避自己放弃一名队员的决定；状态维度为 accountability、distress、trust 和 mission_stability。

病例文件是静态、受版本控制的数据。API 不接受用户上传 Python 表达式或自定义 Guard 规则。

## 7. 前端体验

页面采用已批准的单屏三栏布局：

- 左栏：活动病例、当前状态、启动/重置控制、模式和限制说明。
- 中栏：按时间排列的 GPT-5.6 动作、理由、参数校验和执行结果。
- 右栏：Guard 裁决、requested/applied patch 差异、状态 diff 和审计导出。

页面顶栏始终显示 `LIVE · GPT-5.6` 或 `REPLAY MODE`。回放不得使用容易与实时调用混淆的样式或文案。运行按钮触发逐步执行，前端在每个 step 响应后更新轨迹，不依赖服务端流式传输。

视觉方向为深色审计控制台：金色表示模型提案，蓝色表示调查动作，绿色表示通过或修复后的提交，红色表示拒绝或错误。界面必须支持键盘操作、可见焦点和不只依赖颜色的状态标签。

## 8. 故障与降级

- GPT-5.6 正常返回：记录 live 模式、模型 ID、动作、延迟和裁决。
- API key 未配置：`/api/health` 返回 `live_available=false`，前端只允许回放。
- 超时或 429：退避后重试一次；仍失败则停止 live 会话并提供回放。
- schema 无效：记录 `VALIDATION_REJECTED` 并反馈模型；连续两次无效终止。
- Guard 异常：不提交状态，返回 `GUARD_ERROR`，禁止绕过 Guard。
- 前端断线：Railway 内存会话保留一小时，可用 session ID 恢复。
- replay：使用版本控制中的固定审计事件，响应中始终带 `mode=replay`。

## 9. 安全与成本控制

- OpenAI API key 只存在于 Railway 环境变量。
- CORS 允许正式 Vercel 域名和显式本地开发地址。
- session ID 使用密码学安全随机值。
- 模型只能修改病例声明的白名单字段和数值区间。
- 审计 JSON 不记录密钥、认证头或内部异常堆栈。
- 每个客户端地址 10 分钟最多创建 5 个实时会话。默认使用 socket 来源地址；仅在 Railway 部署显式设置 `TRUST_PROXY=true` 时读取平台代理提供的首个 `X-Forwarded-For` 地址。
- 首版采用单 Railway 实例和进程内固定窗口限流；README 明确其 demo 级边界。
- 每个会话最多 8 个模型调用，每次最多输出 600 tokens。

## 10. 测试策略

实现遵循测试先行的 RED-GREEN-REFACTOR 循环。最低覆盖：

- 结构化动作解析和非法参数拒绝。
- 每一步只执行一个动作。
- 探索动作不产生 Guard 裁决。
- 干预必须经过 Guard。
- REPAIR 记录 requested/applied 差异。
- REJECT 不改变状态。
- 步数、提案数和连续无效动作限制。
- 无 key、超时和 429 进入明确标记的回放。
- 限流和 CORS。
- 前端 live/replay 标签、三栏轨迹和状态 diff。
- Docker 构建和本地端到端 smoke。
- 现有 `sonuv-guard` 121 项回归。

模型客户端使用接口注入，单元和集成测试使用确定性 fake client；只有凭证 smoke 测试访问真实 GPT-5.6。

## 11. 参赛材料

参赛目录必须包含：

- 英文 README：安装、运行、架构、GPT-5.6 用法、Codex 协作过程。
- `PREEXISTING_VS_NEW.md`：区分赛前资产与比赛期新增内容。
- `SUBMISSION.md`：可粘贴到 Devpost 的英文材料。
- `DEMO_SCRIPT.md`：三分钟以内英文旁白与镜头表。
- `CODEX_EVIDENCE.md`：主要构建任务、Codex Session ID 和提交记录。
- `SECURITY.md`、开源许可证和 `.env.example`。
- 提交前验证报告。

根目录 `/Users/bill/hackathon_game_plan.md` 同步改写为证据约束的执行计划，不再宣称 Guard 审查 GPT 文本，也不再使用未经验证的候选项目星级比较。

## 12. 完成标准

应用达到“可直接参赛”需要同时满足：

1. Vercel 前端和 Railway API 公开可访问。
2. 实时 GPT-5.6 路径通过一次真实凭证 smoke；若凭证不可用，状态必须明确写为未完成，不得以 replay 替代此验收项。
3. API 故障时可进入明确标记的 replay。
4. 比赛期新增功能有 Git 提交和 Codex 构建证据。
5. 新增测试、旧 Guard 121 项、Docker 构建和部署 smoke 全部通过。
6. README、提交文案和视频脚本无未填写占位符。
7. 公开仓库具有许可证和测试说明。
8. 最终只剩参赛者本人确认地区资格、上传 YouTube 视频并点击 Devpost 提交。

## 13. 非目标

- 不修改或继续打磨 `palace-cleaner-demo`。
- 不证明现有游戏的可玩性假设。
- 不把 demo 级内存限流描述为生产级安全系统。
- 不声称 Guard 审查或保证 GPT 自然语言安全。
- 不支持多实例共享 session 或分布式限流。
- 不在本阶段增加多人游戏、账号系统、数据库或用户自定义规则。
