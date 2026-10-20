
import csv
from pathlib import Path

from logger import get_logger

# Configure project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

logger = get_logger("hospital_pipeline.relationships")


def read_csv(filename):
    """Read validated CSV records."""
    with open(
        DATA_DIR / filename,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def write_csv(filename, records, fieldnames):
    """Write records with a consistent schema."""
    with open(
        DATA_DIR / filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def validate_claim_relationships():
    """Quarantine claims with invalid appointment relationships."""

    logger.info("Starting claim relationship validation")

    appointments = read_csv("appointments_valid.csv")
    claims = read_csv("claims_valid.csv")

    # Map each valid appointment to its patient
    appointment_patients = {
        row["appointment_id"]: row["patient_id"]
        for row in appointments
    }

    ready_claims = []
    quarantined_claims = []

    for claim in claims:
        appointment_id = claim["appointment_id"]
        patient_id = claim["patient_id"]

        # Validate appointment existence and patient ownership
        if appointment_id not in appointment_patients:
            reason = "Referenced appointment is not valid"

        elif patient_id != appointment_patients[appointment_id]:
            reason = "Claim patient does not match appointment patient"

        else:
            reason = None

        if reason:
            quarantined_claims.append({
                **claim,
                "rejection_reason": reason
            })
        else:
            ready_claims.append(claim)

    # Preserve the original claim schema
    claim_fields = list(claims[0].keys()) if claims else [
        "claim_id",
        "appointment_id",
        "patient_id",
        "service_code",
        "amount",
        "claim_status"
    ]

    write_csv(
        "claims_ready.csv",
        ready_claims,
        claim_fields
    )

    write_csv(
        "claims_orphaned.csv",
        quarantined_claims,
        claim_fields + ["rejection_reason"]
    )

    logger.info("Claims ready: %d", len(ready_claims))
    logger.info("Claims quarantined: %d", len(quarantined_claims))
    logger.info("Claim relationship validation completed")


if __name__ == "__main__":
    validate_claim_relationships()
