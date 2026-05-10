from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: str | Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)
