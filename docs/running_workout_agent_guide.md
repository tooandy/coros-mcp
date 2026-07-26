# Running Workout Agent Guide

本文档面向 LLM / agent 使用 `coros-mcp` 创建、预览、校验和下发跑步课表。

它是操作型文档：优先说明怎么选工具、怎么组织输入、哪些组合合法、编译后会映射到哪些 COROS 字段。

详细 wire 字段背景见 [Coros_API_Params.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/Coros_API_Params.md)。

---

## 工具选择

优先按这个顺序使用 running-first 工具：

| 场景 | 工具 | 是否写入 COROS |
|------|------|----------------|
| 想先看完整结果 | `preview_running_workout` | 否 |
| 只想检查输入是否合法 | `validate_running_workout` | 否 |
| 只想看人类可读摘要 | `render_running_workout` | 否 |
| 只想看 COROS payload | `compile_running_workout` | 否 |
| 确认无误后写入日历 | `schedule_running_workout` | 是 |

推荐默认流程：

1. 先调用 `preview_running_workout`
2. 检查 `ok == true`、`valid == true`
3. 检查 `rendered_summary`
4. 必要时检查 `program.exercises`
5. 最后再调用 `schedule_running_workout`

只读工具不需要认证、不触网、不写日历。

---

## 顶层输入结构

所有 running-first 工具都使用同一组语义字段：

