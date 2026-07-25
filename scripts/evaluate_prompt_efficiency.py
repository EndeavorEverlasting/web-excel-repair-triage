#!/usr/bin/env python3
"""CLI for deterministic and LLM-as-judge prompt-efficiency evaluation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import build_prompt_kit_registry as registry

from prompt_efficiency_eval import (
    PromptEfficiencyEvalError,
    build_judge_packet_set,
    build_prompt_cases,
    build_report,
    build_response_cases,
    load_candidate_responses,
    load_judge_results,
    load_policy,
    print_summary,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate prompt token efficiency and weak-model readiness with "
            "deterministic checks plus optional independent LLM judge results."
        )
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-judge-packets", type=Path)
    parser.add_argument("--judge-results", type=Path)
    parser.add_argument("--candidate-responses", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        policy = load_policy()
        prompts = registry.load_prompt_registry()
        if args.candidate_responses:
            candidates = load_candidate_responses(args.candidate_responses)
            cases = build_response_cases(
                candidates,
                prompts,
                policy,
                prompt_id=args.prompt,
            )
        else:
            cases = build_prompt_cases(prompts, policy, prompt_id=args.prompt)
        judge_results = (
            load_judge_results(args.judge_results)
            if args.judge_results
            else None
        )
        report = build_report(
            cases,
            policy,
            judge_results=judge_results,
            strict=args.strict,
        )
        output = write_json(report, args.output) if args.output else None
        packet_output = None
        if args.emit_judge_packets:
            packet_output = write_json(
                build_judge_packet_set(cases, policy),
                args.emit_judge_packets,
            )
    except (
        PromptEfficiencyEvalError,
        SystemExit,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"Prompt efficiency evaluation failed: {exc}", file=sys.stderr)
        return 2

    if args.summary or not args.output:
        print_summary(report, output=output)
        if packet_output:
            print(f"Judge packets: {packet_output}")
    if not report["code"]["safe"]:
        return 1
    if args.strict and not report["strict_ready"]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
