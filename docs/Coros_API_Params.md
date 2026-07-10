# Coros API 参数详解

> 来源：逆向分析用户创建的校准课程（"这是我设置的校准课程"，2026-07-14）
> 和 Coros 官方的 Training Hub API 响应。
>
> 原始抓包样本保存在 [docs/exercises.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/exercises.md)。

---

## exercise 对象的完整字段

```json
{
  "id": 1,
  "name": "T1120",
  "exerciseType": 1,
  "sportType": 1,
  "targetType": 5,
  "targetValue": 300000,
  "intensityType": 3,
  "intensityValue": 300000,
  "intensityValueExtend": 360000,
  "intensityMultiplier": 1000,
  "intensityDisplayUnit": "1",
  "hrType": 0,
  "restType": 3,
  "restValue": 0,
  "groupId": "",
  "isGroup": false,
  "sets": 1,
  "sortNo": 1,
  "isIntensityPercent": false,
  "intensityPercent": 74000,
  "intensityPercentExtend": 88000,
  "overview": "sid_run_warm_up_dist"
}
```

---

## exerciseType — 步骤类型

| 值 | 含义 | 说明 |
|----|------|------|
| `0` | 组容器 | 结构行，仅用于 repeat 循环的父节点 |
| `1` | 热身（Warm-up） | App 显示"热身" |
| `2` | 训练（Main Work） | App 显示"训练"，也是循环子步骤的默认值 |
| `3` | 冷身（Cool-down） | App 显示"放松" |
| `4` | 恢复（Recovery） | App 显示"恢复"，用于间歇组内的慢跑恢复段 |

**在 `_build_workout_program_payload` 中的映射：**

```python
step["exercise_type"] = 1  # 热身
step["exercise_type"] = 2  # 训练（默认）
step["exercise_type"] = 3  # 冷身
step["exercise_type"] = 4  # 恢复（循环内慢跑恢复）
```

---

## targetType / targetValue — 目标类型和值

`targetType` 决定 `targetValue` 的单位：

| targetType | 含义 | targetValue 单位 | 示例 |
|------------|------|-----------------|------|
| `1` | 自由模式 / Open | 固定为 `0` | `targetValue=0` |
| `2` | 时间 | **秒** | `targetValue=300` → 300 秒 = 5 分钟 |
| `5` | 距离 | **厘米（cm）** | `targetValue=300000` → 300000 cm = 3000 m = 3 km |
| `6` | 负荷（Training Load） | 整数 LT/TL 值 | `targetValue=100` → 100 LT |
| `3` | 次数/组数 | 整数 | `targetValue=10` → 10 次 |

**在 `_build_workout_program_payload` 中的映射：**

```python
# 距离型（米 → 厘米）
step["target_distance_m"] = 600   # → targetType=5, targetValue=60000

# 时间型（分钟 → 秒）
step["duration_minutes"] = 2.5    # → targetType=2, targetValue=150

# 自由模式
step["open_target"] = True        # → targetType=1, targetValue=0

# 负荷目标
step["training_load"] = 100       # → targetType=6, targetValue=100
```

---

## intensityType / intensityValue — 强度类型和值

| intensityType | 含义 | intensityValue 单位 | intensityMultiplier |
|---------------|------|--------------------|--------------------|
| `0` | 无 | — | — |
| `2` | 心率（BPM） | 原始 BPM 值 | **必须 = 0** |
| `3` | 配速（秒/公里） | **intensityValue / intensityMultiplier = 秒/公里** | **必须 = 1000** |
| `8` | 等强配速（Effort Pace） | **intensityValue / intensityMultiplier = 秒/公里** | **必须 = 1000** |

### 配速格式详解

`intensityType=3` 时，`intensityMultiplier=1000` 是关键。

```
intensityValue = 240000
intensityMultiplier = 1000
─────────────────────────
intensityValue / intensityMultiplier = 240 秒/km = 4:00/km
```

**常用配速对应的 intensityValue：**

| 配速 | intensityValue (intensityMultiplier=1000) |
|------|------------------------------------------|
| 4:00/km | 240000 |
| 4:10/km | 250000 |
| 4:28/km (LT配速) | 268000 |
| 4:44/km (GMP配速) | 284000 |
| 5:00/km | 300000 |
| 5:03/km | 303000 |
| 5:40/km | 340000 |
| 6:00/km | 360000 |

**在 `_build_workout_program_payload` 中的映射：**

```python
def pace(pace_str):
    """'M:SS' → Coros intensityValue (sec/km × 1000)"""
    m, s = pace_str.split(':')
    return (int(m)*60 + int(s)) * 1000

step["pace_low_ms"] = pace("4:00")   # 240000，下限
step["pace_high_ms"] = pace("4:10")  # 250000，上限
```

