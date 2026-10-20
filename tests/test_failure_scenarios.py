
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import data_quality


class TestControlledFailures(unittest.TestCase):
    """Verify that invalid data is detected without changing source files."""

    def setUp(self):
        """Create an isolated copy of the generated CSV files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

        for source in (BASE_DIR / "data").glob("*.csv"):
            shutil.copy2(source, self.data_dir / source.name)

    def tearDown(self):
        """Remove temporary test files."""
        self.temp_dir.cleanup()

    def modify_csv(self, filename, transform):
        """Apply a controlled modification to a temporary CSV file."""
        path = self.data_dir / filename

        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            fields = list(reader.fieldnames)
            records = list(reader)

        new_fields, new_records = transform(fields, records)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=new_fields)
            writer.writeheader()
            writer.writerows(new_records)

    def test_renamed_column_is_rejected(self):
        """Detect schema drift caused by a renamed patient identifier."""

        def rename_column(fields, records):
            updated_fields = [
                "patient_number" if field == "patient_id" else field
                for field in fields
            ]

            for record in records:
                record["patient_number"] = record.pop("patient_id")

            return updated_fields, records

        self.modify_csv("appointments_valid.csv", rename_column)

        with patch.object(data_quality, "DATA_DIR", self.data_dir):
            with self.assertRaisesRegex(
                ValueError, "Schema validation failed"
            ) as error:
                data_quality.run_data_quality_checks()

        self.assertIn("patient_id", str(error.exception))
        print("CONTROLLED FAILURE 1 PASSED: Renamed column detected")

    def test_negative_claim_amount_is_rejected(self):
        """Detect a negative claim amount in curated data."""

        def set_negative_amount(fields, records):
            records[0]["amount"] = "-500"
            return fields, records

        self.modify_csv("claims_valid.csv", set_negative_amount)

        with patch.object(data_quality, "DATA_DIR", self.data_dir):
            with self.assertRaisesRegex(
                ValueError, "Data quality validation failed"
            ):
                data_quality.run_data_quality_checks()

        print("CONTROLLED FAILURE 2 PASSED: Negative amount detected")


if __name__ == "__main__":
    unittest.main()
