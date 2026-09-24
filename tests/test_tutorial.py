from __future__ import annotations


from triage.tutorial import get_tutorial_sections


def test_tutorial_sections_non_empty():
    secs = get_tutorial_sections()
    assert isinstance(secs, list)
    assert len(secs) >= 3
    assert all(s.title and s.markdown for s in secs)


def test_tutorial_mentions_lifecycle_folders():
    text = "\n".join(s.markdown for s in get_tutorial_sections())
    assert "Active/" in text
    assert "Deprecated/" in text
    assert "Outputs/" in text