### 心率格式

`intensityType=2` 时，`intensityMultiplier` 必须为 0：

```
intensityValue = 146
intensityMultiplier = 0
─────────────────────────
直接使用：146 BPM
```

### 等强配速格式

`intensityType=8` 与普通配速一样，仍然使用 `秒/公里 × 1000`：

```
intensityValue = 300000
intensityMultiplier = 1000
─────────────────────────
intensityValue / intensityMultiplier = 300 秒/km = 5:00/km
```

区别在于语义：

- `intensityType=3`：普通配速 / `%乳酸阈配速`
- `intensityType=8`：等强配速 / `%等强阈值配速`

---

## intensityDisplayUnit

**样本直接观察到的语义规律：**

| 观察值 | 含义 |
|--------|------|
| `1` / `"1"` | 配速类 / 等强配速类强度展示 |
| `0` / `"0"` | 无强度、心率类、步频类展示 |

- `intensityType in (3, 8)` 时，样本里对应配速 / 等强配速展示
- `intensityType == 2` 时，样本里对应心率 / 心率百分比展示
- `intensityType in (0, 7)` 时，样本里对应无强度 / 步频展示
- 样本本身同时出现过数字 `0/1` 和字符串 `"0"/"1"`，因此这里只能确认语义对应关系，不能仅从样本推出字段一定永远是字符串

**当前 MCP 实现策略：**

- 编译器固定输出字符串 `"1"`（配速 / 等强配速）和 `"0"`（无强度 / 心率 / 步频）
- 这是一种稳定化输出策略，不等于样本对字段类型的直接证明

---

## hrType

| 值 | 含义 |
|----|------|
| `0` | 非心率型 |
| `1` | `%最大心率` |
| `2` | `%储备心率` |
| `3` | `%乳酸阈心率` |

**补充说明：**

- `docs/exercises.md` 已直接证明 `1 / 2 / 3` 分别对应 `%最大心率 / %储备心率 / %乳酸阈心率`
- 当前代码实现中，绝对心率 `heart_rate` 也沿用 `hrType=2`，但这属于实现策略，不是本样本文件单独证明出来的结论

---

## restType / restValue — 组间休息

这两个字段仅在 **repeat 循环组**（`isGroup=true` 的父节点）上有意义。

### restType — 休息类型

| restType | 含义 |
|----------|------|
| `0` | **停顿计时** — 循环之间停顿 `restValue` 秒 |
| `1` | **动作型休息** — 下一个动作开始前等待 `restValue` 秒（力量训练用） |
| `3` | **无自动休息** — 子步骤之间不插自动恢复（用于间歇的"训练→恢复"连续进行） |

### restValue — 休息时长（秒）

- `restType=0` 且 `restValue=30` → 每组之间停顿 30 秒
- `restType=3` → `restValue` 忽略

### 示例：8×600m 间歇

```
Group (restType=0, restValue=30)    ← 每组间停顿30秒
  子步骤1: 600m 训练 (restType=3, restValue=0)   ← 无自动恢复
  子步骤2: 400m 恢复 (restType=3, restValue=0)   ← 无自动恢复
```

---

## groupId / isGroup — 循环组结构

| 字段 | 父节点（Group） | 子步骤 |
|------|----------------|--------|
| `isGroup` | `true` | `false` |
| `groupId` | `"0"` | 父节点的 `id`（字符串） |

**父节点（Group）本身：**
- `exerciseType=0`
- 当前实现里，纯结构组头使用 `targetType=0, targetValue=0`
- 如果一轮间歇的 work/recovery 都是时间目标，当前实现会把组头汇总成 `targetType=2, targetValue=单轮总秒数`
- `sets` = 循环次数（repeat）
- `restType/restValue` = 组间休息

**子步骤：**
- `groupId` = 父节点 `id`（字符串）
- 每个子步骤可以是不同的 `targetType`

---

## intensityPercent / intensityPercentExtend

当 workout 使用百分比强度区间（如乳酸阈配速的 94%~102%）时使用：

| 字段 | 含义 |
|------|------|
| `intensityPercent` | 强度下限（百分比 × 1000） |
| `intensityPercentExtend` | 强度上限（百分比 × 1000） |
| `isIntensityPercent` | 是否为百分比模式 |

**注意：** 使用配速或心率绝对值时（`pace_low_ms` / `pace_high_ms`），这些字段填 0 即可。

**已确认的组合：**

- `%最大心率 / %储备心率 / %乳酸阈心率`
  - `intensityType=2`
  - `isIntensityPercent=true`
  - `intensityPercent / intensityPercentExtend` 填百分比
  - 原始样本中 `intensityValue / intensityValueExtend` 会同时出现系统换算后的 BPM
  - 当前 MCP 实现为了避免引入用户阈值依赖，统一写 `0`
