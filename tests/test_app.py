import unittest
from Aether_Audio_Archivist_Pro import AetherApp

class TestAppStartup(unittest.TestCase):
    def test_app_instantiation(self):
        app = AetherApp()
        self.assertIsNotNone(app)

if __name__ == '__main__':
    unittest.main()
