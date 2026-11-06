from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "courses.yaml"


def load(path: str | Path | None = None) -> dict:
    path = Path(path) if path else DEFAULT_CONFIG
    if not path.exists():
        raise SystemExit(
            f"Config not found: {path}\n"
            "Copy config/courses.example.yaml to config/courses.yaml and edit the paths."
        )
    cfg = yaml.safe_load(path.read_text())
    base = path.resolve().parent.parent
    for key, default in (("work_dir", "work"), ("output_dir", "output")):
        p = Path(cfg.get(key, default)).expanduser()
        cfg[key] = p if p.is_absolute() else base / p
    return cfg


def course(cfg: dict, name: str) -> dict:
    if name not in cfg.get("courses", {}):
        raise SystemExit(f"Unknown course {name!r}. Available: {list(cfg.get('courses', {}))}")
    c = dict(cfg["courses"][name])
    c["name"] = name
    c["work"] = cfg["work_dir"] / name
    c["out"] = cfg["output_dir"] / name
    return c
