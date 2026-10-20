
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

input_path = DATA_DIR / "claims_cleaned.csv"
valid_path = DATA_DIR / "claims_valid.csv"
rejected_path = DATA_DIR / "claims_rejected.csv"

with open(input_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    rows = list(reader)

valid_rows = []
rejected_rows = []

for row in rows:
    
    # Validate claim status
    valid_claim_statuses = {
        "Submitted",
        "Approved",
        "Rejected"
    }

    if row["claim_status"] not in valid_claim_statuses:
        rejected_rows.append({
            **row,
            "rejection_reason": "Invalid claim status"
        })
        continue

    # Validate required service code
    if not row["service_code"].strip():
        rejected_rows.append({
            **row,
            "rejection_reason": "Missing service code"
        })
        continue

    try:
        amount = float(row["amount"])

        if amount < 0:
            raise ValueError("Negative amount")

        valid_rows.append(row)

    except (ValueError, TypeError) as error:
        rejected_rows.append({
            **row,
            "rejection_reason": str(error)
        })

with open(valid_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(valid_rows)

with open(rejected_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames + ["rejection_reason"]
    )
    writer.writeheader()
    writer.writerows(rejected_rows)

print(f"Valid claims: {len(valid_rows)}")
print(f"Rejected claims: {len(rejected_rows)}")

from datetime import datetime

# Define input and output paths
support_path = DATA_DIR / "support_cleaned.csv"
support_valid_path = DATA_DIR / "support_valid.csv"
support_rejected_path = DATA_DIR / "support_rejected.csv"

# Load support records
with open(support_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    support_fields = reader.fieldnames
    support_rows = list(reader)

# Initialize validation results
valid_support = []
rejected_support = []

# Validate support records
for row in support_rows:
    reasons = []
    
    # Validate resolution status
    valid_support_statuses = {
        "Escalated",
        "Pending",
        "Resolved"
    }

    if row["resolution_status"] not in valid_support_statuses:
        reasons.append("Invalid resolution status")


    # Check required patient ID
    if not row["patient_id"].strip():
        reasons.append("Missing patient_id")

    # Validate interaction date
    try:
        datetime.strptime(row["interaction_date"], "%Y-%m-%d")
    except ValueError:
        reasons.append("Invalid date")

    # Separate valid and rejected records
    if reasons:
        rejected_support.append({
            **row,
            "rejection_reason": "; ".join(reasons)
        })
    else:
        valid_support.append(row)

# Save valid records
with open(support_valid_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=support_fields)
    writer.writeheader()
    writer.writerows(valid_support)

# Save rejected records with reasons
with open(support_rejected_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=support_fields + ["rejection_reason"]
    )
    writer.writeheader()
    writer.writerows(rejected_support)

# Report validation results
print(f"Valid support: {len(valid_support)}")
print(f"Rejected support: {len(rejected_support)}")

# Define appointment file paths
appointments_path = DATA_DIR / "appointments_cleaned.csv"
appointments_valid_path = DATA_DIR / "appointments_valid.csv"
appointments_rejected_path = DATA_DIR / "appointments_rejected.csv"

# Load appointment records
with open(appointments_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    appointment_fields = reader.fieldnames
    appointment_rows = list(reader)

valid_appointments = []
rejected_appointments = []

# Validate appointment records
for row in appointment_rows:
    reasons = []
    
    # Validate and normalize appointment status
    status_mapping = {
        "scheduled": "Scheduled",
        "completed": "Completed",
        "complete": "Completed",
        "cancelled": "Cancelled",
        "no show": "No Show"
    }

    raw_status = row["status"].strip().lower()

    if raw_status in status_mapping:
        row["status"] = status_mapping[raw_status]
    else:
        reasons.append("Invalid appointment status")


    # Check required patient ID
    if not row["patient_id"].strip():
        reasons.append("Missing patient_id")

    # Validate appointment date
    try:
        datetime.strptime(row["appointment_date"], "%Y-%m-%d")
    except ValueError:
        reasons.append("Invalid date")

    # Separate valid and rejected records
    if reasons:
        rejected_appointments.append({
            **row,
            "rejection_reason": "; ".join(reasons)
        })
    else:
        valid_appointments.append(row)

# Save valid appointments
with open(appointments_valid_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=appointment_fields)
    writer.writeheader()
    writer.writerows(valid_appointments)

# Save rejected appointments
with open(appointments_rejected_path, "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=appointment_fields + ["rejection_reason"]
    )
    writer.writeheader()
    writer.writerows(rejected_appointments)

# Report validation results
print(f"Valid appointments: {len(valid_appointments)}")
print(f"Rejected appointments: {len(rejected_appointments)}")
