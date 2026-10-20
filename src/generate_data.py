
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# Project configuration
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RECORD_COUNT = 150
START_DATE = datetime(2026, 10, 1)
random.seed(42)


def save_csv(filename, records, fieldnames):
    """Write records to a CSV file."""

    file_path = DATA_DIR / filename

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Created {len(records)} records: {filename}")


def generate_appointments():
    """Generate synthetic appointment records."""

    statuses = [
        "Scheduled",
        "Completed",
        "Cancelled",
        "No Show"
    ]

    appointments = []

    for appointment_id in range(1, RECORD_COUNT + 1):
        appointment_date = START_DATE + timedelta(
            days=random.randint(0, 29)
        )

        appointments.append({
            "appointment_id": appointment_id,
            "patient_id": random.randint(1, 50),
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "status": random.choice(statuses)
        })

    # Inject controlled data quality issues
    appointments[5]["status"] = "complete"
    appointments[10]["appointment_date"] = "invalid-date"
    appointments[15]["patient_id"] = ""
    appointments[20]["status"] = "Unknown"
    appointments.append(appointments[0].copy())

    save_csv(
        "appointments.csv",
        appointments,
        [
            "appointment_id",
            "patient_id",
            "appointment_date",
            "status"
        ]
    )

    return appointments


def generate_claims(appointments):
    """Generate claims linked to existing appointments."""

    service_codes = [
        "CONSULT",
        "XRAY",
        "LAB",
        "THERAPY"
    ]

    claim_statuses = [
        "Submitted",
        "Approved",
        "Rejected"
    ]

    # Exclude appointments with missing patient IDs
    eligible_appointments = [
        appointment
        for appointment in appointments[:RECORD_COUNT]
        if str(appointment["patient_id"]).strip()
    ]

    claims = []

    for claim_id in range(1, RECORD_COUNT + 1):

        # Preserve the appointment-patient relationship
        appointment = random.choice(eligible_appointments)

        claims.append({
            "claim_id": claim_id,
            "appointment_id": appointment["appointment_id"],
            "patient_id": appointment["patient_id"],
            "service_code": random.choice(service_codes),
            "amount": round(random.uniform(50, 1500), 2),
            "claim_status": random.choice(claim_statuses)
        })

    # Inject controlled data quality issues
    claims[4]["amount"] = -100
    claims[9]["service_code"] = ""
    claims[14]["claim_status"] = "unknown"
    claims.append(claims[0].copy())

    save_csv(
        "claims.csv",
        claims,
        [
            "claim_id",
            "appointment_id",
            "patient_id",
            "service_code",
            "amount",
            "claim_status"
        ]
    )

    return claims


def generate_support():
    """Generate synthetic patient support interactions."""

    channels = [
        "Phone",
        "Email",
        "Chat"
    ]

    issue_types = [
        "Appointment",
        "Billing",
        "Complaint",
        "Inquiry"
    ]

    resolution_statuses = [
        "Resolved",
        "Pending",
        "Escalated"
    ]

    support_records = []

    for interaction_id in range(1, RECORD_COUNT + 1):
        interaction_date = START_DATE + timedelta(
            days=random.randint(0, 29)
        )

        support_records.append({
            "interaction_id": interaction_id,
            "patient_id": random.randint(1, 50),
            "channel": random.choice(channels),
            "issue_type": random.choice(issue_types),
            "interaction_date": interaction_date.strftime("%Y-%m-%d"),
            "resolution_status": random.choice(resolution_statuses)
        })

    # Inject controlled data quality issues
    support_records[3]["patient_id"] = ""
    support_records[8]["channel"] = "phone"
    support_records[12]["interaction_date"] = "bad-date"
    support_records[18]["resolution_status"] = "Unknown"
    support_records.append(support_records[0].copy())

    save_csv(
        "support.csv",
        support_records,
        [
            "interaction_id",
            "patient_id",
            "channel",
            "issue_type",
            "interaction_date",
            "resolution_status"
        ]
    )

    return support_records


def main():
    """Generate all synthetic hospital datasets."""

    print("Starting synthetic data generation...")

    appointments = generate_appointments()
    generate_claims(appointments)
    generate_support()

    print("Data generation completed successfully.")


if __name__ == "__main__":
    main()
