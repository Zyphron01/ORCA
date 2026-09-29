# Phase 9: SAR Engine Completion Report

## 1. Existing SAR implementation
Before Phase 9, `packages/sar_physics/predict.py` contained a rudimentary mock drift calculation. The previous implementation:
- Used a simple Euler integration scheme (despite the filename being `rk4.py`).
- Combined wind and current directly but did not expose components.
- Lacked true numerical stability and failed when given floating-point edge cases.
- Did not export structured breakdowns of environmental vectors or a strict JSON schema for prediction horizons.

## 2. New SAR engine architecture
Phase 9 radically upgrades the mathematical and structural integrity of the SAR predictions:
- Replaced the simple Euler loop with a true 4-stage Runge-Kutta (RK4) integration algorithm evaluating intermediate drift velocity and position.
- Calculates explicit Vector Components for Ocean Current, Windage (Leeway), and Stokes Drift.
- Implements proper spherical coordinate stepping, safeguarding against singularity limits near poles (`abs(cos(lat)) < 1e-4`).
- Outputs structured `predictions` arrays targeting T+1, T+3, and T+6 hours dynamically.

## 3. Drift equations/model assumptions
- **Current Drift**: Fully applied based on ocean provider velocity and direction.
- **Windage/Leeway**: Approximated at 3% of total wind speed applied to the wind direction.
- **Stokes Drift**: Approximated at 1% of wind speed, active only when significant wave height is > 0.0m.

## 4. RK4 implementation
The integration uses a 0.25-hour (15 minute) discrete timestep. At each step, it accumulates four derivative evaluations (`k1`, `k2`, `k3`, `k4`) representing localized velocity vectors across the geographic plane. These are merged using standard Runge-Kutta fractional weighting (1/6, 1/3, 1/3, 1/6) to advance the latitude and longitude.

## 5. Environmental factors
The model correctly extracts environmental factors from the simulated data providers (Wind Speed/Dir, Wave Height, Current Speed/Dir) and merges them in the `compute_velocity` function to calculate the net trajectory vector.

## 6. Prediction horizons
Regardless of intermediate timesteps, the engine strictly outputs the coordinates at `1`, `3`, and `6` hours (or until requested duration). The output format clearly defines the exact `horizon_hours` for each entry.

## 7. Search-area representation
Search areas are represented by dynamic circles defined by the predicted `position` (center) and an `uncertainty_radius_nm` which scales based on integration time and starting drift velocity (Base 0.5nm + 5% of velocity per hour). 

## 8. Uncertainty assumptions
The uncertainty expansion assumes a deterministic drift error of 5% applied linearly over time plus a fixed 0.5nm baseline inaccuracy parameter.

## 9. ORCA integration
The `calculate_drift_prediction` tool in `orca_core/tools.py` was refactored to parse the new rich JSON schema returned by `predict_drift`. The tool surfaces the comprehensive SAR payload, allowing the LLM supervisor to read the `drift_components`, reason over uncertainty expansion, and present the final search radius and position.

## 10. SOS compatibility
The existing `sos.py` routers inherently rely on the `predict_drift` logic via the overarching application. Updating the core `rk4.py` implementation natively improves the physics calculation of the ongoing Phase 10 simulator without requiring interface changes in the API.

## 11. Tests
- Created `apps/api/tests/test_phase9_sar.py`.
- Tested explicit velocity combinations (zero drift, current-only, wind-only), invalid numerical input trapping (NaNs), horizon generation, structured JSON payload matching, and Search Cone generation.
- Corrected and updated previous Phase 4 SAR tests in `test_phase4.py` and `test_orca_supervisor.py` to match the new robust payload shape.

## 12. Test results
- `pytest -q` resulted in `64 passed` out of 64 selected tests.

## 13. Build result
- Frontend Vite + TSC build ran successfully via `npm run build`.

## 14. Simulated vs real data
- The inputs and outputs strictly respect `is_simulated: True`. The environmental constraints are passed in from the deterministic mock providers.

## 15. Known limitations
- The environmental field assumes constant wind and current over the horizon because the deterministic mock provider returns a single localized forecast rather than a spatio-temporal grid.

## 16. Files changed
- `packages/sar_physics/rk4.py` (Modified - implemented true RK4 and physics vectors)
- `packages/orca_core/tools.py` (Modified - updated drift prediction tool schema)
- `apps/api/tests/test_phase4.py` (Modified - fixed legacy test assertions)
- `apps/api/tests/test_orca_supervisor.py` (Modified - fixed tool test assertions)
- `apps/api/tests/test_phase9_sar.py` (New - robust unit tests for new physics engine)
- `docs/Phase9_SAR_Engine_Completion.md` (New - this report)
