import unittest

class Archivist:
    def parse_duration(self, d_str):
        try:
            parts = d_str.split(":")
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except: return 0
        return 0

class TestDurationParsing(unittest.TestCase):
    def setUp(self):
        self.archivist = Archivist()

    def test_valid_mm_ss(self):
        self.assertEqual(self.archivist.parse_duration("3:45"), 3 * 60 + 45)

    def test_valid_hh_mm_ss(self):
        self.assertEqual(self.archivist.parse_duration("1:02:30"), 3600 + 2 * 60 + 30)

    def test_invalid_format(self):
        self.assertEqual(self.archivist.parse_duration("invalid"), 0)

    def test_invalid_numbers(self):
        self.assertEqual(self.archivist.parse_duration("3:xx"), 0)

    def test_empty(self):
        self.assertEqual(self.archivist.parse_duration(""), 0)

    def test_none(self):
        # This currently catches AttributeError and returns 0 because of bare except
        self.assertEqual(self.archivist.parse_duration(None), 0)

if __name__ == '__main__':
    unittest.main()
