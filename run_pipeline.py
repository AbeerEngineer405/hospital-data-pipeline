

import subprocess
import sys
from pathlib import Path

# Project configuration
BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_step(script):
    """Execute a pipeline stage and stop if it fails."""
    script_path = BASE_DIR / "src" / script

    print(f"\nRunning {script}...", flush=True)

    subprocess.run(
        [PYTHON, str(script_path)],
        cwd=BASE_DIR,
        check=True
    )


def main():
    """Execute the complete hospital data pipeline."""

    steps = [
        "generate_data.py",
        "clean_data.py",
        "process_data.py",
        "validate_relationships.py",
        "data_quality.py",
        "database.py",
        "load_data.py"
    ]

    try:
        for step in steps:
            run_step(step)

        print(
            "\nHospital data pipeline completed successfully."
        )

    except subprocess.CalledProcessError as error:
        print(
            f"\nPipeline failed during: {error.cmd}",
            file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
