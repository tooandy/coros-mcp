# 跑步课表只读 MCP 工具设计

## 摘要

本文档设计一组 running-first 的只读 MCP 工具，建立在 `coros-mcp` 现有跑步语义领域层之上。

目标是在真正下发课表之前，让跑步课表编写过程对 agent 更友好。现在 agent 如果想验证一个跑步课表，基本只能直接调用 `schedule_running_workout`。这轮要把当前已有的 running domain 能力显式暴露出来：

- 标准化 + 校验
- 人类可读摘要渲染
- COROS payload 编译
- 综合预览

这些工具都应是只读工具：

- 不触发网络请求
- 不要求认证
- 不写日历
- 不写模板库

它们的作用是补齐 MCP 编写闭环，同时为后续 CLI 复用同一套代码形态打基础，避免重复实现跑步逻辑。

## 问题

当前跑步语义模型已经存在，但 MCP 调用者只有一个 running-first 入口：

- `schedule_running_workout`

这意味着 agent 只能通过“尝试下发”来确认课表是否合法。这会带来几个问题：

- 校验能力不能单独调用
- 编译后的 payload 不能单独查看
- 摘要渲染必须绕到 scheduling 工具里才能拿到
- preview 类工作流很别扭
- 未来 CLI 需要暴露的概念，在 MCP 层仍然是隐藏的

问题不在于 domain 层缺少跑步语义，而在于 MCP 还没有把这些语义暴露成只读工作流。

## 目标

- 新增 running-first 的只读 MCP 工具，覆盖 validate、render、compile、preview。
- 复用现有 `normalize -> validate -> render -> compile` 跑步领域链路。
- 保持现有下发行为不变。
- 返回结构化结果，而不是让原始异常穿透 MCP 工具边界。
- 将 `preview_running_workout` 作为 agent 编写和调试跑步课表时的首选入口。
- 保持设计可直接迁移到后续 CLI 命令。

## 非目标

- 不改变跑步语义模型本身。
- 不给只读 running 工具增加认证要求。
- 不在新工具里调度或保存课表。
- 不替代 `schedule_running_workout`。
- 不在本阶段实现 running template lifecycle。
- 不重新设计当前 renderer 已支持之外的渲染能力。

## 用户可见 MCP 变化

新增 4 个 MCP 工具。

### `validate_running_workout`

用途：

- 标准化输入
- 校验语义正确性
- 返回结构化成功或失败结果

典型场景：

- agent 在下发前检查课表结构是否合法
- 人类调试非法 running workout 输入

### `render_running_workout`

用途：

- 标准化输入
- 校验输入
- 返回当前人类可读摘要字符串

典型场景：

- 用户或 agent 快速检查课表内容
- 后续 skill 需要一个简短文本预览

### `compile_running_workout`

用途：

- 标准化输入
- 校验输入
- 编译最终 COROS inline program payload

典型场景：

- 对照语义输入和 COROS wire 输出
- 逆向分析和 QA 时检查字段映射

### `preview_running_workout`

用途：

- 提供一次性的只读编写预览结果

它应返回：

- normalized workout 结构
- rendered summary
- compiled COROS payload
- validation 成功/失败状态

典型场景：

- agent authoring flow 的默认入口
- “看看实际会下发什么”的预览工作流

## 输出结构

4 个工具都应返回结构化字典。

### 成功结构

至少包含：

```json
{
  "ok": true
}
```

每个工具再追加自己的业务字段。

### 失败结构

所有只读工具都使用一致的失败合约：

```json
{
  "ok": false,
  "error": "human-readable error message"
}
```

工具边界不应泄漏原始异常。

## 工具合约

### `validate_running_workout`

输入：

- `name`
- `steps`
- `happen_day`
- `description`，可选
- `sort_no`，可选

成功输出：

```json
{
  "ok": true,
  "valid": true,
  "normalized_workout": { "...": "..." }
}
```

失败输出：

```json
{
  "ok": false,
  "valid": false,
  "error": "..."
}
```

### `render_running_workout`

输入：

- 同上，使用相同的 semantic running workout 字段

成功输出：

```json
{
  "ok": true,
  "rendered_summary": "Warmup 15 min | 4 x [...]"
}
```

