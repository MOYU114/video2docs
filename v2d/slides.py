"""Step 2: slide/notes PDFs -> per-page text JSON."""
from __future__ import annotations

import json
from pathlib import Path


def parse_dir(src: Path, dst: Path) -> None:
    import pymupdf

    dst.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(Path(src).expanduser().glob("*.pdf")):
        with pymupdf.open(pdf) as doc:
            pages = [{"page": i + 1, "text": p.get_text().strip()} for i, p in enumerate(doc)]
        (dst / f"{pdf.stem}.json").write_text(
            json.dumps({"file": pdf.name, "pages": pages}, ensure_ascii=False, indent=1)
        )
        print(f"{pdf.name}: {len(pages)} pages")


def run(c: dict) -> None:
    for kind in ("slides", "notes"):
        if c.get(kind):
            parse_dir(Path(c[kind]), c["work"] / kind)
