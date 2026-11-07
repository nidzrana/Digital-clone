""" chunk data/ -> chunks.json + embeddings.npy. Commit both files."""
import json
import re
from pathlib import Path

import numpy as np  # type: ignore[reportMissingImports]
from sentence_transformers import SentenceTransformer  # type: ignore[reportMissingImports]

DATA = Path(__file__).resolve().parent / "data"
CHUNK_WORDS, OVERLAP = 200, 30
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def read_file(p: Path) -> str:
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader  # type: ignore[reportMissingImports]  # pip install pypdf (only needed locally)
        return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(p)).pages)
    return p.read_text(encoding="utf-8")


def chunk_words(text: str, size=CHUNK_WORDS, overlap=OVERLAP):
    words = re.sub(r"\s+", " ", text).strip().split(" ")
    step = size - overlap
    out = []
    for start in range(0, max(len(words), 1), step):
        piece = words[start:start + size]
        if len(piece) < 40 and out:  # merge tiny tail into previous chunk
            out[-1] += " " + " ".join(piece)
            break
        out.append(" ".join(piece))
        if start + size >= len(words):
            break
    return out


chunks = []
files = sorted(p for p in DATA.iterdir() if p.suffix.lower() in {".md", ".txt", ".pdf"})
assert files, "Put your .md/.txt/.pdf files in data/"
for p in files:
    for i, t in enumerate(chunk_words(read_file(p))):
        chunks.append({"source": p.name, "chunk_id": f"{p.stem}-{i}", "text": t})

print(f"{len(files)} files -> {len(chunks)} chunks")
model = SentenceTransformer(MODEL_NAME)
model.max_seq_length = 384
emb = model.encode(
    [c["text"] for c in chunks],
    normalize_embeddings=True,
    show_progress_bar=True,
    convert_to_numpy=True,
)
OUT = Path(__file__).resolve().parent
np.save(str(OUT / "embeddings.npy"), emb.astype(np.float32))
(OUT / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
print("Saved to", OUT)


