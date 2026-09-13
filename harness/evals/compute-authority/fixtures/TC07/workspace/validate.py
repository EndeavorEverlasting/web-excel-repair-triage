#!/usr/bin/env python3
import subprocess
import sys
raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "tests.test_math", "-v"]))
