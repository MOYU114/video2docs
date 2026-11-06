import random

from v2d.align import align_one, pick_decks
from v2d.matching import TfIdf, tokens, viterbi, windows

TOPICS = {
    "lecture01": ["remote procedure call stub marshalling", "at most once semantics retransmission",
                  "idempotent operations duplicate requests", "failure detection timeout crash"],
    "lecture02": ["logical clock lamport timestamp", "vector clock causality happened before",
                  "snapshot chandy lamport marker channel", "global state consistent cut"],
    "lecture03": ["paxos proposer acceptor ballot", "quorum majority intersection",
                  "leader election view change", "replicated state machine log"],
}
FILLER = "so okay let us look at this now the idea here is basically".split()


def fake_lecture(decks, per_page=6, seed=0):
    rnd = random.Random(seed)
    segs, t = [], 0
    for d in decks:
        for page in TOPICS[d]:
            for _ in range(per_page):
                words = rnd.sample(page.split(), 2) + rnd.sample(FILLER, 5)
                segs.append({"start": t, "end": t + 10, "text": " ".join(words)})
                t += 10
    return segs


def setup(segs):
    decks = {n: [{"page": i + 1, "text": p} for i, p in enumerate(ps)] for n, ps in TOPICS.items()}
    wins = windows(segs, 30)
    page_toks = {n: [tokens(p["text"]) for p in ps] for n, ps in decks.items()}
    model = TfIdf([t for ts in page_toks.values() for t in ts] + [tokens(w["text"]) for w in wins])
    page_vecs = {n: [model.vec(t) for t in ts] for n, ts in page_toks.items()}
    wvecs = [model.vec(tokens(w["text"])) for w in wins]
    return decks, wins, wvecs, page_vecs


def test_windows_respect_length():
    segs = [{"start": i * 10, "end": i * 10 + 10, "text": str(i)} for i in range(10)]
    wins = windows(segs, 30)
    assert all(w["end"] - w["start"] <= 30 for w in wins)
    assert " ".join(w["text"] for w in wins).split() == [str(i) for i in range(10)]


def test_viterbi_prefers_forward_path_over_single_noisy_window():
    scores = [[0.9, 0.1, 0.1], [0.2, 0.25, 0.1], [0.1, 0.9, 0.1], [0.1, 0.1, 0.9]]
    assert viterbi(scores) == [0, 1, 1, 2]


def test_end_to_end_picks_decks_and_pages_in_order():
    decks, wins, wvecs, page_vecs = setup(fake_lecture(["lecture02", "lecture03"]))
    chosen, _ = pick_decks(wvecs, list(decks), page_vecs)
    assert chosen == ["lecture02", "lecture03"]
    sections = align_one(wins, wvecs, decks, page_vecs, chosen)
    assert [(s["deck"], s["page"]) for s in sections] == [
        (d, p) for d in chosen for p in range(1, 5)
    ]
