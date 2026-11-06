"""Step 1: video/audio -> timestamped transcript using mlx-whisper (Apple Silicon).

mlx-whisper decodes the media through ffmpeg directly, so no intermediate WAV
is written. Videos that already have a transcript are skipped.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

MEDIA_EXT = {".mp4", ".mkv", ".mov", ".webm", ".m4a", ".mp3", ".wav"}
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def fmt_ts(t: float) -> str:
    h, rem = divmod(int(t), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def run(c: dict, model: str = DEFAULT_MODEL, only: str | None = None) -> None:
    import mlx_whisper

    out_dir = c["work"] / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(c["videos"]).expanduser()
    videos = sorted(p for p in src.iterdir() if p.suffix.lower() in MEDIA_EXT)
    if only:
        videos = [v for v in videos if only in v.name]
    if not videos:
        raise SystemExit(f"No media files found in {src}")

    for v in videos:
        dst = out_dir / f"{v.stem}.json"
        if dst.exists():
            print(f"skip (done): {v.name}")
            continue
        print(f"transcribing: {v.name}")
        t0 = time.time()
        res = mlx_whisper.transcribe(
            str(v),
            path_or_hf_repo=model,
            language=c.get("language"),
            condition_on_previous_text=False,  # reduces repetition loops on long audio
            verbose=False,
        )
        segs = [
            {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
            for s in res["segments"]
        ]
        dst.write_text(json.dumps({"video": v.name, "segments": segs}, ensure_ascii=False, indent=1))
        (out_dir / f"{v.stem}.txt").write_text(
            "\n".join(f"[{fmt_ts(s['start'])}] {s['text']}" for s in segs)
        )
        print(f"  done: {len(segs)} segments in {time.time() - t0:.0f}s")