- `%乳酸阈配速`
  - `intensityType=3`
  - `isIntensityPercent=true`
  - `intensityPercent / intensityPercentExtend` 填百分比
  - 原始样本中 `intensityValue / intensityValueExtend` 会同时出现系统换算后的 sec/km
  - 当前 MCP 实现统一写 `0`
- `%等强阈值配速`
  - `intensityType=8`
  - `isIntensityPercent=true`
  - `intensityPercent / intensityPercentExtend` 填百分比
  - 原始样本中 `intensityValue / intensityValueExtend` 会同时出现系统换算后的 sec/km
  - 当前 MCP 实现统一写 `0`
- `等强配速`
  - `intensityType=8`
  - `isIntensityPercent=false`
  - `intensityValue / intensityValueExtend` 直接存 sec/km × 1000

---

## 完整 step 参数对照表

调用 `_build_workout_program_payload(steps=[...])` 时，`step` dict 支持以下字段：

### 普通步骤（无 repeat）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | str | 步骤名称 | `"热身跑 3km"` |
| `target_distance_m` | int | 距离目标（米），targetType=5 | `3000` |
| `duration_minutes` | float | 时间目标（分钟），targetType=2 | `10` |
| `pace_low_ms` | int | 配速下限（秒/km × 1000） | `pace("5:00")` → `300000` |
| `pace_high_ms` | int | 配速上限 | `pace("6:00")` → `360000` |
| `intensity_low` | int | 心率下限（BPM，intMult=0） | `140` |
| `intensity_high` | int | 心率上限 | `155` |
| `exercise_type` | int | 1=热身 2=训练 3=冷身 4=恢复 | `1` |
| `rest_type` | int | 组间休息类型（见 restType 表） | `3` |
| `rest_value` | int | 组间休息秒数 | `0` |

### repeat 循环步骤

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | str | 组名称 | `"600m×8"` |
| `repeat` | int | 循环次数 | `8` |
| `rest_type` | int | 组间停顿类型 | `0` |
| `rest_value` | int | 组间停顿秒数 | `30` |
| `steps` | list | 子步骤列表（同普通步骤格式） | 见下 |

### 子步骤（repeat 内部）

子步骤支持普通步骤的所有字段。推荐格式：

```python
{
    "name": "600m 间歇",
    "target_distance_m": 600,
    "pace_low_ms": pace("4:00"),
    "pace_high_ms": pace("4:10"),
    "exercise_type": 2,     # 2=训练
    "rest_type": 3,
    "rest_value": 0,
},
{
    "name": "400m 慢跑恢复",
    "target_distance_m": 400,
    "pace_low_ms": pace("5:40"),
    "exercise_type": 4,     # 4=恢复！
    "rest_type": 3,
    "rest_value": 0,
},
```

**补充：** 跑步间歇里的恢复段如果使用配速目标，Coros 显示单位也应保持公里体系：

- `intensityDisplayUnit = "1"` 代表按 `min/km` 展示配速
- `targetDisplayUnit = 1` 代表按公制距离展示步骤目标
- 不要把恢复段写成 `2`，否则 App 可能按 mile 体系展示恢复配速

---

## overview / description — 课程描述

Coros 课程列表和日历详情中显示的 `overview` 字段就是 description 参数传入的值。

| 字段 | 位置 | 用途 |
|------|------|------|
| `overview` | program 顶层 JSON | 在课程详情/日历中显示的描述文本 |

在 `_build_workout_program_payload` 中通过 `description` 参数传入，默认为空字符串。

示例：

```python
description = """本周重点：速度训练，4:00/km 配速，前3组找节奏，后5组稳速

注意事项：
- 选择操场或田径场进行，速度快时注意安全
- 组间好好休息，可以完全停下
- 如感觉体力充沛，可缓步走或慢跑"""

program = _build_workout_program_payload(name, steps, sport_type=100, intensity_type=3, description=description)
```

---

## 校验规则总结

| 检查项 | 规则 |
|--------|------|
| 配速（`intensity_type=3`） | `intensityMultiplier` 必须为 `1000` |
| 心率（`intensity_type=2`） | `intensityMultiplier` 必须为 `0` |
| 恢复段（`exercise_type=4`） | 仅用于循环子步骤 |
| 组间停顿 | `rest_type=0`，`rest_value`=秒数 |
| 循环子步骤无间隙 | `rest_type=3`（默认） |
| 距离单位 | 米 × 100 = 厘米（Coros API） |
| 配速单位 | 秒/公里（`intensityValue / 1000`） |
