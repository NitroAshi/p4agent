# Coverity -> P4 -> Swarm Agent Flow 实施清单（可直接执行）

## Summary
本方案将人工流程重构为 `1 个对外 Flow Task + 4 个内部分步`：自动接收告警、同步代码、生成局部修复，人工确认后发布 Helix Swarm review。
默认策略为：`事件驱动+手动兜底`、`单告警单运行`、`仅人工确认`、`仅函数内部修改`、`CI+本地混合执行`。

## Public APIs / Interfaces / Types
1. 新增任务 `coverity_fix_flow`。
2. 输入字段：
`mode`（`analyze_patch` | `publish_review`）、`finding_ref`（`project/stream/cid/checker/file/function/line_start/line_end`）、`run_id`（publish 必填）、`approval_token`（publish 必填）。
3. 输出字段：
`status`、`run_id`、`step_statuses`、`artifacts`、`swarm_review_url`（publish 成功时返回）。
4. 内部步骤接口：
`ingest_finding`、`sync_workspace`、`propose_and_apply_fix`、`publish_review`。
5. 状态机：
`RECEIVED -> SYNCED -> PATCHED -> NEEDS_HUMAN_APPROVAL -> PUBLISHED`，失败进入 `FAILED`。
6. 幂等键：
`project + stream + cid + file + function`。

## Execution Plan
1. M1 集成打通（不改代码、不发 review）。
交付：Coverity finding 标准化、`p4 sync`、run 状态记录、artifacts 输出、CLI/API 可触发。
验收：单 finding 可稳定落到 `SYNCED` 或可诊断失败。
2. M2 修复生成（到人工确认）。
交付：函数内 patch 生成与应用、修改范围守卫、审批包输出。
验收：越界修改自动拦截，成功场景进入 `NEEDS_HUMAN_APPROVAL`。
3. M3 发布 review（人工确认后）。
交付：shelve + Helix Swarm review 创建/更新、publish 重试机制、事件触发闭环。
验收：审批后可进入 `PUBLISHED`，失败可重试 publish 且不重复改码。

## Testing Scenarios
1. Happy path：单告警端到端成功并返回 Swarm URL。
2. 重复触发：同幂等键不重复创建 run。
3. 行号漂移：定位失败时终止并返回可读错误。
4. 守卫拦截：跨函数或跨文件修改被拒绝。
5. P4 失败：sync 权限或冲突时终止并保留诊断信息。
6. 审批缺失：无 `approval_token` 禁止 publish。
7. Swarm 失败：仅重试 publish 即可，不重新 analyze。

## Governance / Guardrails
1. 仅函数内部修改，禁止跨函数修改。
2. 单告警单运行，不做批处理。
3. 发布前必须人工确认。
4. 每步产出审计日志与 artifacts。

## Assumptions And Defaults
1. `sweam` 指 Helix Swarm。
2. Coverity API 可用并可提供凭据。
3. 主执行路径为 CI，开发机用于调试与手动兜底。
4. 当前不启用自动质量门禁，以人工确认为主。
5. 文档落地路径固定为 `docs/coverity_fix_flow_plan.md`。
