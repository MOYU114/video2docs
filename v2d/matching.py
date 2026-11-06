"""Transcript <-> slide-page matching (pure Python, no extra dependencies).

1. Split the transcript into fixed-length time windows.
2. Score every window against every slide page with TF-IDF cosine similarity.
3. Run Viterbi to find a mostly-forward path through the pages, which suppresses
   spurious jumps caused by a single shared keyword.
"""
from __future__ import annotations

import math
import re
from collections import Counter

STOP = set("""
a an the and or but if then else of to in on at by for with from as is are was were be been being
this that these those it its we you they i he she him her them our your their my me us so do does
did not no yes can could will would should may might just very really also there here what which
who whom how why when where all any some one two okay ok right yeah um uh like actually basically
going gonna get got have has had let lets thing things now well see know mean
""".split())
TOKEN = re.compile(r"[a-z][a-z0-9_]+")


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


class TfIdf:
    def __init__(self, docs: list[list[str]]):
        n = len(docs)
        df = Counter(t for d in docs for t in set(d))
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}

    def vec(self, toks: list[str]) -> dict[str, float]:
        tf = Counter(toks)
        v = {t: (1 + math.log(c)) * self.idf.get(t, 0.0) for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}


def cos(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())


def windows(segments: list[dict], seconds: float) -> list[dict]:
    out, cur = [], []
    for s in segments:
        if cur and s["end"] - cur[0]["start"] > seconds:
            out.append(cur)
            cur = []
        cur.append(s)
    if cur:
        out.append(cur)
    return [
        {"start": w[0]["start"], "end": w[-1]["end"], "text": " ".join(s["text"] for s in w)}
        for w in out
    ]


def viterbi(scores: list[list[float]], back_penalty=0.15, jump_penalty=0.02, stay_bonus=0.01):
    """scores[t][j] is the similarity of window t to page j; returns a page index per window.

    Transitions: staying on a page earns stay_bonus, moving forward to any later page
    costs jump_penalty, and going back costs back_penalty (lecturers do revisit
    slides, so it is allowed but discouraged).
    """
    T, J = len(scores), len(scores[0])
    best = list(scores[0])
    ptr: list[list[int]] = []
    for t in range(1, T):
        top = max(range(J), key=lambda k: best[k])
        new, p = [0.0] * J, [0] * J
        run_v, run_k = float("-inf"), -1  # max best[k] over k < j
        for j in range(J):
            cands = [(best[j] + stay_bonus, j), (best[top] - back_penalty, top)]
            if run_k >= 0:
                cands.append((run_v - jump_penalty, run_k))
            v, k = max(cands)
            new[j], p[j] = v + scores[t][j], k
            if best[j] > run_v:
                run_v, run_k = best[j], j
        best = new
        ptr.append(p)
    j = max(range(J), key=lambda k: best[k])
    path = [j]
    for p in reversed(ptr):
        j = p[j]
        path.append(j)
    return path[::-1]
