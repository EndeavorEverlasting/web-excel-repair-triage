#!/usr/bin/env python3
from __future__ import annotations

import argparse

from scripts import tmp_apply_p79_upstream_synthesis as base

base.EXTERNAL_TEST_METHOD = r'''
    def test_prompt_adder_exposes_predraft_all_registered_source_review(self) -> None:
        query = "prompt registry upstream synthesis zeta"
        configured = {item["id"] for item in self.contract["sources"]}
        receipt = {
            "schema_version": add_prior_art.RECEIPT_SCHEMA,
            "query": query,
            "sources": [{"source_id": source_id} for source_id in sorted(configured)],
            "all_registered_sources_searched": True,
            "distinct_residual_terms": ["synthesis"],
            "automatic_prompt_authoring": False,
        }
        with mock.patch.object(
            add_prior_art, "review_external_prior_art", return_value=receipt
        ) as review:
            result = prompt_ops.review_prior_art(query)
        review.assert_called_once_with(query)
        self.assertTrue(result["all_registered_sources_searched"])
        self.assertEqual({row["source_id"] for row in result["sources"]}, configured)

        with (
            mock.patch.object(prompt_ops, "review_prior_art", return_value=receipt) as cli_review,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(prompt_ops.main(["prior-art", "--query", query]), 0)
        cli_review.assert_called_once_with(query)

'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        base.verify()
    else:
        base.apply()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
