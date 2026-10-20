# Controlled Failure Scenarios

## Overview

This document demonstrates two controlled data quality failures using isolated temporary copies of the generated synthetic datasets. The original CSV files and SQLite database were not modified by these tests.

## Scenario 1: Schema Drift

**Injected failure:** Renamed `patient_id` to `patient_number` in `appointments_valid.csv`.

**Expected behavior:** The data quality validator must reject the unexpected schema before loading data.

**Observed result:** PASSED

The validator raised a `ValueError` and identified:

- Missing column: `patient_id`
- Unexpected column: `patient_number`
- Expected appointment schema

**Root cause:** An upstream column name changed without a corresponding update to the data contract.

**Debugging and resolution:** Compare the incoming CSV header against the expected schema. Restore the correct column name or explicitly update the schema contract and downstream transformations after review.

## Scenario 2: Negative Claim Amount

**Injected failure:** Changed a claim amount to `-500` in `claims_valid.csv`.

**Expected behavior:** The data quality validator must reject negative financial amounts.

**Observed result:** PASSED

The validator logged:

`DATA QUALITY FAILED: claims: Invalid amount at CSV row 2`

It then raised a `ValueError`, causing the controlled test to pass.

**Root cause:** An invalid negative amount was introduced into a curated claims dataset.

**Debugging and resolution:** Identify the affected claim, inspect its upstream source, and correct or quarantine the invalid record before loading. Negative claim values are not accepted under this project's current assumptions.

## Verification

Executed on October 20, 2026:

`python -m unittest discover -s tests -p "test_failure_scenarios.py" -v`

**Result:** 2 tests executed, 2 passed (`OK`).

Both scenarios use temporary CSV copies and demonstrate that invalid records are detected without changing the project's original data.

## Operational Behavior

The main pipeline executes `data_quality.py` before SQLite loading. If validation raises an exception, the pipeline stops and reports the failing stage. This prevents the current invalid batch from proceeding to the database loading step.