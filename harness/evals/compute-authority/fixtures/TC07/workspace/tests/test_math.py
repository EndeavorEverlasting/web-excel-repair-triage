import unittest
from src.mathutil import double

class TestMath(unittest.TestCase):
    def test_double(self):
        self.assertEqual(double(3), 6)

    def test_zero(self):
        self.assertEqual(double(0), 0)

if __name__ == "__main__":
    unittest.main()
