import os
import sys
import json
import pytest
from unittest.mock import MagicMock, mock_open, patch
from pathlib import Path

# Import the module under test
import Aether_Audio_Archivist_Pro

class TestMissionReport:
    @pytest.fixture
    def archivist(self):
        """Create an Archivist instance with mock data."""
        with patch("pathlib.Path.mkdir"):
            # Now Screen is a real class (MockScreen), so we don't need to patch init
            # unless Aether_Audio_Archivist_Pro.Archivist calls something specific we want to avoid.
            # The base MockScreen.__init__ does nothing.

            archivist = Aether_Audio_Archivist_Pro.Archivist(
                url="https://open.spotify.com/playlist/test",
                library="Test_Library",
                threads=4,
                engine="cpu"
            )

            # Setup sample data
            archivist.stats = {"total": 5, "complete": 3, "no_match": 1, "failed": 1}
            archivist.track_times = {0: 120.5, 1: 180.2, 2: 150.0}
            archivist.track_sizes = {0: 5000000, 1: 7000000, 2: 6000000}
            archivist.tracks = [
                {"title": "Track 1", "artist": "Artist 1", "status": "COMPLETE", "duration": "2:00"},
                {"title": "Track 2", "artist": "Artist 2", "status": "COMPLETE", "duration": "3:00"},
                {"title": "Track 3", "artist": "Artist 3", "status": "COMPLETE", "duration": "2:30"},
                {"title": "Track 4", "artist": "Artist 4", "status": "NO MATCH", "duration": "4:00"},
                {"title": "Track 5", "artist": "Artist 5", "status": "FAILED", "duration": "3:30"},
            ]

            # Mock query_one since we aren't running the full app
            archivist.query_one = MagicMock()

            return archivist

    def test_save_mission_report_happy_path(self, archivist):
        """Test saving a report when everything works normally."""
        total_time = 600.0
        mock_file = mock_open()

        # Mock file operations and hashlib
        with patch("builtins.open", mock_file),              patch("pathlib.Path.exists", return_value=False),              patch("json.dump") as mock_json_dump,              patch("hashlib.md5") as mock_md5:

            # Setup md5 mock
            mock_md5_obj = MagicMock()
            mock_md5_obj.hexdigest.return_value = "abcdef12"
            mock_md5.return_value = mock_md5_obj

            # Mock log_kernel to avoid errors
            archivist.log_kernel = MagicMock()

            # Call the method
            archivist.save_mission_report(total_time)

            # Verify file was opened
            assert mock_file.call_count == 1

            # Verify json structure
            assert mock_json_dump.call_count == 1
            args, _ = mock_json_dump.call_args
            data = args[0]

            # Check key fields
            assert data[0]["playlist_id"] == "abcdef12"
            assert data[0]["total_time"] == 600.0
            assert data[0]["avg_time_per_song"] == 200.0  # 600 / 3 completed
            assert data[0]["stats"] == archivist.stats
            assert data[0]["largest_song"] == "Track 2"  # 7MB is largest
            assert len(data[0]["tracks"]) == 5

    def test_save_mission_report_division_by_zero(self, archivist):
        """Test that stats['complete'] = 0 doesn't cause ZeroDivisionError."""
        archivist.stats["complete"] = 0
        total_time = 100.0

        with patch("builtins.open", mock_open()),              patch("pathlib.Path.exists", return_value=False),              patch("json.dump") as mock_json_dump:

            archivist.log_kernel = MagicMock()

            archivist.save_mission_report(total_time)

            args, _ = mock_json_dump.call_args
            data = args[0]
            # Should divide by 1 instead of 0
            assert data[0]["avg_time_per_song"] == 100.0

    def test_save_mission_report_appends_history(self, archivist):
        """Test that new report is appended to existing history."""
        existing_data = [{"id": "old_report"}]
        total_time = 300.0

        mock_file = mock_open(read_data=json.dumps(existing_data))

        with patch("builtins.open", mock_file),              patch("pathlib.Path.exists", return_value=True),              patch("json.load", return_value=existing_data),              patch("json.dump") as mock_json_dump:

            archivist.log_kernel = MagicMock()

            archivist.save_mission_report(total_time)

            # Verify json dump called with list containing both old and new
            args, _ = mock_json_dump.call_args
            data = args[0]
            assert len(data) == 2
            assert data[0] == existing_data[0]
            assert data[1]["library"] == "Test_Library"
