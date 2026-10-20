
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import run_pipeline


class TestPipelineEngineering(unittest.TestCase):
    """Test pipeline orchestration and failure handling."""

    @patch("run_pipeline.subprocess.run")
    def test_pipeline_uses_current_python(self, mock_run):
        """Verify that stages run with the active Python interpreter."""
        run_pipeline.run_step("generate_data.py")

        args, kwargs = mock_run.call_args

        self.assertEqual(args[0][0], sys.executable)
        self.assertEqual(kwargs["cwd"], BASE_DIR)
        self.assertTrue(kwargs["check"])

    @patch("run_pipeline.subprocess.run")
    def test_pipeline_runs_all_stages_in_order(self, mock_run):
        """Verify the required execution order of pipeline stages."""
        run_pipeline.main()

        executed_scripts = [
            Path(call.args[0][1]).name
            for call in mock_run.call_args_list
        ]

        expected_scripts = [
            "generate_data.py",
            "clean_data.py",
            "process_data.py",
            "validate_relationships.py",
            "data_quality.py",
            "database.py",
            "load_data.py"
        ]

        self.assertEqual(executed_scripts, expected_scripts)

    @patch("run_pipeline.subprocess.run")
    def test_pipeline_stops_when_stage_fails(self, mock_run):
        """Verify that a failed stage stops downstream execution."""

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["python", "clean_data.py"]
        )

        with self.assertRaises(SystemExit) as error:
            run_pipeline.main()

        self.assertEqual(error.exception.code, 1)
        self.assertEqual(mock_run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
