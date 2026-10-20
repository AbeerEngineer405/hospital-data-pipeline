# Hospital Data Pipeline

## Project Overview

This project implements a reproducible hospital data engineering pipeline using Python and SQLite.

The pipeline generates synthetic hospital operations data, cleans and standardizes source records, validates data quality, checks relationships, quarantines invalid records, and loads curated data into a relational database.

The solution demonstrates core data engineering practices, including:

- Data ingestion and transformation
- Schema and data quality validation
- Relational database modeling
- Referential integrity
- Idempotent loading using SQLite UPSERT
- Second-batch processing and record corrections
- SQL analytics and operational KPIs
- Automated engineering tests
- Logging and controlled failure handling

All datasets are synthetic. No real patient information is used.

## Technology Stack

- Python 3
- SQLite
- SQL
- CSV
- Python unittest
- Python logging
- Windows PowerShell for local development and testing

The implementation uses Python's standard library and does not require third-party Python packages.

## Project Structure

```text
hospital_data_pipeline/
├── data/
│   ├── appointments.csv
│   ├── claims.csv
│   ├── support.csv
│   └── generated intermediate and curated CSV files
├── docs/
│   ├── database_design.md
│   ├── AI_PRODUCT_HANDOFF.md
│   └── AI_USAGE_DISCLOSURE.md
├── logs/
│   └── pipeline.log
├── sql/
│   └── analysis_queries.sql
├── src/
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── process_data.py
│   ├── validate_relationships.py
│   ├── data_quality.py
│   ├── database.py
│   ├── load_data.py
│   └── logger.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_failure_scenarios.py
│   └── test_second_batch.py
├── hospital.db
├── run_pipeline.py
├── FAILURE_SCENARIOS.md
└── README.md
```

## Pipeline Architecture

```text
Synthetic Data Generation
          |
          v
Data Cleaning and Deduplication
          |
          v
Record Validation and Standardization
          |
          v
Relationship Validation
          |
          v
Automated Data Quality Checks
          |
          v
SQLite Database Initialization
          |
          v
Idempotent Data Loading
          |
          v
Curated Database
          |
          v
SQL Analytics and Reporting
```

Invalid records are written to rejected or quarantined CSV files before database loading.

## Data Sources

The pipeline processes three synthetic datasets.

### Appointments

Contains appointment identifiers, patient identifiers, appointment dates, and appointment statuses.

### Claims

Contains claim identifiers, appointment references, patient identifiers, service codes, claim amounts, and claim statuses.

### Support

Contains support interaction identifiers, patient identifiers, communication channels, issue categories, interaction dates, and resolution statuses.

A patient reference table is derived from the validated records.

The synthetic data generator uses a fixed random seed to support reproducible results.

## Data Cleaning and Transformation

The processing stages perform the following operations:

- Remove duplicate source identifiers.
- Standardize accepted appointment status values.
- Validate required fields.
- Validate dates in YYYY-MM-DD format.
- Validate positive identifiers.
- Reject negative or invalid claim amounts.
- Validate accepted claim and support statuses.
- Separate valid and rejected records.
- Quarantine claims with missing or mismatched appointment relationships.

Rejected records include a reason explaining why they were excluded.

## Data Quality Framework

The pipeline performs eight categories of automated checks:

1. Schema and expected column validation.
2. Primary key uniqueness.
3. Required field completeness.
4. Identifier and numeric type/range validation.
5. Accepted status values.
6. Date format validation.
7. Claim-to-appointment relationship consistency.
8. Record count reconciliation.

The checks execute before database initialization and loading.

A data quality failure raises an error and stops the pipeline.

The database also applies primary keys, foreign keys, and a nonnegative claim amount constraint.

## Database Design

The curated SQLite database contains four tables:

| Table | Purpose | Primary Key |
|---|---|---|
| patients | Patient reference identifiers | patient_id |
| appointments | Appointment activity | appointment_id |
| claims | Claim and financial activity | claim_id |
| support | Patient support interactions | interaction_id |

Relationships:

- One patient can have multiple appointments.
- One patient can have multiple claims.
- One patient can have multiple support interactions.
- One appointment can have multiple claims.

Foreign key constraints are enabled during database operations.

The complete entity relationship diagram, column definitions, and design decisions are documented in:

`docs/database_design.md`

## Assumptions

The following assumptions were made for this assessment:

- All input records are synthetic.
- Identifiers are positive integers.
- Appointment and support dates use the YYYY-MM-DD format.
- Claim amounts must be nonnegative.
- Only predefined status values are accepted.
- Claims must reference an existing valid appointment.
- A claim's patient identifier must match the referenced appointment's patient identifier.
- Invalid records are quarantined rather than silently loaded.
- Primary keys identify records for insert-or-update behavior.
- Records absent from a later batch are not automatically deleted from the database.

## Idempotency and Second-Batch Processing

The loader uses SQLite UPSERT operations.

New records are inserted, while existing records with matching primary keys are updated with the latest validated values.

Running the loader repeatedly with unchanged curated data does not create duplicate records.

A dedicated automated test simulates a second batch by:

