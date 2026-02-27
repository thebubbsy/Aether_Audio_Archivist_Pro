import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock playwright.async_api to prevent bootstrap_dependencies from launching browsers
sys.modules['playwright.async_api'] = MagicMock()
sys.modules['playwright.async_api.async_playwright'] = MagicMock()

# Mock other dependencies that might trigger installs or heavy imports
sys.modules['yt_dlp'] = MagicMock()

# Add parent directory to path to import the module
sys.path.append(os.getcwd())

# Import the module AFTER mocking
from Aether_Audio_Archivist_Pro import AetherApp

class TestCSSRefactor(unittest.TestCase):
    def test_css_path_is_set(self):
        """Test that CSS_PATH is set correctly in AetherApp."""
        self.assertTrue(hasattr(AetherApp, 'CSS_PATH'), "AetherApp should have CSS_PATH attribute")
        self.assertEqual(AetherApp.CSS_PATH, "Aether_Audio_Archivist_Pro.tcss")

        # Check that CSS is NOT defined in AetherApp's own dictionary (it might exist in parent App)
        self.assertNotIn('CSS', AetherApp.__dict__, "AetherApp should NOT define CSS attribute directly")

    def test_tcss_file_exists(self):
        """Test that the .tcss file exists."""
        self.assertTrue(os.path.exists("Aether_Audio_Archivist_Pro.tcss"), ".tcss file should exist")

    def test_tcss_content(self):
        """Test that the .tcss file contains expected selectors."""
        with open("Aether_Audio_Archivist_Pro.tcss", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Screen {", content)
            self.assertIn("#launchpad-box {", content)
            self.assertIn("background: #050505;", content)

if __name__ == '__main__':
    unittest.main()
