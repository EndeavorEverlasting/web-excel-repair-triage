#!/usr/bin/env python3
"""
Harness Completeness Validator
Checks that all required harness components exist and are valid.
"""

import json
import os
import sys
from pathlib import Path


def check_file_exists(path: Path, name: str) -> bool:
    """Check if a file exists and is not empty."""
    if not path.exists():
        print(f"  [FAIL] {name}: Missing")
        return False
    if path.stat().st_size == 0:
        print(f"  [FAIL] {name}: Empty")
        return False
    print(f"  [PASS] {name}")
    return True


def check_directory_exists(path: Path, name: str) -> bool:
    """Check if a directory exists."""
    if not path.exists():
        print(f"  [FAIL] {name}: Missing")
        return False
    if not path.is_dir():
        print(f"  [FAIL] {name}: Not a directory")
        return False
    print(f"  [PASS] {name}")
    return True


def validate_json(path: Path, name: str) -> bool:
    """Validate that a file contains valid JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"  [PASS] {name}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"  [FAIL] {name}: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] {name}: Error reading - {e}")
        return False


def main():
    """Main validation function."""
    print("Harness Completeness Check")
    print("=" * 50)
    
    repo_root = Path(__file__).parent.parent
    results = []
    
    # 1. Required files
    print("\n1. Required Files:")
    results.append(check_file_exists(repo_root / "AGENTS.md", "AGENTS.md"))
    results.append(check_file_exists(repo_root / "README.md", "README.md"))
    results.append(check_file_exists(repo_root / "CODEBASE_MAP.md", "CODEBASE_MAP.md"))
    results.append(check_file_exists(repo_root / "WORKFLOW.md", "WORKFLOW.md"))
    results.append(check_file_exists(repo_root / "ARTIFACT_REGISTRY.md", "ARTIFACT_REGISTRY.md"))
    results.append(check_file_exists(repo_root / "SKILLS.md", "SKILLS.md"))
    results.append(check_file_exists(repo_root / "requirements.txt", "requirements.txt"))
    
    # 2. Directory structure
    print("\n2. Directory Structure:")
    results.append(check_directory_exists(repo_root / "scripts", "scripts/"))
    results.append(check_directory_exists(repo_root / "tests", "tests/"))
    results.append(check_directory_exists(repo_root / "docs", "docs/"))
    results.append(check_directory_exists(repo_root / "Outputs", "Outputs/"))
    results.append(check_directory_exists(repo_root / "Repaired", "Repaired/"))
    
    # 3. Prompt Kit
    print("\n3. Prompt Kit:")
    results.append(check_file_exists(repo_root / "docs" / "prompt-kit.html", "prompt-kit.html"))
    results.append(check_file_exists(repo_root / "docs" / "prompt-kit.js", "prompt-kit.js"))
    results.append(check_file_exists(repo_root / "docs" / "prompts.json", "prompts.json"))
    results.append(validate_json(repo_root / "docs" / "prompts.json", "prompts.json"))
    results.append(check_file_exists(repo_root / "docs" / "reference.json", "reference.json"))
    results.append(validate_json(repo_root / "docs" / "reference.json", "reference.json"))
    
    # 4. Scripts
    print("\n4. Scripts:")
    scripts = list((repo_root / "scripts").glob("*.py"))
    results.append(len(scripts) > 0)
    if scripts:
        print(f"  [PASS] Found {len(scripts)} Python scripts")
    else:
        print("  [FAIL] No Python scripts found")
    
    # 5. Tests
    print("\n5. Tests:")
    tests = list((repo_root / "tests").glob("test_*.py"))
    results.append(len(tests) > 0)
    if tests:
        print(f"  [PASS] Found {len(tests)} test files")
    else:
        print("  [FAIL] No test files found")
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("Harness is complete!")
        return 0
    else:
        print("Harness is incomplete. Fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
