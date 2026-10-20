
import csv
from datetime import datetime
from pathlib import Path

from logger import get_logger

# Project configuration
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
logger = get_logger("hospital_pipeline.data_quality")

SCHEMAS = {
    "appointments": [
        "appointment_id",
        "patient_id",
        "appointment_date",
        "status"
    ],
    "claims": [
        "claim_id",
        "appointment_id",
        "patient_id",
        "service_code",
        "amount",
        "claim_status"
    ],
    "support": [
        "interaction_id",
        "patient_id",
        "channel",
        "issue_type",
        "interaction_date",
        "resolution_status"
    ]
}

PRIMARY_KEYS = {
    "appointments": "appointment_id",
    "claims": "claim_id",
    "support": "interaction_id"
}

STATUSES = {
    "appointments": {
        "Scheduled",
        "Completed",
        "Cancelled",
        "No Show"
    },
    "claims": {
        "Submitted",
        "Approved",
        "Rejected"
    },
    "support": {
        "Escalated",
        "Pending",
        "Resolved"
    }
}


def read_csv(filename):
    """Read CSV records and preserve the source schema."""
    file_path = DATA_DIR / filename

    with file_path.open(
        newline="",
        encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


def validate_schema(dataset_name, actual_fields, expected_fields):
    """Detect missing, unexpected, or reordered CSV columns."""

    if actual_fields != expected_fields:
        missing_columns = [
            column for column in expected_fields
            if column not in (actual_fields or [])
        ]

        unexpected_columns = [
            column for column in (actual_fields or [])
            if column not in expected_fields
        ]

        message = (
            f"{dataset_name}: Schema validation failed. "
            f"Missing columns: {missing_columns}. "
            f"Unexpected columns: {unexpected_columns}. "
            f"Expected order: {expected_fields}."
        )

        logger.error("DATA QUALITY FAILED: %s", message)
        raise ValueError(message)


def run_data_quality_checks():
    """Execute eight categories of data quality validation."""

    failures = []
    datasets = {}

    for name in SCHEMAS:
        fields, records = read_csv(f"{name}_valid.csv")

        # Check 1: Validate expected schema
        validate_schema(name, fields, SCHEMAS[name])

        datasets[name] = records

        # Check 2: Validate primary key uniqueness
        key = PRIMARY_KEYS[name]

        identifiers = [
            row.get(key)
            for row in records
        ]

        if len(identifiers) != len(set(identifiers)):
            failures.append(
                f"{name}: Duplicate primary keys"
            )

        # Check 3: Validate required values
        for index, row in enumerate(records, start=2):
            for field in SCHEMAS[name]:
                value = row.get(field)

                if not str(value or "").strip():
                    failures.append(
                        f"{name}: Missing {field} at CSV row {index}"
                    )

        # Check 4: Validate identifier and amount types
        for index, row in enumerate(records, start=2):

            id_fields = [
                field for field in SCHEMAS[name]
                if field.endswith("_id")
            ]

            for field in id_fields:
                try:
                    if int(row[field]) <= 0:
                        raise ValueError

                except (ValueError, TypeError, KeyError):
                    failures.append(
                        f"{name}: Invalid {field} at CSV row {index}"
                    )

            if name == "claims":
                try:
                    amount = float(row["amount"])

                    if not 0 <= amount < float("inf"):
                        raise ValueError

                except (ValueError, TypeError, KeyError):
                    failures.append(
                        f"claims: Invalid amount at CSV row {index}"
                    )

        # Check 5: Validate accepted status values
        status_field = {
            "appointments": "status",
            "claims": "claim_status",
            "support": "resolution_status"
        }[name]

        for index, row in enumerate(records, start=2):
            if row.get(status_field) not in STATUSES[name]:
                failures.append(
                    f"{name}: Invalid status at CSV row {index}"
                )

        # Check 6: Validate date formats and calendar dates
        if name in ("appointments", "support"):
            date_field = (
                "appointment_date"
                if name == "appointments"
                else "interaction_date"
            )

            for index, row in enumerate(records, start=2):
                try:
                    value = row[date_field]

                    parsed = datetime.strptime(
                        value,
                        "%Y-%m-%d"
                    )

                    if parsed.strftime("%Y-%m-%d") != value:
                        raise ValueError

                except (ValueError, TypeError, KeyError):
                    failures.append(
                        f"{name}: Invalid date at CSV row {index}"
                    )

    # Check 7: Validate claim-to-appointment relationships
    appointment_patients = {
        row["appointment_id"]: row["patient_id"]
        for row in datasets["appointments"]
    }

    ready_fields, ready_claims = read_csv(
        "claims_ready.csv"
    )

    validate_schema(
        "claims_ready",
        ready_fields,
        SCHEMAS["claims"]
    )

    for claim in ready_claims:
        expected_patient = appointment_patients.get(
            claim["appointment_id"]
        )

        if expected_patient is None:
            failures.append(
                f"Claim {claim['claim_id']}: Missing valid appointment"
            )

        elif expected_patient != claim["patient_id"]:
            failures.append(
                f"Claim {claim['claim_id']}: Patient mismatch"
            )

    # Check 8: Validate row-count reconciliation
    for name in SCHEMAS:
        _, cleaned = read_csv(
            f"{name}_cleaned.csv"
        )

        _, valid = read_csv(
            f"{name}_valid.csv"
        )

        _, rejected = read_csv(
            f"{name}_rejected.csv"
        )

        if len(cleaned) != len(valid) + len(rejected):
            failures.append(
                f"{name}: Cleaned/valid/rejected count mismatch"
            )

    _, orphaned_claims = read_csv(
        "claims_orphaned.csv"
    )

    if len(datasets["claims"]) != (
        len(ready_claims) + len(orphaned_claims)
    ):
        failures.append(
            "claims: Ready/quarantined count mismatch"
        )

    # Stop the pipeline when validation fails
    if failures:
        for failure in failures:
            logger.error(
                "DATA QUALITY FAILED: %s",
                failure
            )

        raise ValueError(
            f"Data quality validation failed: "
            f"{len(failures)} issue(s)"
        )

    logger.info(
        "All 8 data quality check categories passed"
    )

    logger.info(
        "Validated records: appointments=%d, claims=%d, support=%d",
        len(datasets["appointments"]),
        len(ready_claims),
        len(datasets["support"])
    )


if __name__ == "__main__":
    run_data_quality_checks()
