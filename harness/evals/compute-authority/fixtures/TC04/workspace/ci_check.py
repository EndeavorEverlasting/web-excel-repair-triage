#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
from src.feature import greeting

class TestGreeting(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greeting(), "Hello")

def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestGreeting)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    gen = json.loads(Path("generated/feature.json").read_text(encoding="utf-8"))
    if gen.get("greeting") != "Hello" or gen.get("ENABLE_GREETING") is not True:
        print("CI FAIL: generated artifact out of sync")
        raise SystemExit(1)
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
