from __future__ import annotations


def composite_index_methodology() -> str:
    return (
        "Temporal factor = target_value / base_value. "
        "Weighted composite = sum(weight * temporal_factor). "
        "Percent change = (factor - 1) * 100."
    )


def locality_adjustment_methodology() -> str:
    return (
        "Locality factor = target_locality_wage / reference_locality_wage. "
        "This is separate from the temporal factor and is normally "
        "defaulted to 1.0 unless explicitly applied."
    )
