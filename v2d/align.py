"""Step 3: align transcript windows to slide pages and write Markdown for reading.

Outputs, per recording:
  <output_dir>/<course>/<recording>.md   one section per slide page: page, time range,
                                         slide text and what the lecturer said
  <work_dir>/<course>/aligned/<recording>.json
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .matching import TfIdf, cos, tokens, viterbi, windows
from .transcribe import fmt_ts


def load_decks(d: Path) -> dict[str, list[dict]]:
    return {f.stem: json.loads(f.read_text())["pages"] for f in sorted(d.glob("*.json"))}


def pick_decks(win_vecs, deck_names, page_vecs, min_share=0.15, min_sim=0.05):
    """Each window votes for its most similar deck; decks with >= min_share of votes are kept."""
    votes: Counter = Counter()
    for wv in win_vecs:
        sim, name = max(
            ((cos(wv, pv), n) for n, pvs in page_vecs.items() for pv in pvs), default=(0.0, None)
        )
        if sim > min_sim:
            votes[name] += 1
    total = sum(votes.values()) or 1
    chosen = [n for n, v in votes.items() if v / total >= min_share]
    return sorted(chosen, key=deck_names.index), votes


def align_one(wins, wvecs, decks, page_vecs, chosen):
    seq = [(n, i) for n in chosen for i in range(len(decks[n]))]
    flat = [page_vecs[n][i] for n, i in seq]
    scores = [[cos(wv, pv) for pv in flat] for wv in wvecs]
    path = viterbi(scores)

    sections: list[dict] = []
    for w, j, sc in zip(wins, path, scores):
        n, i = seq[j]
        last = sections[-1] if sections else None
        if last and last["deck"] == n and last["page"] == i + 1:
            last["end"] = w["end"]
            last["text"] += " " + w["text"]
            last["_sims"].append(sc[j])
        else:
            sections.append({"deck": n, "page": i + 1, "start": w["start"], "end": w["end"],
                             "text": w["text"], "_sims": [sc[j]]})
    for s in sections:
        sims = s.pop("_sims")
        s["similarity"] = round(sum(sims) / len(sims), 3)
    return sections


def to_markdown(stem: str, chosen: list[str], sections: list[dict], decks) -> str:
    md = [f"# {stem}", "", f"Slide decks: {', '.join(chosen)}", "",
          "One section per slide page. *Slide* is the page text; *Lecture* is what was said "
          "during that time range (automatic transcription, may contain errors). A page can "
          "appear more than once when the lecturer goes back to it.", ""]
    for s in sections:
        page_text = decks[s["deck"]][s["page"] - 1]["text"]
        quoted = "\n".join("> " + ln for ln in page_text.splitlines() if ln.strip()) or "> (blank page)"
        md += [f"## {s['deck']} p.{s['page']}  [{fmt_ts(s['start'])}–{fmt_ts(s['end'])}]", "",
               "**Slide**", "", quoted, "", "**Lecture**", "", s["text"].strip(), ""]
    return "\n".join(md)


def run(c: dict, window: float = 45, only: str | None = None) -> None:
    tr_dir, sl_dir = c["work"] / "transcripts", c["work"] / "slides"
    aligned_dir = c["work"] / "aligned"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    c["out"].mkdir(parents=True, exist_ok=True)

    decks = load_decks(sl_dir)
    if not decks:
        raise SystemExit("No parsed slides found; run the `slides` step first.")
    transcripts = sorted(tr_dir.glob("*.json"))
    if only:
        transcripts = [t for t in transcripts if only in t.name]
    if not transcripts:
        raise SystemExit("No transcripts found; run the `transcribe` step first.")

    all_wins = {t.stem: windows(json.loads(t.read_text())["segments"], window) for t in transcripts}
    page_toks = {n: [tokens(p["text"]) for p in pages] for n, pages in decks.items()}
    # IDF is estimated over all slide pages and all transcript windows together.
    model = TfIdf([pt for pts in page_toks.values() for pt in pts]
                  + [tokens(w["text"]) for ws in all_wins.values() for w in ws])
    page_vecs = {n: [model.vec(pt) for pt in pts] for n, pts in page_toks.items()}
    lecture_map = c.get("lecture_map") or {}

    for stem, wins in all_wins.items():
        wvecs = [model.vec(tokens(w["text"])) for w in wins]
        if stem in lecture_map:
            chosen, votes = list(lecture_map[stem]), Counter()
        else:
            chosen, votes = pick_decks(wvecs, list(decks), page_vecs)
        if not chosen:
            print(f"{stem}: no matching slides found, skipped (set it in lecture_map)")
            continue
        sections = align_one(wins, wvecs, decks, page_vecs, chosen)
        page_texts = {(s["deck"], s["page"]): decks[s["deck"]][s["page"] - 1]["text"] for s in sections}
        (aligned_dir / f"{stem}.json").write_text(json.dumps({
            "video": stem, "decks": chosen, "votes": dict(votes),
            "sections": [{**s, "slide_text": page_texts[(s["deck"], s["page"])]} for s in sections],
        }, ensure_ascii=False, indent=1))
        out = c["out"] / f"{stem}.md"
        out.write_text(to_markdown(stem, chosen, sections, decks))
        print(f"{stem}: decks {chosen}, {len(sections)} sections -> {out}")
