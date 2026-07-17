from __future__ import annotations

from triage import prompt_kit_v39_generator as generator
from triage import prompt_kit_v39_ooxml_base as ooxml


def test_v39_public_ooxml_surface_contains_no_prompt_taxonomy_or_generator() -> None:
    for forbidden in (
        "generate_v39",
        "validate_v39",
        "NEW_PROMPT_IDS",
        "ADVANCED_STANDARD_AI_IDS",
        "GNHF_PROMPT_IDS",
    ):
        assert not hasattr(ooxml, forbidden), forbidden


def test_v39_semantic_ownership_lives_in_canonical_generator() -> None:
    assert generator.STANDARD_AI_EXTENSION_IDS == ("P50", "P51", "P52", "P53", "P54", "P55")
    assert generator.GNHF_HARNESS_IDS == ("P45", "P46", "P47", "P48", "P49")
    assert generator.APPEND_ORDER == (
        "P50", "P51", "P52", "P53", "P54", "P55",
        "P45", "P46", "P47", "P48", "P49",
    )
