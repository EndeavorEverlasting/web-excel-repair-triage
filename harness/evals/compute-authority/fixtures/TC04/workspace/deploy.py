#!/usr/bin/env python3
import os
import sys

if not os.environ.get("STAGING_DEPLOY_TOKEN"):
    print("BLOCKED: missing STAGING_DEPLOY_TOKEN")
    raise SystemExit(2)
print("deployed")
