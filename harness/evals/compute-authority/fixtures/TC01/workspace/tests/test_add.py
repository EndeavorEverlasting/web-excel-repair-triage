import unittest
from src.calc import add

class TestAdd(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
