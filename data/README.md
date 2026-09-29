# ORCA Marine Data

This directory contains external marine datasets used by ORCA.

## Raw Data

`raw/` contains original downloaded datasets.

Raw datasets must never be modified.

## Processed Data

`processed/` contains reduced/normalized datasets generated from raw sources.

## Metadata

`metadata/` contains dataset descriptions, variable mappings, provenance and ingestion metadata.

## Initial Data Sources

- Ocean: INCOIS HYCOM — downloading
- Wind: Not downloaded yet
- Waves: Not downloaded yet
- PFZ: Not downloaded yet
- SST: Not downloaded yet
- Chlorophyll: Not downloaded yet

## Data Integrity Rule

Do not fabricate marine data.

Every processed dataset must preserve:
- source
- dataset name
- acquisition date
- forecast/observation time
- geographic coverage
- variable names
- units
- whether data is simulated

## Current Status

The first INCOIS HYCOM ocean dataset is currently downloading.

No ingestion or transformation should happen until the raw dataset has been inspected.
