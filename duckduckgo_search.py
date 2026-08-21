"""Lightweight shim for duckduckgo_search used in tests.

This stub provides the minimal API surface used by the project so
unit tests can import without installing external dependencies.
"""
from typing import Iterator, Dict


class DDGS:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def text(self, query: str, max_results: int = 6) -> Iterator[Dict[str, str]]:
        # Return an empty iterator to simulate no live results (tests use fallbacks)
        return iter([])
