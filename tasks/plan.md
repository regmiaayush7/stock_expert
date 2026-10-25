# Plan: build `nepse-expert` skill, Version 3

## Context

Versions 0, 1, and 2 are complete and all 94 unit tests pass successfully. This plan covers **Version 3** of the `nepse-expert` skill as specified in `NEPSE_SKILL_BUILD_PROMPT.md` (section 9, item 4).

Version 3 adds:
- Richer forecasting models (`scripts/forecast.py`).
- Forecast evaluation and ensemble combination (`scripts/ensemble.py`).

## Version 3 Scope

1. **Forecasting Module (`scripts/forecast.py`)**:
   - Implements baseline models (naive, moving average, mean reversion, momentum) and regime detection.
   - Unit tests in `scripts/tests/test_forecast.py`.
2. **Ensemble & Forecast Combination (`scripts/ensemble.py`)**:
   - Averages independent methods and reports model disagreement as uncertainty.
   - Unit tests in `scripts/tests/test_ensemble.py`.
3. **Skill Integration & Verification (`SKILL.md`)**:
   - Update `SKILL.md` router for V3 predictive modules, sync files to `C:\Users\HP\.claude\skills\nepse-expert/`, and run all test suites.

## Dependency Graph

```
T21: Forecasting Module (forecast.py) ────────┐
T22: Ensemble Combination (ensemble.py) ──────┼──> T23: SKILL.md Integration & Verification
```

## Tasks and Acceptance Criteria

### T21: Forecasting Module (`scripts/forecast.py`)
- **Action**: Implement baseline forecasts and regime detection.
- **Test**: Write `scripts/tests/test_forecast.py`.
- **Acceptance Criteria**: Baseline forecasts and regime classifications run correctly.

### T22: Ensemble Combination (`scripts/ensemble.py`)
- **Action**: Implement forecast combination and disagreement measure.
- **Test**: Write `scripts/tests/test_ensemble.py`.
- **Acceptance Criteria**: Combines forecasts and outputs uncertainty bounds.

### T23: Skill Router Integration & Verification
- **Action**: Update `SKILL.md` for V3, sync skill folder, run all unit tests.
- **Acceptance Criteria**: All unit tests (V0 through V3) pass successfully.
