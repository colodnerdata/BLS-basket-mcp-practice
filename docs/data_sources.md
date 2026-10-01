# Data sources

## PPI

Purpose: materials, equipment, and service price escalation over time.

This scaffold does not yet implement authoritative bulk-file field mappings or all PPI ingestion details. The loader interfaces and series models are established to support this later.

## ECI

Purpose: labor escalation over time.

This is the intended source for labor cost-curve movement between periods. The loader and service seams exist, but file-specific mapping details remain deferred.

## OEWS

Purpose: occupation and locality wage comparison for labor-rate differences across geographic areas.

The initial locality service only accepts supplied wages and calculates a factor. Full OEWS area-data mapping remains an explicit TODO.
