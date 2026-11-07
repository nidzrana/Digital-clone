"""BM25 + dense retrieval + Reciprocal Rank Fusion."""
import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RRF_K = 60       # constant in 1 / (60 + rank)
FUSE_TOP_N = 20  # only the top-N of each ranking contributes to RRF
MIN_DENSE = 0.10#cosine floor: chunks less similar than this are treated as unrelated (tune 0.15-0.30)
MAX_WORDS = 180   # all-MiniLM-L6-v2 reads ~256 tokens; longer chunks are cut off in dense search

# "no" and "not" are kept on purpose so negation survives in queries.
STOP = set("""a an the and or but of to in on at for with by from is are was were be been am
i me my we our you your it its this that these those as do does did so if then than
what which who whom how when where why can could would should will about into over under
s t d ll re ve m
""".split())  # last line: fragments left over from contractions (what's -> "what", "s")


def tokenize(text: str):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


chunks = json.loads((BASE / "chunks.json").read_text(encoding="utf-8"))
emb = np.load(BASE / "embeddings.npy")  # precomputed, L2-normalised

# Fail loudly if the two files drifted apart (e.g. notes edited, embeddings not rebuilt).
assert len(chunks) == emb.shape[0], (
    f"chunks.json has {len(chunks)} chunks but embeddings.npy has {emb.shape[0]} rows: "
    "re-run the embedding script so they match."
)

_long = [c["chunk_id"] for c in chunks if len(c["text"].split()) > MAX_WORDS]
if _long:
    print(f"[retrieval] Warning: {len(_long)} chunk(s) exceed {MAX_WORDS} words and are truncated "
          f"in dense search. Consider re-chunking: {_long[:5]}")

bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
model = SentenceTransformer(MODEL_NAME)

MODES = ["BM25 only", "Dense only", "Hybrid (RRF)"]


def bm25_scores(q):
    return np.array(bm25.get_scores(tokenize(q)))


def dense_scores(q):
    qv = model.encode([q], normalize_embeddings=True)[0]
    return emb @ qv  # cosine similarity (vectors are normalised)


def retrieve(q: str, mode: str, k: int = 4):
    b, d = bm25_scores(q), dense_scores(q)
    b_order, d_order = np.argsort(-b), np.argsort(-d)
    b_rank = {int(i): r + 1 for r, i in enumerate(b_order)}
    d_rank = {int(i): r + 1 for r, i in enumerate(d_order)}

    if mode == "BM25 only":
        order = [int(i) for i in b_order if b[i] > 0][:k]
        score = lambda i: b[i]
    elif mode == "Dense only":
        order = [int(i) for i in d_order if d[i] >= MIN_DENSE][:k]
        score = lambda i: d[i]
    else:  # Hybrid: Reciprocal Rank Fusion
        rrf = {}
        for i in range(len(chunks)):
            s = 0.0
            if d_rank[i] <= FUSE_TOP_N and d[i] >= MIN_DENSE:
                s += 1.0 / (RRF_K + d_rank[i])
            if b_rank[i] <= FUSE_TOP_N and b[i] > 0:
                s += 1.0 / (RRF_K + b_rank[i])
            rrf[i] = s
        order = [i for i in sorted(rrf, key=lambda i: rrf[i], reverse=True) if rrf[i] > 0][:k]
        score = lambda i: rrf[i]

    return [
        {
            "rank": n + 1,
            "source": chunks[i]["source"],
            "chunk_id": chunks[i]["chunk_id"],
            "score": round(float(score(i)), 4),
            "bm25_rank": b_rank[i],
            "dense_rank": d_rank[i],
            "text": chunks[i]["text"],
        }
        for n, i in enumerate(order)
    ]