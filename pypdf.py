"""Minimal shim for pypdf.PdfReader used in tests.

Provides a `PdfReader` with a `pages` list whose `extract_text()`
method returns an empty string. Keeps tests importable without
installing the full `pypdf` package.
"""


class _Page:
    def extract_text(self):
        return ""


class PdfReader:
    def __init__(self, path):
        # Provide an empty set of pages to avoid extraction errors
        self.pages = [_Page()]
