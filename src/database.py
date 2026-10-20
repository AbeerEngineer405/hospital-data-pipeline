
import sqlite3
from contextlib import closing
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"


def create_database():
    """Initialize the hospital database and enforce data integrity."""

    # Ensure the SQLite connection is explicitly closed.
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:

            # Enforce foreign key constraints for this connection.
            conn.execute("PRAGMA foreign_keys = ON")

            # Store unique patient identifiers.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY
                )
            """)

            # Store validated patient appointments.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id INTEGER PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    appointment_date TEXT NOT NULL,
                    status TEXT NOT NULL,

                    FOREIGN KEY (patient_id)
                        REFERENCES patients(patient_id)
                )
            """)

            # Store validated claims linked to appointments.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id INTEGER PRIMARY KEY,
                    appointment_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    service_code TEXT NOT NULL,
                    amount REAL NOT NULL CHECK (amount >= 0),
                    claim_status TEXT NOT NULL,

                    FOREIGN KEY (patient_id)
                        REFERENCES patients(patient_id),

                    FOREIGN KEY (appointment_id)
                        REFERENCES appointments(appointment_id)
                )
            """)

            # Store validated patient support interactions.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS support (
                    interaction_id INTEGER PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    interaction_date TEXT NOT NULL,
                    resolution_status TEXT NOT NULL,

                    FOREIGN KEY (patient_id)
                        REFERENCES patients(patient_id)
                )
            """)

    print("Database initialized successfully.")


if __name__ == "__main__":
    create_database()
