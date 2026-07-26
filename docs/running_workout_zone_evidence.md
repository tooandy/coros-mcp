# Running Workout Zone Evidence

本文档记录跑步课表百分比强度 zone 的证据状态。

目标是把 `type × zone × low/high` 从“代码里有一张表”推进到“知道哪些来自样本，哪些仍是待验证实现假设”。

原始样本来源：

- [exercises.md](/Users/aniss/Documents/Marathon/coros-mcp/docs/exercises.md)

---

## 证据等级

| 等级 | 含义 |
|------|------|
| 样本已标注 | `docs/exercises.md` 中有中文强度名，并能直接对应 percent payload |
| 样本未标注 | 有 percent payload，但样本片段没有写出具体 zone 名称 |
| 当前实现假设 | 代码中已有映射，但还缺直接样本标注 |

---

## 样本已标注

### `%乳酸阈配速 × 有氧动力区`

语义类型：

- `pace_percent_lthr`

zone preset：

- `aerobic_power_zone`

样本证据：

- “强度: %乳酸阈配速 有氧动力区”
- `intensityType=3`
- `intensityCustom=2`
- `intensityPercent=85100`
- `intensityPercentExtend=92600`

结论：

- 默认百分比为 `85.1-92.6`

### `%等强阈值配速 × 有氧动力区`

语义类型：

- `effort_pace_percent_threshold`

zone preset：

- `aerobic_power_zone`

样本证据：

- “强度:%等强阈值配速 有氧动力区”
- `intensityType=8`
- `intensityCustom=2`
- `intensityPercent=85100`
- `intensityPercentExtend=92600`

结论：

- 默认百分比为 `85.1-92.6`

---

## 样本未标注

`docs/exercises.md` 中存在一组心率百分比样本，但该段标题只写了：

- `%最大心率`
- `%储备心率`
- `%乳酸阈心率`

没有逐条写出选择的是哪个 zone 名称。

因此这些 payload 目前只能作为候选证据，不能直接绑定到具体 preset。

| hrType | intensityCustom | intensityPercent | intensityPercentExtend | 当前可确认 |
|--------|-----------------|------------------|------------------------|------------|
| `1` | `1` | `51000` | `60000` | `%最大心率` 某 zone |
| `1` | `2` | `61000` | `70000` | `%最大心率` 某 zone |
| `1` | `3` | `71000` | `80000` | `%最大心率` 某 zone |
| `2` | `2` | `75000` | `84000` | `%储备心率` 某 zone |
| `3` | `3` | `96000` | `102000` | `%乳酸阈心率` 某 zone |

后续如果补充每条对应的中文 zone 名称，就可以把它们提升为“样本已标注”。

---

## 当前实现表

### `%最大心率`

语义类型：

- `heart_rate_percent_max`

| preset | 当前实现 | 证据状态 |
|--------|----------|----------|
| `recovery_zone` | `50-60` | 当前实现假设 |
| `warmup_zone` | `60-70` | 当前实现假设 |
| `fat_burn_zone` | `70-80` | 当前实现假设 |
| `aerobic_endurance_zone` | `80-87` | 当前实现假设 |
| `lactate_threshold_zone` | `87-93` | 当前实现假设 |
| `anaerobic_zone` | `93-100` | 当前实现假设 |

### 心率阈值家族

语义类型：

- `heart_rate_percent_reserve`
- `heart_rate_percent_lthr`

| preset | 当前实现 | 证据状态 |
|--------|----------|----------|
| `active_recovery_zone` | `80-88` | 当前实现假设 |
| `aerobic_endurance_zone` | `88-95` | 当前实现假设 |
| `aerobic_power_zone` | `95-100` | 当前实现假设 |
| `lactate_threshold_zone` | `100-105` | 当前实现假设 |
| `speed_endurance_zone` | `105-115` | 当前实现假设 |
| `anaerobic_power_zone` | `115-130` | 当前实现假设 |

### 配速阈值家族

语义类型：

- `pace_percent_lthr`
- `effort_pace_percent_threshold`

| preset | 当前实现 | 证据状态 |
|--------|----------|----------|
| `active_recovery_zone` | `80-88` | 当前实现假设 |
| `aerobic_endurance_zone` | `88-95` | 当前实现假设 |
| `aerobic_power_zone` | `85.1-92.6` | 样本已标注，已由 `pace_percent_lthr` / `effort_pace_percent_threshold` 证明 |
| `lactate_threshold_zone` | `100-105` | 当前实现假设 |
| `speed_endurance_zone` | `105-115` | 当前实现假设 |
| `anaerobic_power_zone` | `115-130` | 当前实现假设 |

---

## 后续采样清单

为了完全闭合 P2，需要继续采样：

- `%最大心率` 的全部 6 个非自定义 zone
- `%储备心率` 的全部 6 个非自定义 zone
- `%乳酸阈心率` 的全部 6 个非自定义 zone
- `%乳酸阈配速` 除 `aerobic_power_zone` 外的其他 5 个 zone
- `%等强阈值配速` 除 `aerobic_power_zone` 外的其他 5 个 zone

每条样本最好包含：

- 中文强度名
- 中文 zone 名称
- `intensityType`
- `hrType`
- `intensityCustom`
- `intensityPercent`
- `intensityPercentExtend`
- `intensityValue`
- `intensityValueExtend`
