"""Command-Line Interface for the local AI Harness."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

from .doctor import run_doctor
from .registry import load_workflows
from .runner import (
    explain_workflow,
    run_workflow,
    validate_run,
    generate_report,
    generate_handoff,
)


def parse_remaining_args(args_list: list[str]) -> Dict[str, Any]:
    """Parse remaining arguments of the form --key value or --key val1 val2 into a dict."""
    params: Dict[str, Any] = {}
    i = 0
    while i < len(args_list):
        arg = args_list[i]
        if arg.startswith("--"):
            key = arg[2:]
            vals = []
            i += 1
            while i < len(args_list) and not args_list[i].startswith("--"):
                vals.append(args_list[i])
                i += 1
            if len(vals) == 1:
                params[key] = vals[0]
            elif len(vals) > 1:
                params[key] = vals
            else:
                params[key] = True
        else:
            i += 1
    return params


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m triage.harness.cli",
        description="Local AI Harness Spine CLI for Excel Triage & Repair Workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. doctor
    subparsers.add_parser("doctor", help="Check workspace health, git hygiene, and package policy.")

    # 2. workflows
    subparsers.add_parser("workflows", help="List registered workflows in the repository.")

    # 3. explain
    explain_p = subparsers.add_parser("explain", help="Explain workflow requirements and outputs.")
    explain_p.add_argument("workflow_id", help="Target workflow ID.")

    # 4. run
    run_p = subparsers.add_parser("run", help="Run a registered workflow.")
    run_p.add_argument("workflow_id", help="Target workflow ID.")
    # Allow extra arguments to be captured and parsed manually for dynamic workflows
    
    # 5. validate
    val_p = subparsers.add_parser("validate", help="Validate generated outputs inside a run directory.")
    val_p.add_argument("run_dir", help="Path to the dated run directory.")

    # 6. report
    rep_p = subparsers.add_parser("report", help="Generate operator run report.")
    rep_p.add_argument("run_dir", help="Path to the dated run directory.")

    # 7. handoff
    hand_p = subparsers.add_parser("handoff", help="Generate handoff digest for the next session.")
    hand_p.add_argument("run_dir", help="Path to the dated run directory.")

    # We parse the known args first to isolate subcommand routing
    args, remaining = parser.parse_known_args(argv)

    if args.command == "doctor":
        healthy = run_doctor()
        return 0 if healthy else 1

    elif args.command == "workflows":
        workflows = load_workflows()
        if not workflows:
            print("No workflows registered.", file=sys.stderr)
            return 0
        print(f"{'Workflow ID':<25} | {'Name':<40}")
        print("-" * 70)
        for wf in workflows:
            print(f"{wf.get('id', ''):<25} | {wf.get('name', ''):<40}")
        return 0

    elif args.command == "explain":
        explain_workflow(args.workflow_id)
        return 0

    elif args.command == "run":
        params = parse_remaining_args(remaining)
        try:
            run_dir = run_workflow(args.workflow_id, params)
            print(f"\nWorkflow run completed successfully. Run directory: {run_dir}")
            return 0
        except Exception as exc:
            print(f"Error executing workflow: {exc}", file=sys.stderr)
            return 2

    elif args.command == "validate":
        try:
            val_report = validate_run(Path(args.run_dir))
            if val_report.get("passed"):
                print("Validation PASSED successfully.")
                return 0
            else:
                print("Validation FAILED. Issues found:")
                for issue in val_report.get("issues", []):
                    print(f"  - [{issue.get('code')}] {issue.get('message')}")
                return 1
        except Exception as exc:
            print(f"Error during validation: {exc}", file=sys.stderr)
            return 2

    elif args.command == "report":
        try:
            report_file = generate_report(Path(args.run_dir))
            print(f"Operator report written to {report_file}")
            return 0
        except Exception as exc:
            print(f"Error generating report: {exc}", file=sys.stderr)
            return 2

    elif args.command == "handoff":
        try:
            handoff_file = generate_handoff(Path(args.run_dir))
            print(f"Handoff digest written to {handoff_file}")
            return 0
        except Exception as exc:
            print(f"Error generating handoff digest: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
