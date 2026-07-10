from __future__ import annotations

_SUPPORTED_TARGET_UNITS = {
    "distance": {"m"},
    "time": {"min", "sec"},
}

_PERCENT_INTENSITY_ZONE_FAMILIES = {
    "heart_rate_percent_max": {
        "recovery_zone",
        "warmup_zone",
        "fat_burn_zone",
        "aerobic_endurance_zone",
        "lactate_threshold_zone",
        "anaerobic_zone",
    },
    "heart_rate_percent_reserve": {
        "active_recovery_zone",
        "aerobic_endurance_zone",
        "aerobic_power_zone",
        "lactate_threshold_zone",
        "speed_endurance_zone",
        "anaerobic_power_zone",
    },
    "heart_rate_percent_lthr": {
        "active_recovery_zone",
        "aerobic_endurance_zone",
        "aerobic_power_zone",
        "lactate_threshold_zone",
        "speed_endurance_zone",
        "anaerobic_power_zone",
    },
    "pace_percent_lthr": {
        "active_recovery_zone",
        "aerobic_endurance_zone",
        "aerobic_power_zone",
        "lactate_threshold_zone",
        "speed_endurance_zone",
        "anaerobic_power_zone",
    },
    "effort_pace_percent_threshold": {
        "active_recovery_zone",
        "aerobic_endurance_zone",
        "aerobic_power_zone",
        "lactate_threshold_zone",
        "speed_endurance_zone",
        "anaerobic_power_zone",
    },
}

_DIRECT_NUMERIC_INTENSITY_TYPES = {
    "heart_rate",
    "pace",
    "power",
    "cadence",
    "effort_pace",
}


def is_supported_target_unit(target_type: str, unit: str | None) -> bool:
    return unit in _SUPPORTED_TARGET_UNITS.get(target_type, set())


def supported_target_units(target_type: str) -> tuple[str, ...]:
    return tuple(sorted(_SUPPORTED_TARGET_UNITS.get(target_type, set())))


def is_direct_numeric_intensity(intensity_type: str) -> bool:
    return intensity_type in _DIRECT_NUMERIC_INTENSITY_TYPES


def percent_zone_family_for(intensity_type: str) -> frozenset[str] | None:
    family = _PERCENT_INTENSITY_ZONE_FAMILIES.get(intensity_type)
    if family is None:
        return None
    return frozenset(family)
