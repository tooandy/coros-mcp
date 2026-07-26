# Running Workout Remaining Gaps

本文档记录 `coros-mcp` 当前跑步课表能力的剩余缺口。

目标不是重新描述已经支持的能力，而是回答两个问题：

1. 从“对齐 COROS 当前产品能力”角度，还缺什么？
2. 从“MCP / agent / 后续 CLI 可用性”角度，还缺什么？

---

## 已修正的判断

下面两条不应再作为当前缺口：

- “跑步语义偏窄”
  - 这个表述不准确。就 COROS 跑步课表当前产品形态而言，动作、目标、强度的大类本身就是有限集合。
  - 当前问题不是“语义种类太少”，而是“语义映射还没有完全证据化、文档化、闭环化”。

- “直接数值强度不支持开区间”
  - 这不算缺陷。
  - 现有样本和产品行为都表明，COROS 本身就不支持这类表达，因此当前拒绝 open-ended direct range 是合理限制。

---

## 当前主要缺口

### 1. MCP 能力还不闭环

状态：已部分完成。

已完成：

- `validate_running_workout`
- `render_running_workout`
- `compile_running_workout`
- `preview_running_workout`

这些工具已经把“校验 / 预览 / 编译 / 下发”拆成独立步骤，其中前 4 个是只读工具，`schedule_running_workout` 仍然是唯一写日历入口。

已完成最小 running-first template lifecycle：

- `save_running_workout_template`
- `list_running_workout_templates`
- `schedule_running_workout_template`
- 删除跑步模板可复用 `delete_workout_template`

仍未完成：

- running-first update/delete alias
- 参数化 running template
- 用 running-first 语义反编译 / 渲染已有模板

关于后续模板化方向，已经单独整理在：

- [running_workout_templates.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/running_workout_templates.md)

只读 MCP 闭环已经补齐，模板生命周期也已经有最小可用闭环。后续重点是参数化模板和已有模板的语义化编辑。

---

### 2. 百分比强度映射还没有完全证据闭合

状态：部分推进。

当前已经支持以下 `%` 语义大类：

- `%最大心率`
- `%储备心率`
- `%乳酸阈心率`
- `%乳酸阈配速`
- `%等强阈值配速`

并且已经有一部分 zone family 映射表。

已完成：

- 新增 [running_workout_zone_evidence.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/running_workout_zone_evidence.md)，区分“样本已标注 / 样本未标注 / 当前实现假设”。
- 已将样本明确证明的配速阈值家族 `aerobic_power_zone=85.1-92.6` 固化到代码、测试和 agent guide。

但从“完全对齐 COROS”角度，还缺最后一步：

- 找全每个 `intensity type`
- 在每个 `zone preset` 下
- 默认 `low/high` 百分比到底是多少

也就是说，这里的核心问题不是复杂计算，而是证据采集和映射固化。

### 这部分的目标状态

代码和文档中应能明确回答：

- `heart_rate_percent_max × warmup_zone` 的默认上下限是多少
- `heart_rate_percent_reserve × aerobic_power_zone` 的默认上下限是多少
- `heart_rate_percent_lthr × lactate_threshold_zone` 的默认上下限是多少
- `pace_percent_lthr × speed_endurance_zone` 的默认上下限是多少
- `effort_pace_percent_threshold × aerobic_endurance_zone` 的默认上下限是多少

### 当前还未完全闭合的点

- 是否所有 zone 都已被样本或抓包直接证明
- 是否还存在 alias / display-only zone name
- 百分比模式下 `intensityValue / intensityValueExtend` 是否始终可以仅靠固定 zone 表推导出来
- 如果 COROS 还依赖用户的阈值基准值，是否需要额外文档说明“百分比固定，但绝对值取决于用户阈值”

---

### 3. 文档还不够 agent-friendly

状态：已完成第一版。

当前已经有：

- [Coros_API_Params.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/Coros_API_Params.md)
- [exercises.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/exercises.md)
- [running_workout_agent_guide.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/running_workout_agent_guide.md)

其中 `running_workout_agent_guide.md` 是面向 agent 的操作型文档，已经覆盖：

