"""Command-line entry point: video2docs {transcribe,slides,align,all} COURSE."""
from __future__ import annotations

import argparse

from . import config


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="video2docs", description=__doc__)
    ap.add_argument("--config", help="path to courses.yaml (default: config/courses.yaml)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("course")
        return p

    t = add("transcribe", "transcribe recordings with mlx-whisper")
    t.add_argument("--model", default=None, help="Hugging Face repo of an MLX Whisper model")
    t.add_argument("--only", help="only process files whose name contains this string")
    add("slides", "extract per-page text from slide and notes PDFs")
    a = add("align", "align transcripts to slide pages and write Markdown")
    a.add_argument("--window", type=float, default=45, help="transcript window length in seconds")
    a.add_argument("--only", help="only process files whose name contains this string")
    add("all", "run transcribe, slides and align")

    args = ap.parse_args(argv)
    c = config.course(config.load(args.config), args.course)

    from . import align, slides, transcribe

    if args.cmd in ("transcribe", "all"):
        kw = {"only": getattr(args, "only", None)}
        if getattr(args, "model", None):
            kw["model"] = args.model
        transcribe.run(c, **kw)
    if args.cmd in ("slides", "all"):
        slides.run(c)
    if args.cmd in ("align", "all"):
        align.run(c, window=getattr(args, "window", 45), only=getattr(args, "only", None))


if __name__ == "__main__":
    main()
