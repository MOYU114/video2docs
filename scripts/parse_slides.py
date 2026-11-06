"""Thin wrapper kept for backwards compatibility: same as `video2docs slides ...`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from v2d.cli import main

main(["slides", *sys.argv[1:]])
