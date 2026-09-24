import unittest
from src.core import value

class TestCore(unittest.TestCase):
    def test_value(self):
        self.assertEqual(value(), 42)

if __name__ == "__main__":
    unittest.main()
