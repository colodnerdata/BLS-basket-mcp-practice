# Methodology

This document describes only the methodology implemented or explicitly planned in this scaffold.

## Fixed-weight composite index

A custom index is built from a fixed list of weighted components. Each component represents a cost element and an associated BLS series, with an explicit weight chosen by the specification author.

## Temporal escalation

For an indexed component:

- temporal_factor = target_value / base_value

For a fixed/unindexed component:

- temporal_factor = 1

The weighted temporal composite is:

- sum(weight * temporal_factor)

The corresponding percentage change is:

- (factor - 1) * 100

## Labor locality ratio

For labor wage comparisons:

- locality_factor = target_wage / reference_wage

This is distinct from temporal escalation. The locality factor is applied only when the component explicitly opts into locality adjustment; it is not automatically applied to all materials, equipment, or service components.

## Component-level locality

The combined component factor is:

- combined_factor = temporal_factor * locality_factor

The localized composite is:

- sum(weight * combined_factor)

The locality-adjusted result is reported separately from the temporal-only result so the two effects remain transparent.

## Why substitution and interpolation are avoided

This scaffold intentionally does not silently normalize weights, interpolate missing observations, replace discontinued series, or apply automatic locality adjustments. Those changes are significant methodology decisions and must be controlled through explicit policies.
