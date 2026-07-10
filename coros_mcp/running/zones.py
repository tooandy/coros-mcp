from __future__ import annotations

_MAX_HR_ZONES = {
    "recovery_zone": (50, 60),
    "warmup_zone": (60, 70),
    "fat_burn_zone": (70, 80),
    "aerobic_endurance_zone": (80, 87),
    "lactate_threshold_zone": (87, 93),
    "anaerobic_zone": (93, 100),
}

_THRESHOLD_FAMILY_ZONES = {
    "active_recovery_zone": (80, 88),
    "aerobic_endurance_zone": (88, 95),
    "aerobic_power_zone": (95, 100),
    "lactate_threshold_zone": (100, 105),
    "speed_endurance_zone": (105, 115),
    "anaerobic_power_zone": (115, 130),
}

_ZONE_FAMILY_BY_INTENSITY = {
    "heart_rate_percent_max": _MAX_HR_ZONES,
    "heart_rate_percent_reserve": _THRESHOLD_FAMILY_ZONES,
    "heart_rate_percent_lthr": _THRESHOLD_FAMILY_ZONES,
    "pace_percent_lthr": _THRESHOLD_FAMILY_ZONES,
    "effort_pace_percent_threshold": _THRESHOLD_FAMILY_ZONES,
}


def resolve_zone_range(intensity_type: str, preset: str) -> tuple[int, int]:
    family = _ZONE_FAMILY_BY_INTENSITY.get(intensity_type)
    if family is None:
        raise ValueError(f"intensity type '{intensity_type}' does not support zone presets")

    try:
        return family[preset]
    except KeyError as exc:
        raise ValueError(f"zone preset '{preset}' is invalid for intensity type '{intensity_type}'") from exc