```json
{
  "name": "4x1km LT",
  "description": "Threshold repeats",
  "happen_day": "20260715",
  "sort_no": 1,
  "steps": []
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 课表名称 |
| `happen_day` | 是 | 日期，格式 `YYYYMMDD` |
| `steps` | 是 | 非空步骤列表 |
| `description` | 否 | 写入 workout overview |
| `sort_no` | 否 | 同一天内排序，默认 `1` |

---

## 节点类型

`steps` 中支持两种 node：

| kind | 含义 | 结构 |
|------|------|------|
| `step` | 普通动作 | 一个 `action + target + intensity` |
| `interval` | 间歇组 | `repeat + work + recovery` |

### 普通 step

```json
{
  "kind": "step",
  "action": "warmup",
  "target": {"type": "time", "value": 15, "unit": "min"},
  "intensity": {"type": "none"}
}
```

### interval

```json
{
  "kind": "interval",
  "repeat": 4,
  "work": {
    "action": "work",
    "target": {"type": "distance", "value": 1000, "unit": "m"},
    "intensity": {
      "type": "pace_percent_lthr",
      "zone": {"preset": "lactate_threshold_zone"}
    }
  },
  "recovery": {
    "action": "recovery",
    "target": {"type": "distance", "value": 400, "unit": "m"},
    "intensity": {"type": "none"}
  }
}
```

当前 `interval` 固定为 `work + recovery` 两段。`repeat` 必须是整数且 `>= 1`。

---

## 动作矩阵

| action | COROS `exerciseType` | 允许位置 | 说明 |
|--------|----------------------|----------|------|
| `warmup` | `1` | 普通 step | 热身 |
| `work` | `2` | 普通 step、interval.work | 训练 |
| `recovery` | `4` | 普通 step、interval.recovery | 恢复 |
| `cooldown` | `3` | 普通 step | 放松 |

interval 内有额外校验：

- `work.action` 必须是 `work`
- `recovery.action` 必须是 `recovery`

---

## 目标矩阵

| target.type | 输入要求 | COROS `targetType` | COROS `targetValue` | 说明 |
|-------------|----------|--------------------|---------------------|------|
| `distance` | `value` 数字，`unit: "m"` | `5` | 米 × 100 | COROS 使用厘米 |
| `time` | `value` 数字，`unit: "min"` 或 `"sec"` | `2` | 秒 | `min` 会乘以 60 |
| `training_load` | `value` 整数，不允许 `unit` | `6` | 原整数 | 例如 `100 TL` |
| `open` | 不允许 `value`，不允许 `unit` | `1` | `0` | 自由模式 |

示例：

```json
{"type": "distance", "value": 1000, "unit": "m"}
```

```json
{"type": "time", "value": 5, "unit": "min"}
```

```json
{"type": "training_load", "value": 100}
```

```json
{"type": "open"}
```

---

## 强度输入形态

强度分三类：

| 形态 | 适用类型 | 输入字段 |
|------|----------|----------|
| 无强度 | `none` | 不带 `range` / `zone` |
| 直接数值区间 | `heart_rate`、`pace`、`effort_pace`、`power`、`cadence` | `range.low` + `range.high` |
| 百分比强度 | `heart_rate_percent_max`、`heart_rate_percent_reserve`、`heart_rate_percent_lthr`、`pace_percent_lthr`、`effort_pace_percent_threshold` | `zone` 或 `range` |

直接数值强度不支持开区间。必须给出 `low` 和 `high`。

百分比强度支持两种写法：

```json
{
  "type": "pace_percent_lthr",
  "zone": {"preset": "lactate_threshold_zone"}
}
```

```json
{
  "type": "pace_percent_lthr",
  "range": {"low": 95, "high": 100}
}
```

---

## 强度矩阵

| intensity.type | 输入方式 | COROS `intensityType` | 关键字段 | 单位 |
|----------------|----------|-----------------------|----------|------|
| `none` | 无 | `0` | `isIntensityPercent=false` | 无 |
| `heart_rate_percent_max` | `zone` 或百分比 `range` | `2` | `hrType=1`, `isIntensityPercent=true` | 百分比 × 1000 |
| `heart_rate_percent_reserve` | `zone` 或百分比 `range` | `2` | `hrType=2`, `isIntensityPercent=true` | 百分比 × 1000 |
| `heart_rate_percent_lthr` | `zone` 或百分比 `range` | `2` | `hrType=3`, `isIntensityPercent=true` | 百分比 × 1000 |
| `heart_rate` | 直接数值 `range` | `2` | `hrType=2`, `isIntensityPercent=false` | BPM |
| `pace_percent_lthr` | `zone` 或百分比 `range` | `3` | `hrType=0`, `isIntensityPercent=true` | 百分比 × 1000 |
| `pace` | 直接数值 `range` | `3` | `hrType=0`, `isIntensityPercent=false` | 秒/公里 × 1000 |
| `effort_pace_percent_threshold` | `zone` 或百分比 `range` | `8` | `hrType=0`, `isIntensityPercent=true` | 百分比 × 1000 |
| `effort_pace` | 直接数值 `range` | `8` | `hrType=0`, `isIntensityPercent=false` | 秒/公里 × 1000 |
| `power` | 直接数值 `range` | `6` | `hrType=0`, `isIntensityPercent=false` | W |
| `cadence` | 直接数值 `range` | `7` | `hrType=0`, `isIntensityPercent=false` | spm |

配速数值换算：

| 配速 | range 值 |
|------|----------|
| `4:00/km` | `240000` |
| `5:00/km` | `300000` |
| `6:00/km` | `360000` |

公式：

```text
秒/公里 × 1000
```

---

## Zone 矩阵

### `%最大心率`

仅 `heart_rate_percent_max` 支持下面这些 preset：

| preset | 默认百分比 |
|--------|------------|
| `recovery_zone` | `50-60` |
| `warmup_zone` | `60-70` |
| `fat_burn_zone` | `70-80` |
| `aerobic_endurance_zone` | `80-87` |
| `lactate_threshold_zone` | `87-93` |
| `anaerobic_zone` | `93-100` |

### 阈值家族

下面这些 intensity 共用同一组 preset：

- `heart_rate_percent_reserve`
- `heart_rate_percent_lthr`
- `pace_percent_lthr`
- `effort_pace_percent_threshold`

| preset | 默认百分比 |
|--------|------------|
| `active_recovery_zone` | `80-88` |
| `aerobic_endurance_zone` | `88-95` |
| `aerobic_power_zone` | `95-100` |
| `lactate_threshold_zone` | `100-105` |
| `speed_endurance_zone` | `105-115` |
| `anaerobic_power_zone` | `115-130` |

说明：

- 以上百分比表来自当前代码实现。
- 如果后续抓包证明 COROS 对不同 threshold family 使用不同默认边界，需要同步更新代码、测试和本文档。
- `zone.preset: "custom"` 时必须提供 `low` 和 `high`，例如 `{"preset": "custom", "low": 92, "high": 96}`。

---

## interval 编译规则

interval 会编译成：

- 一个 group 父节点
- 一个 work 子步骤
- 一个 recovery 子步骤

父节点规则：

| 情况 | group `targetType` | group `targetValue` |
|------|--------------------|---------------------|
| work 和 recovery 都是时间目标 | `2` | 单轮总秒数 |
| 其他情况 | `0` | `0` |

子步骤规则：

- `work` 子步骤使用 `exerciseType=2`
- `recovery` 子步骤使用 `exerciseType=4`
- 子步骤 `groupId` 指向父节点 `id`

---

## 结果检查清单

agent 在调用 `preview_running_workout` 后，建议检查：

- `ok == true`
- `valid == true`
- `rendered_summary` 是否符合用户意图
- `program.overview` 是否包含期望的 description
- `program.exercises` 中 step 数量是否正确
- interval recovery 是否为 `exerciseType=4`
- distance target 是否为 `targetType=5`
- time target 是否为 `targetType=2`
- open target 是否为 `targetType=1`
- training load target 是否为 `targetType=6`
- 配速类是否为 `intensityType=3`
- 等强配速类是否为 `intensityType=8`
- 心率类是否为 `intensityType=2`

确认后再调用 `schedule_running_workout`。

---

## 常见错误

| 错误 | 原因 | 修正 |
|------|------|------|
| `open target must not include value` | `open` 带了 `value` | 改成 `{"type": "open"}` |
| `training_load target requires integer value` | `training_load` 不是整数 | 使用整数，例如 `100` |
| `training_load target must not include unit` | `training_load` 带了 `unit` | 删除 `unit` |
| `zone is only supported for percent-based intensity types` | 直接数值强度用了 `zone` | 改用 `range` |
| `percent-based intensity types require range or zone` | 百分比强度没有给区间 | 添加 `zone` 或百分比 `range` |
| `open-ended intensity range ... not yet supported` | 直接数值强度只给了 `low` | 同时给 `low` 和 `high` |
| `interval work.action must be 'work'` | interval work 动作不是 `work` | 改成 `action: "work"` |
| `interval recovery.action must be 'recovery'` | interval recovery 动作不是 `recovery` | 改成 `action: "recovery"` |

---

## 完整示例

```json
{
  "name": "4x1km LT",
  "description": "Threshold repeats",
  "happen_day": "20260715",
  "sort_no": 1,
  "steps": [
    {
      "kind": "step",
      "action": "warmup",
      "target": {"type": "time", "value": 15, "unit": "min"},
      "intensity": {"type": "none"}
    },
    {
      "kind": "interval",
      "repeat": 4,
      "work": {
        "action": "work",
        "target": {"type": "distance", "value": 1000, "unit": "m"},
        "intensity": {
          "type": "pace_percent_lthr",
          "zone": {"preset": "lactate_threshold_zone"}
        }
      },
      "recovery": {
        "action": "recovery",
        "target": {"type": "distance", "value": 400, "unit": "m"},
        "intensity": {"type": "none"}
      }
    },
    {
      "kind": "step",
      "action": "cooldown",
      "target": {"type": "time", "value": 10, "unit": "min"},
      "intensity": {"type": "none"}
    }
  ]
}
```

建议先调用：

```text
preview_running_workout
```

确认结果后再调用：

```text
schedule_running_workout
```
