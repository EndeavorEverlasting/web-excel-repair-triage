import unittest
from src.calc import scale

class TestEdge(unittest.TestCase):
    def test_scale_double(self):
        self.assertEqual(scale(3), 6)

    def test_scale_zero(self):
        self.assertEqual(scale(0), 0)

if __name__ == "__main__":
    unittest.main()
