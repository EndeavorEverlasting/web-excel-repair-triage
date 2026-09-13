import unittest
from src.owner import compose

class TestOwner(unittest.TestCase):
    def test_compose(self):
        self.assertEqual(compose("x"), "A:x:B")

if __name__ == "__main__":
    unittest.main()
