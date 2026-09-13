import unittest
from src.price import apply_discount

class TestPrice(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(apply_discount(100, 10), 90)

if __name__ == "__main__":
    unittest.main()
