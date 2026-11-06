"""Thin wrapper kept for backwards compatibility: same as `video2docs align ...`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from v2d.cli import main

main(["align", *sys.argv[1:]])