- 支持的动作枚举
- 支持的 target 枚举
- 支持的 intensity 枚举
- 每种 intensity 支持 `range` 还是 `zone`
- 每种 target / intensity 编译后映射到哪些 COROS wire 字段
- 已知不支持项
- 推荐调用方式
- 示例输入

后续如果 P2 补齐更多 `%` zone 证据，需要同步更新这份文档。

---

### 4. Running 入口仍有分裂

当前和 running 相关的调度入口至少有两条：

- `schedule_workout`
- `schedule_running_workout`

这带来的问题不是功能不能用，而是：

- agent 需要自己判断什么时候走 legacy 入口
- agent 需要知道哪条路径支持更完整的 running 语义
- 后续如果继续增强 running，容易出现两套行为不完全一致

理想状态：

- 新 running 流程默认只推荐 `schedule_running_workout`
- legacy `schedule_workout` 仅作为兼容入口保留
- 文档明确说明两者边界
- 未来有机会时，让 running 场景统一复用同一套 semantic compiler

---

### 5. 课表生命周期能力仍不足

当前 running-first 已经支持“一次性课表下发”和“保存固定结构模板后再安排”。

但从“完整课表能力”来看，还缺：

- 列出 running 模板及其语义摘要
- 更新已有 running 模板
- running-first 删除 alias
- 将已有模板反编译回 running semantic schema
- 参数化模板
- 基于模板批量安排多天课表

这部分不一定要马上做，但它决定了后续是否能从“one-off scheduling”走向“真正可复用的跑步课表系统”。

补充说明：

- 模板化能力建议单独演进，不要和当前 running workout 主链路增强混在一起推进
- 当前已经有一份后续设计草稿，见 [running_workout_templates.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/running_workout_templates.md)
- 如果后续首批模板面向汉森训练法，建议优先采用更收敛的 `hansons-first` 抽象，而不是一开始就做成大而全的通用模板系统

---

### 6. Group 能力仍可增强

这不是说 COROS 还有更多动作种类。

这里的意思是：当前内部结构仍然把“间歇”建模成固定的：

- `repeat`
- `work`
- `recovery`

这个结构已经足够覆盖最常见的跑步间歇。

但如果后面要更完整贴合 App / Web 的组装能力，仍可能需要探索：

- 一个 group 内是否允许超过 2 个子步骤
- 是否存在 group-level pause / rest 语义
- 是否存在嵌套结构
- 是否存在更复杂的 block 组织方式

当前这不是最优先的问题，但它是后续“继续往上做完整课表编辑能力”时需要重新验证的一项。

---

## 优先级建议

### P1

- 已完成：补齐 MCP 只读闭环能力
  - validate
  - render / preview
  - compile
- 已完成：整理一份 agent-friendly 支持矩阵文档

### P2

- 部分完成：新增 zone evidence 文档
- 部分完成：固化样本已证明的配速阈值家族 `aerobic_power_zone=85.1-92.6`
- 待完成：把所有 `%` 强度的 `type × zone × low/high` 证据补齐
- 待完成：将剩余区间映射正式固化到代码、测试、文档

### P3

- 已完成：最小 running template lifecycle
  - `save_running_workout_template`
  - `list_running_workout_templates`
  - `schedule_running_workout_template`
- 待完成：running-first update/delete alias
- 待完成：已有模板语义反编译 / 摘要渲染
- 待完成：沉淀并实现 [running_workout_templates.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/running_workout_templates.md) 中的参数化 running-first / hansons-first 模板设计
- 评估是否需要更强的 group 结构表达

### P4

- 已完成：新增本地 running authoring CLI 底座
  - `coros-mcp running validate`
  - `coros-mcp running render`
  - `coros-mcp running compile`
  - `coros-mcp running preview`
- 待完成：将写路径逐步补到 CLI
  - schedule one-off running workout
  - save/list/schedule running template
  - auth-aware command output
- 待完成：再结合 skill 做高层提效

---

## 当前结论

全局来看，`coros-mcp` 的跑步课表能力已经跨过了“能发一个简单跑步课表”的阶段。

当前真正缺的，不再是动作/目标/强度种类本身，而是：

- 把 MCP 做闭环
- 把百分比映射做证据闭合
- 把知识组织成 agent 能稳定消费的文档
- 把 one-off scheduling 扩展成完整生命周期能力
