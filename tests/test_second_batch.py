
import csv
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import database
import load_data


class TestSecondDailyBatch(unittest.TestCase):
    """Verify that a second batch inserts and updates records."""

    def test_second_batch_inserts_and_updates(self):
        """Load two batches into an isolated SQLite database."""

        with tempfile.TemporaryDirectory() as temp:
            temp_dir = Path(temp)
            test_db = temp_dir / "test_hospital.db"
            test_data = temp_dir / "data"
            test_data.mkdir()

            # Copy validated source files.
            filenames = [
                "appointments_valid.csv",
                "claims_ready.csv",
                "support_valid.csv"
            ]

            for filename in filenames:
                source = BASE_DIR / "data" / filename
                destination = test_data / filename
                destination.write_bytes(source.read_bytes())

            with (
                patch.object(database, "DB_PATH", test_db),
                patch.object(load_data, "DB_PATH", test_db),
                patch.object(load_data, "DATA_DIR", test_data)
            ):

                # Load the initial batch.
                load_data.load_data()

                with closing(sqlite3.connect(test_db)) as conn:
                    initial_count = conn.execute(
                        "SELECT COUNT(*) FROM appointments"
                    ).fetchone()[0]

                appointments_path = (
                    test_data / "appointments_valid.csv"
                )

                with appointments_path.open(
                    newline="",
                    encoding="utf-8-sig"
                ) as file:
                    reader = csv.DictReader(file)
                    fields = list(reader.fieldnames)
                    rows = list(reader)

                # Simulate a corrected record.
                corrected_id = int(rows[0]["appointment_id"])
                original_status = rows[0]["status"]

                corrected_status = (
                    "Completed"
                    if original_status != "Completed"
                    else "Scheduled"
                )

                rows[0]["status"] = corrected_status

                # Simulate a new appointment in the second batch.
                new_id = (
                    max(int(row["appointment_id"]) for row in rows)
                    + 1000
                )

                rows.append({
                    "appointment_id": str(new_id),
                    "patient_id": rows[0]["patient_id"],
                    "appointment_date": "2026-10-21",
                    "status": "Scheduled"
                })

                with appointments_path.open(
                    "w",
                    newline="",
                    encoding="utf-8"
                ) as file:
                    writer = csv.DictWriter(
                        file,
                        fieldnames=fields
                    )
                    writer.writeheader()
                    writer.writerows(rows)

                # Load the second batch.
                load_data.load_data()

                with closing(sqlite3.connect(test_db)) as conn:
                    final_count = conn.execute(
                        "SELECT COUNT(*) FROM appointments"
                    ).fetchone()[0]

                    updated_status = conn.execute(
                        """
                        SELECT status
                        FROM appointments
                        WHERE appointment_id = ?
                        """,
                        (corrected_id,)
                    ).fetchone()[0]

                    new_record = conn.execute(
                        """
                        SELECT appointment_id
                        FROM appointments
                        WHERE appointment_id = ?
                        """,
                        (new_id,)
                    ).fetchone()

                    violations = conn.execute(
                        "PRAGMA foreign_key_check"
                    ).fetchall()

                self.assertEqual(
                    final_count,
                    initial_count + 1
                )
                self.assertEqual(
                    updated_status,
                    corrected_status
                )
                self.assertIsNotNone(new_record)
                self.assertEqual(violations, [])

                print("\nSECOND DAILY BATCH TEST PASSED")
                print("Initial appointments:", initial_count)
                print("Final appointments:", final_count)
                print("New appointment ID:", new_id)
                print(
                    "Corrected appointment status:",
                    updated_status
                )
                print(
                    "Foreign key violations:",
                    len(violations)
                )


if __name__ == "__main__":
    unittest.main()
