# CLI TODOs

本文档记录把 `coros-mcp` 从 MCP-first 逐步补齐为 CLI-first 的剩余工作。

## 基本原则

- CLI 不需要启动 `coros-mcp serve`。
- `serve` 只负责 MCP stdio 服务。
- CLI 命令应直接调用本地 domain layer / `coros_api`。
- 本地只读命令应尽量不认证、不触网。
- 写入 COROS 的命令必须显式命名，例如 `schedule`、`remove`、`update`、`delete-template`。
- 所有 agent/skill 友好的 CLI 命令优先输出 JSON。

## P1：补齐日历 planned workout 闭环

- [x] `coros-mcp planned list --from YYYYMMDD --to YYYYMMDD`
- [x] `coros-mcp planned list-raw --from YYYYMMDD --to YYYYMMDD`
- [x] `coros-mcp planned remove --plan-id ID --id-in-plan ID [--plan-program-id ID]`
- [x] `coros-mcp planned calculate --program-file program.json`
- [x] `coros-mcp planned update --entity-file entity.json --program-file program.json`
- [x] `coros-mcp planned add --entity-file entity.json --program-file program.json`

目标：让“查看 / 修改 / 删除已安排课表”可以不通过 MCP 完成。

## P2：补齐 running template CLI 闭环

- [x] `coros-mcp running delete-template --workout-id ID`

目标：running template 已经能保存、列出、安排，还需要删除入口。

## P3：补齐通用 workout template CLI

- [x] `coros-mcp workout list-templates`
- [x] `coros-mcp workout delete-template --workout-id ID`
- [x] `coros-mcp workout schedule-template --workout-id ID --happen-day YYYYMMDD`
- [x] `coros-mcp workout save-template --file workout.json`

目标：让骑行/通用 workout template 也具备 CLI 闭环。

## P4：补齐 strength CLI

- [x] `coros-mcp strength schedule --file strength.json`
- [x] `coros-mcp strength save-template --file strength.json`
- [x] `coros-mcp strength list-exercises [--sport-type 4]`

目标：让力量训练不依赖 MCP。

## P5：训练计划 training plan 能力调研与实现

当前底层已支持：

- `fetch_training_plans`
- `fetch_training_plans_raw`

但还没有完整训练计划 CRUD：

- [ ] 创建 training plan
- [ ] 修改 training plan
- [ ] 删除 / 归档 training plan
- [ ] 将多日 workouts 组织成 plan
- [ ] 查询 Training Hub 对应接口和 payload

目标：先不要把 workout calendar 闭环误称为 training plan 闭环；真正 training plan 需要单独抓包和设计。

## P6：agent/skill 集成

- [ ] 基于 CLI 写 running workout skill
- [ ] 规范 JSON 输入模板
- [ ] 增加示例课表库
- [ ] 将 `docs/running_workout_agent_guide.md` 中的知识转成 skill 操作步骤
