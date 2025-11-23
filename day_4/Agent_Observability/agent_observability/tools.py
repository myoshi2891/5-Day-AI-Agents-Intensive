"""Domain tools wired into the research agent."""

from __future__ import annotations

from typing import Sequence


def count_papers(papers: list[str]) -> int:
    """Count validated papers returned by the search agent."""
    if not isinstance(papers, Sequence):
        raise ValueError("papers must be a sequence of strings")

    invalid_items = [paper for paper in papers if not isinstance(paper, str)]
    if invalid_items:
        raise ValueError("papers must only include strings")

    return len(papers)
