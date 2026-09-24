import unittest
from src.names import normalize_name

class TestNormalize(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(normalize_name("  Ada   Lovelace "), "ada lovelace")

if __name__ == "__main__":
    unittest.main()
