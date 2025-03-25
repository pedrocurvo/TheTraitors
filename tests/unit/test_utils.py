import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

from utils import compute_traitors_game_metrics


class TestUtils(unittest.TestCase):
    """Test cases for the utils module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Create a sample CSV content
        self.csv_content = (
            "Round,Vote_Type,Player_ID,Role,Vote_Target,Eliminated\n"
            "1,General,0,Faithful,2,2\n"
            "1,General,1,Faithful,2,2\n"
            "1,General,2,Traitor,0,2\n"
            "1,General,3,Faithful,2,2\n"
            "1,Traitor,2,Traitor,3,3\n"
            "2,General,0,Faithful,1,1\n"
            "2,General,1,Faithful,0,1\n"
            "2,General,3,Faithful,0,1\n"
            "2,Traitor,2,Traitor,0,0\n"
        )

        # Create a temporary CSV file
        self.csv_file = os.path.join(self.temp_dir, "votes.csv")
        with open(self.csv_file, "w") as f:
            f.write(self.csv_content)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory
        import shutil

        shutil.rmtree(self.temp_dir)

    @mock.patch("pandas.read_csv")
    def test_compute_traitors_game_metrics(self, mock_read_csv):
        """Test computing game metrics."""
        # Set up mock DataFrame
        mock_df = pd.DataFrame(
            {
                "Round": [1, 1, 1, 1, 1, 2, 2, 2, 2],
                "Vote_Type": [
                    "General",
                    "General",
                    "General",
                    "General",
                    "Traitor",
                    "General",
                    "General",
                    "General",
                    "Traitor",
                ],
                "Player_ID": [0, 1, 2, 3, 2, 0, 1, 3, 2],
                "Role": [
                    "Faithful",
                    "Faithful",
                    "Traitor",
                    "Faithful",
                    "Traitor",
                    "Faithful",
                    "Faithful",
                    "Faithful",
                    "Traitor",
                ],
                "Vote_Target": [2, 2, 0, 2, 3, 1, 0, 0, 0],
                "Eliminated": [2, 2, 2, 2, 3, 1, 1, 1, 0],
            }
        )
        mock_read_csv.return_value = mock_df

        # Call the function
        metrics = compute_traitors_game_metrics(csv_file="dummy_path.csv")

        # Check that read_csv was called
        mock_read_csv.assert_called_once_with("dummy_path.csv")

        # Check metrics - adjust these based on your actual implementation
        self.assertIn("Traitor Agreement Score (TAS)", metrics)
        self.assertIn("Faithful Agreement Score (FAS)", metrics)
        self.assertIn("Faithful Correctness Rate (FCR)", metrics)
        self.assertIn("Traitor Survival Rate (TSR)", metrics)
        self.assertIn("Faithful Survival Rate (FSR)", metrics)

        # Check specific values if they're deterministic
        self.assertEqual(metrics["Traitor Agreement Score (TAS)"], 1.0)

    def test_compute_traitors_game_metrics_with_file(self):
        """Test computing game metrics with an actual file."""
        # Call the function with the actual file
        metrics = compute_traitors_game_metrics(csv_file=self.csv_file)

        # Check metrics - adjust these based on your actual implementation
        self.assertIn("Traitor Agreement Score (TAS)", metrics)
        self.assertIn("Faithful Agreement Score (FAS)", metrics)
        self.assertIn("Faithful Correctness Rate (FCR)", metrics)
        self.assertIn("Traitor Survival Rate (TSR)", metrics)
        self.assertIn("Faithful Survival Rate (FSR)", metrics)

        # Check specific values if they're deterministic
        self.assertEqual(metrics["Traitor Agreement Score (TAS)"], 1.0)


if __name__ == "__main__":
    unittest.main()