### `compile_running_workout`

输入：

- 同上，使用相同的 semantic running workout 字段

成功输出：

```json
{
  "ok": true,
  "program": { "...": "final coros payload ..." }
}
```

### `preview_running_workout`

输入：

- 同上，使用相同的 semantic running workout 字段

成功输出：

```json
{
  "ok": true,
  "valid": true,
  "normalized_workout": { "...": "..." },
  "rendered_summary": "...",
  "program": { "...": "..." }
}
```

## 设计约束

### 复用当前 domain 逻辑

新增 MCP 工具必须复用现有 running 模块：

- `normalize_running_workout`
- `validate_running_workout`
- `render_running_workout`
- `compile_running_workout`

MCP 层不应增加第二套校验或编译路径。

### 不要求认证

因为这些工具是只读且纯本地的：

- 不应调用 `_get_auth()`
- 不应调用 `_run_with_auth()`
- 不应依赖已存储的 COROS credentials

### 保持 schedule 行为不变

`schedule_running_workout` 仍然是写路径，不被这些新工具替代。

## 实现形态

### Server 层

实现应放在 `coros_mcp.server` 内。

可能新增：

- 一个很小的共享 helper，用 MCP tool args 构建 `RunningWorkout`
- 一个很小的共享 helper，将异常包装成 `{ok: false, error: ...}`

这样可以避免 4 个工具重复 normalize / validate 样板代码。

### Domain 层

除非实现时发现确实需要一个很小的序列化便利函数，否则 running domain 层应保持不变。

预期结果：

- 不改变语义行为
- 只增加 MCP 暴露面

## 序列化

`RunningWorkout`、`StepNode`、`IntervalNode` 和嵌套 dataclass 不适合直接作为 MCP 返回值。

因此：

- 只要成功响应包含 normalized 结构，就应序列化成普通 dict/list
- 序列化应是确定性的，并且只服务于 running MCP 路径

这个序列化只需要支持当前 running dataclasses，不需要做成通用框架。

## 测试

新增聚焦测试，覆盖：

- 4 个新工具注册到 `mcp.list_tools()`
- `validate_running_workout` 的成功和失败响应
- `render_running_workout` 的成功和失败响应
- `compile_running_workout` 的成功和失败响应
- `preview_running_workout` 的成功和失败响应
- 这些工具不要求 auth
- `schedule_running_workout` 行为保持不变

主要测试位置：

- `tests/test_running_tool.py`

如有需要，可在这里补小型回归：

- `tests/test_post_release_review_fixes.py`

## 文档

更新 `README.md`，让 running tool surface 的职责更清晰：

- `preview_running_workout`：默认编写/调试入口
- `validate_running_workout`：只做校验
- `render_running_workout`：只看摘要
- `compile_running_workout`：查看 payload
- `schedule_running_workout`：真正写入日历

这样 agent 和人类都更容易选择正确工具。

## 风险

### 工具数量增加

新增 4 个工具会扩大 MCP surface area。

缓解方式：

- 清楚记录每个工具的职责
- 推荐 `preview_running_workout` 作为默认只读入口

### 返回结构不一致

如果每个工具各自发明结果格式，agent 会更难稳定使用。

缓解方式：

- 使用共享的 `ok` / `error` 合约
- 字段名保持稳定、明确

### 过早抽象

本阶段不应围绕 tool wrapping 或 dataclass serialization 做大型通用框架。

缓解方式：

- helper 保持窄而直接
- 只解决这 4 个 running 工具需要的问题

## 成功标准

本设计完成时应满足：

- MCP 暴露 4 个新的只读 running 工具
- 新工具不需要 auth
- 新工具返回结构化成功/失败结果
- 新工具复用现有 running 语义，不重新实现校验/编译逻辑
- `schedule_running_workout` 仍然是唯一写路径
- README 清楚说明每个 running 工具适合什么场景

## 当前建议

先实现这层只读 MCP 能力，再开始 running template lifecycle 或 CLI 抽取。

这个顺序可以同时获得：

- 更好的 MCP 编写闭环
- 更清晰的 agent 使用入口
- 后续 CLI 命令可复用的接口形态
