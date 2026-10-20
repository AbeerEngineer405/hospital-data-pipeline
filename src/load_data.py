from contextlib import closing
import csv
import sqlite3
from pathlib import Path

from database import DB_PATH, create_database
from logger import get_logger

# Configure project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

logger = get_logger("hospital_pipeline.load_data")


def read_csv(filename):
    """Read validated records from a CSV file."""
    file_path = DATA_DIR / filename

    with open(file_path, newline="", encoding="utf-8-sig") as file:
        records = list(csv.DictReader(file))

    logger.info("Read %d records from %s", len(records), filename)
    return records


def load_data():
    """Load validated hospital records using idempotent UPSERT operations."""

    logger.info("Starting hospital data loading")

    try:
        create_database()

        appointments = read_csv("appointments_valid.csv")
        claims = read_csv("claims_ready.csv")
        support_records = read_csv("support_valid.csv")

        # Collect unique patient identifiers
        patient_ids = {
            int(record["patient_id"])
            for record in appointments + claims + support_records
        }

        with closing(sqlite3.connect(DB_PATH)) as conn, conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert patient reference records
            conn.executemany(
                """
                INSERT INTO patients (patient_id)
                VALUES (?)
                ON CONFLICT(patient_id) DO NOTHING
                """,
                [(patient_id,) for patient_id in sorted(patient_ids)]
            )

            # Insert or update validated appointments
            conn.executemany(
                """
                INSERT INTO appointments
                (appointment_id, patient_id, appointment_date, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(appointment_id) DO UPDATE SET
                    patient_id = excluded.patient_id,
                    appointment_date = excluded.appointment_date,
                    status = excluded.status
                """,
                [
                    (
                        int(row["appointment_id"]),
                        int(row["patient_id"]),
                        row["appointment_date"],
                        row["status"]
                    )
                    for row in appointments
                ]
            )

            # Insert or update claims with valid references
            conn.executemany(
                """
                INSERT INTO claims
                (
                    claim_id,
                    appointment_id,
                    patient_id,
                    service_code,
                    amount,
                    claim_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(claim_id) DO UPDATE SET
                    appointment_id = excluded.appointment_id,
                    patient_id = excluded.patient_id,
                    service_code = excluded.service_code,
                    amount = excluded.amount,
                    claim_status = excluded.claim_status
                """,
                [
                    (
                        int(row["claim_id"]),
                        int(row["appointment_id"]),
                        int(row["patient_id"]),
                        row["service_code"],
                        float(row["amount"]),
                        row["claim_status"]
                    )
                    for row in claims
                ]
            )

            # Insert or update support interactions
            conn.executemany(
                """
                INSERT INTO support
                (
                    interaction_id,
                    patient_id,
                    channel,
                    issue_type,
                    interaction_date,
                    resolution_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(interaction_id) DO UPDATE SET
                    patient_id = excluded.patient_id,
                    channel = excluded.channel,
                    issue_type = excluded.issue_type,
                    interaction_date = excluded.interaction_date,
                    resolution_status = excluded.resolution_status
                """,
                [
                    (
                        int(row["interaction_id"]),
                        int(row["patient_id"]),
                        row["channel"],
                        row["issue_type"],
                        row["interaction_date"],
                        row["resolution_status"]
                    )
                    for row in support_records
                ]
            )

            # Validate foreign key relationships
            violations = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            if violations:
                raise ValueError(
                    f"Foreign key violations detected: {violations}"
                )

            # Report loaded record counts
            for table in ["patients", "appointments", "claims", "support"]:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

                logger.info("%s: %d records", table, count)

        logger.info("Data loading completed successfully")

    except Exception:
        logger.exception("Data loading failed")
        raise


if __name__ == "__main__":
    load_data()