1. Loading an initial dataset into an isolated test database.
2. Adding a new appointment.
3. Correcting the status of an existing appointment.
4. Loading the modified dataset again.
5. Verifying the new record, updated value, and foreign key integrity.

The observed test results were:

- Initial appointment count: 147
- Final appointment count: 148
- New appointment ID: 1150
- Corrected appointment status: Completed
- Foreign key violations: 0

The production pipeline does not currently include a daily scheduler or persistent batch-tracking service.

The default runner regenerates the seeded synthetic source data on each execution. Incremental behavior is demonstrated through the isolated second-batch test and loader UPSERT functionality.

## Setup and Execution

### Requirements

- Python 3 installed and available from the command line
- No additional Python packages required

### 1. Open a terminal in the project directory

```powershell
cd path\to\hospital_data_pipeline
```

### 2. Run the complete pipeline

```powershell
python run_pipeline.py
```

The runner executes the following stages in order:

1. `generate_data.py`
2. `clean_data.py`
3. `process_data.py`
4. `validate_relationships.py`
5. `data_quality.py`
6. `database.py`
7. `load_data.py`

Successful execution ends with:

```text
Hospital data pipeline completed successfully.
```

### 3. Run automated tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### 4. Review logs

```powershell
Get-Content .\logs\pipeline.log -Tail 20
```

### 5. Review SQL analytics

Open:

`sql/analysis_queries.sql`

Execute the queries against the generated `hospital.db` SQLite database.

## Observed Validation Results

The following record counts were observed during local execution:

| Table | Loaded Records |
|---|---:|
| patients | 50 |
| appointments | 147 |
| claims | 144 |
| support | 147 |
| **Total** | **488** |

Three claims with invalid appointment relationships were quarantined before loading.

These counts represent the supplied deterministic synthetic dataset.

## Automated Testing

The latest local test run completed with:

**6 tests passed, 0 failures.**

The engineering test suite verifies:

- Execution using the active Python interpreter.
- Correct pipeline stage ordering.
- Pipeline termination when a stage fails.
- Detection of unexpected schema changes.
- Detection of negative claim amounts.
- Second-batch insertion, record correction, and referential integrity.

These engineering tests complement the eight automated data quality check categories.

## Controlled Failure Scenarios

Two controlled failure scenarios are included:

**Scenario 1: Schema drift**

A required column is renamed unexpectedly.

Expected behavior: schema validation detects the missing expected column and raises an error.

**Scenario 2: Invalid claim amount**

A negative claim amount is introduced.

Expected behavior: data quality validation detects the invalid amount and raises an error.

The scenarios are documented in:

`FAILURE_SCENARIOS.md`

## SQL Analytics

Seven analytical SQL queries are included in:

`sql/analysis_queries.sql`

They cover:

1. Appointment status distribution.
2. Claim counts and financial summaries.
3. Claims joined to appointment statuses.
4. Support interactions by issue and resolution status.
5. Appointment completion rate as an operational KPI.
6. Data quality investigation of claim relationships.
7. Top 10 patients by appointment count.

All seven queries executed successfully during local verification.

The claim relationship investigation returned zero invalid relationships in the curated database.

## Logging and Error Handling

Pipeline events are recorded in:

`logs/pipeline.log`

Logs include timestamps, processing information, record counts, and failures.

The runner uses fail-fast execution: if a required stage fails, downstream stages are not executed.

Invalid records are retained separately for investigation.

## AI and Product Handoff

Potential downstream applications include:

- Appointment completion monitoring.
- Claim and financial analysis.
- Support issue trend reporting.
- Future AI-assisted operational analytics.

These applications are potential uses of the curated data, not deployed AI features.

Additional details are available in:

`docs/AI_PRODUCT_HANDOFF.md`

## Limitations

- The project uses synthetic data only.
- SQLite is used for local demonstration rather than enterprise-scale ingestion.
- The default pipeline generates synthetic source files instead of connecting to external systems.
- Daily scheduling and persistent batch metadata are not implemented.
- Date values are stored as validated ISO-formatted text.
- Production authentication, authorization, and data governance are not implemented.
- The solution has not been deployed to a production healthcare environment.

## Production Migration Plan

A production implementation could include:

1. External source ingestion through secure APIs or managed storage.
2. Centralized configuration and environment variables.
3. Scheduled orchestration with batch tracking and retry policies.
4. A managed relational database such as PostgreSQL.
5. Automated CI/CD pipelines and regression testing.
6. Data quality monitoring, alerts, and lineage tracking.
7. Secure access controls, audit logging, and privacy safeguards.
8. Scalable processing and partitioning for larger datasets.

## AI and Development Tools Disclosure

The development tools and AI assistance used during the assessment are documented in:

`docs/AI_USAGE_DISCLOSURE.md`

## Conclusion

This project demonstrates foundational data engineering capabilities through synthetic data ingestion, transformation, validation, relational modeling, automated testing, SQL analytics, logging, and repeatable database loading.

The implementation emphasizes reproducibility, traceability, data integrity, and controlled failure handling.