# 跑步课表只读 MCP 工具实现计划

目标：按 spec 增加 `validate_running_workout`、`render_running_workout`、`compile_running_workout`、`preview_running_workout` 四个只读 MCP 工具。

实施顺序：

1. 在 `tests/test_running_tool.py` 先写失败测试，覆盖工具注册、成功响应、失败响应、不需要 auth。
2. 在 `coros_mcp/server.py` 中给 running domain import 加别名，避免 MCP 工具函数与 domain 函数重名。
3. 在 `coros_mcp/server.py` 中增加两个窄 helper：构建并校验 `RunningWorkout`、序列化 normalized workout。
4. 在 `coros_mcp/server.py` 中实现 4 个只读工具，统一返回 `ok` / `error` 合约。
5. 更新 `get_help` 和 `README.md`，让工具选择路径清晰。
6. 运行 running 相关测试和全量相关回归，确认 `schedule_running_workout` 行为不变。

约束：

- 新工具不调用 `_get_auth()`。
- 新工具不调用 `_run_with_auth()`。
- 新工具不触网、不写日历、不写模板库。
- 新工具复用现有 `normalize -> validate -> render -> compile` 链路。
