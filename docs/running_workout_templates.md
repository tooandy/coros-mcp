# Running Workout Template Design Notes

本文档记录跑步课表模板化的后续设计方向。

它不是当前 `coros-mcp` 的已实现能力说明，而是为了后续实现 running-first template lifecycle 时，保留一份清晰、可复用的设计草稿。

---

## 设计目标

模板层的目标不是替代当前的 `schedule_running_workout`，而是在其上方补一层“可保存、可复用、可参数化”的跑步课表能力。

理想结构是：

1. 底层保留统一的 running semantic model
2. 模板层保存“固定结构 + 可参数化字段”
3. 实例化后展开成当前已经支持的 running workout payload
4. 最终仍复用现有 `normalize -> validate -> compile -> schedule` 链路

也就是说，模板层不应重写运行时下发逻辑，而应复用当前 running domain layer。

---

## running-first template 的含义

这里的 running-first，指的是模板能力直接围绕跑步语义建模，而不是先定义一个通用 workout 模板结构，再把跑步字段硬塞进去。

换句话说，模板中的核心对象仍然应该是：

- `step`
- `interval`
- `warmup / work / recovery / cooldown`
- `distance / time / training_load / open`
- `pace` 及其相关 running intensity

对 agent 来说，这样的模板层更容易理解，也更容易稳定调用。

---

## 现阶段建议的模板方向

如果后续首批模板能力是围绕汉森训练法这类高频体系来做，建议优先采用更收敛的 `hansons-first` 抽象，而不是过度泛化。

原因是：

- 汉森训练的模板种类本身相对有限
- 强度核心主要是配速区间
- 间歇结构主要是距离型 repeats
- 过早做成“大而全”的通用模板体系，容易增加 agent 选择空间和误用概率

---

## 汉森风格首批模板建议

如果以后首批 running-first 模板面向汉森训练法，可以先收敛为这几类：

- `easy_run`
- `tempo_run`
- `long_run`
- `strength_repeats`
- `speed_repeats`
- `rest_day`

说明：

- `recovery_run` 不建议在第一版里单列为一级模板类型
- 它更适合作为 `easy_run` 的一个轻量变体
- `interval_time` 也不建议作为汉森专属模板类型
- 汉森的典型重复更常见于距离型组织，而不是时间型组织

---

## 强度语义建议

如果模板是“汉森优先”的，模板层不建议暴露过多与训练法无关的强度类型选择。

更合适的做法是：

- 模板层使用训练语义命名
  - `easy pace`
  - `marathon pace`
  - `strength pace`
  - `speed pace`
- 实例化后再映射到底层 running schema 的具体 intensity 表达

在现阶段的 `coros-mcp` 能力下，最现实的落地方式仍然是：

- 使用 `pace`
- 并明确给出 `low/high` 上下限

因此，对汉森模板来说，强度表达建议以“配速区间”作为核心，而不是优先开放：

- 心率
- 功率
- 步频
- 等强配速

这些类型当然仍然属于 running domain 的一部分，但不一定要成为首批模板层的主表达。

---

## 间歇结构建议

对于汉森风格模板，建议优先支持：

- 距离型 `repeat`
- 固定的 `work + recovery`
- 可参数化的重复次数、work 距离、recovery 距离、work 配速区间

这意味着首批模板层不需要一开始就支持：

- 时间型 interval
- 多于 2 个子步骤的 group
- 嵌套 group
- 复杂 block 编辑器

这些属于更通用的跑步课表编排能力，可以放到更后面的版本。

---

## 模板最小抽象

建议模板分成两部分：

1. 固定结构
2. 参数槽位

例如，一个模板内部可以保存：

- 哪些 step / interval 是固定存在的
- 哪些值是实例化时再填

可参数化字段建议先支持：

- 数值参数
  - 例如 `repeat_count=6`
  - `work_distance_m=1000`
  - `cooldown_min=10`
- 枚举参数
  - 例如 `pace_profile=strength_pace`
  - 或某个固定 zone / preset 名称

第一版不一定要急着支持更复杂的参数类型。

---

## 与当前能力的关系

模板层与当前 `schedule_running_workout` 的关系应该是：

- 模板：保存“课表定义”
- 实例化：模板 + 参数 -> running workout payload
- 调度：实例化结果 -> `schedule_running_workout`

也就是说：

- 当前 `schedule_running_workout` 仍然是运行时下发入口
- 模板能力是在它之前增加一层复用能力

这也意味着，后续最自然的接口形态可能包括：

- `save_running_workout_template`
- `list_running_workout_templates`
- `render_running_workout_template`
- `schedule_running_workout_from_template`

是否需要 `update/delete/copy`，可以在模板生命周期正式立项时再细化。

---

## 当前结论

模板化是值得做的，但它属于后续增强方向，不是当前 running workout 主链路的最高优先级事项。

现阶段更合理的策略是：

1. 先把 running workout MCP 主链路补完整、补闭环
2. 再引入 running-first template lifecycle
3. 如果首批模板以汉森训练法为切入点，优先采用更收敛的 `hansons-first` 抽象

这样能同时兼顾：

- 现实可落地性
- agent 可理解性
- 后续向 CLI / skill 能力迁移的可复用性
