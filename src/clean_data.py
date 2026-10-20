
import csv
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

files = {
    "appointments": "appointment_id",
    "claims": "claim_id",
    "support": "interaction_id"
}

for name, id_column in files.items():
    file_path = DATA_DIR / f"{name}.csv"

    with open(file_path, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    ids = [row[id_column] for row in rows]
    counts = Counter(ids)

    duplicate_ids = [
        record_id
        for record_id, count in counts.items()
        if count > 1
    ]

    missing_values = sum(
        1
        for row in rows
        for value in row.values()
        if value is None or value.strip() == ""
    )

    print(f"\nDataset: {name}")
    print(f"Total records: {len(rows)}")
    print(f"Duplicate IDs: {duplicate_ids}")
    print(f"Missing values: {missing_values}")

# Remove duplicate claims safely

claims_path = DATA_DIR / "claims.csv"
cleaned_path = DATA_DIR / "claims_cleaned.csv"

with open(claims_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    claims = list(reader)

seen_ids = set()
cleaned_claims = []

for claim in claims:
    claim_id = claim["claim_id"]

    if claim_id in seen_ids:
        continue

    seen_ids.add(claim_id)
    cleaned_claims.append(claim)

with open(cleaned_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(cleaned_claims)

print(f"\nOriginal claims: {len(claims)}")
print(f"Cleaned claims: {len(cleaned_claims)}")
print(f"Duplicates removed: {len(claims) - len(cleaned_claims)}")

# Reusable duplicate removal function

def remove_duplicates(file_name, id_column):
    input_path = DATA_DIR / f"{file_name}.csv"
    output_path = DATA_DIR / f"{file_name}_cleaned.csv"

    with open(input_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    seen_ids = set()
    cleaned_rows = []

    for row in rows:
        record_id = row[id_column]

        if record_id in seen_ids:
            continue

        seen_ids.add(record_id)
        cleaned_rows.append(row)

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"\nDataset: {file_name}")
    print(f"Original records: {len(rows)}")
    print(f"Cleaned records: {len(cleaned_rows)}")
    print(f"Duplicates removed: {len(rows) - len(cleaned_rows)}")


remove_duplicates("support", "interaction_id")
remove_duplicates("appointments", "appointment_id")
#Data validation

from datetime import datetime

def validate_data(file_name):
    file_path = DATA_DIR / f"{file_name}_cleaned.csv"

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    errors = []

    for row in rows:
        record_id = (
            row.get("appointment_id")
            or row.get("claim_id")
            or row.get("interaction_id")
        )

        if not row.get("patient_id", "").strip():
            errors.append((record_id, "Missing patient_id"))

        date_column = {
            "appointments": "appointment_date",
            "support": "interaction_date"
        }.get(file_name)

        if date_column:
            try:
                datetime.strptime(row[date_column], "%Y-%m-%d")
            except (ValueError, TypeError):
                errors.append((record_id, "Invalid date"))

        if file_name == "claims":
            try:
                if float(row["amount"]) < 0:
                    errors.append((record_id, "Negative amount"))
            except (ValueError, TypeError):
                errors.append((record_id, "Invalid amount"))

    print(f"\nValidation: {file_name}")
    print(f"Errors found: {len(errors)}")

    for record_id, reason in errors:
        print(f"Record {record_id}: {reason}")


validate_data("appointments")
validate_data("claims")
validate_data("support")


