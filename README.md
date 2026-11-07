# Digital Clone (Hybrid RAG): AI clone, not the real person

An AI clone of **Nida Farooq Rana** (final-year BSCS, UMT Sialkot). It answers in the first person, using only documents I wrote about myself.
**This is an AI clone, not the real person.**

- **Live app:** `https://nida-ai-clone.streamlit.app/'
- **Hosting note:** deployed on Streamlit Community Cloud from this GitHub repo (Streamlit instead of a Hugging Face Space was approved by my instructor).
- **Secrets:** the LLM key is stored as a Streamlit secret (`GROQ_API_KEY`), never in the code or repo.

## 1. Knowledge base and why
Eight first-person Markdown files in `data/` (about 2,400 words), all written by me, with no phone number, address, ID number or private details of other people:

| File | What it holds | Why |
|---|---|---|
| `bio.md` | Who I am, education, interests | Basic identity questions |
| `cv.md` | Education, skills, experience, achievements | Factual, keyword-rich (names, tools, dates) |
| `projects.md` | SentinelGuard, MindBridge, Campus Marketplace, Kharchay, research paper | Long-form project detail |
| `sentinelguard.md` | My part of the final year project | Technical questions (ESP32, MQTT, fail-safes) |
| `opinions.md` | Personality, books, music, food, travel, views on AI | Personal, paraphrase-style questions |
| `how_i_work.md` | Study habits, deadlines, advice for juniors | "How do you work" questions |
| `sports.md` | Table tennis, football | Hobby questions |
| `faq.md` | About 30 first-person Q&As | Direct questions people actually ask |

**Chunking:** about 200 words per chunk with 30 words of overlap. Each chunk keeps its source file name and a chunk ID (for example `faq-3`), which the app shows in the sources panel. The result is 18 chunks.

## 2. Pipeline
1. **Chunk** the documents (`build_index.py`) and save `chunks.json`.
2. **BM25** keyword search with `rank_bm25`.
3. **Dense search** with `all-MiniLM-L6-v2`. Chunk embeddings are computed once and saved in `embeddings.npy`. Queries are embedded at runtime and scored by cosine similarity with numpy.
4. **Reciprocal Rank Fusion:** `score = sum of 1 / (60 + rank)` over the two rankings (top 20 of each).
5. **Generation:** the top 3 chunks go to the LLM (Groq, `openai/gpt-oss-20b`) with a first-person persona prompt. It must answer only from the context and say "I don't have that in my notes" otherwise.

An alternative I did not use is weighted fusion, `alpha * dense + (1 - alpha) * bm25`, after min-max normalisation. RRF needs no score scaling and has no weight to tune.

**Extras:**
- Query rewriting for short or follow-up questions.
- Intent routing, so greetings and "help" do not trigger a search.
- Short conversation memory.
- A mode selector (BM25 / Dense / Hybrid) and a sources panel showing each chunk's file, chunk ID, score and BM25/dense ranks.

## 3. Test questions (`python eval.py`, top 3 chunks per mode, raw question without query rewriting)
| Question | BM25 result | Dense result | Hybrid result | Best mode and why |
|---|---|---|---|---|
| Q1. What is MQTT used for? (exact rare keyword) | `sentinelguard-0`, `faq-3`: both mention MQTT | `faq-3`, `sentinelguard-0`, `cv-0` | `faq-3`, `sentinelguard-0`, `cv-0` | **BM25 / Hybrid.** "MQTT" is a rare exact token, so keyword search nails it. Dense adds a weaker third chunk (`cv-0`). |
| Q2. How do you unwind? (paraphrase, no shared words) | nothing: no chunk shares a word with the question | `faq-1` (0.113, weak) | `faq-1` | **Dense / Hybrid.** Only embeddings connect "unwind" to relaxing and reading. BM25 returns zero results. |
| Q3. What do you do when a submission date is close? | `faq-5`, `how_i_work-0` | `faq-5`, `how_i_work-0` | `faq-5`, `how_i_work-0` | **All equal.** All modes find the deadline notes. |
| Q4. Which cyber attacks did your paper cover? | `faq-4`, `projects-1`, `faq-3` | `projects-1`, `cv-1`, `cv-0` | `projects-1`, `faq-4`, `cv-0` | **Hybrid.** It combines BM25's `faq-4` with dense's `projects-1` and ranks both at the top. |
| Q5. Which university course did you enjoy most? | `faq-5`, `how_i_work-1`, `how_i_work-0` | `how_i_work-1`, `faq-0`, `faq-5` | `how_i_work-1`, `faq-5`, `faq-0` | **Dense / Hybrid.** The question says "course" but my notes say "favourite subject: Operating Systems". All five chunks that mention Operating Systems are relevant, and dense puts the best one first. |

**Summary:** BM25 is strongest on exact keywords (Q1) and fails completely on paraphrases (Q2). Dense handles paraphrases but its scores are low and noisy (Q2 is only 0.113, and Q1/Q4 add weaker chunks). Hybrid (RRF) was never worse than the better of the two and was best or tied on every question, which is why it is the default.

## 4. Failure case
**Question:** "How do you unwind?"

**What happened:** with the raw question, BM25 returned nothing, because my notes say "doing nothing", "switch off" and "pick up a book", and share no words with "unwind". Dense search found `faq-1`, but only at a similarity of 0.113, barely above the cutoff (`MIN_DENSE = 0.10`) that I use to drop unrelated chunks. At my first cutoff of 0.12 even dense returned nothing, so the clone would have said "I don't have that in my notes" about a question my notes do answer.

**Why:** a vocabulary gap (BM25) plus long, multi-topic chunks that dilute the embedding similarity (dense). Off-topic questions such as "Who won the cricket world cup?" scored higher in dense search (0.142) than this on-topic one, so no similarity cutoff can separate them. The LLM prompt (answer only from the notes) handles those.

**Fix:** query rewriting in the app. For short or vague questions, the LLM expands the query into a few related keywords before retrieval, so "How do you unwind" also searches for words like relax and free time. With this the clone answers correctly: "I usually just do nothing, lie around and switch off. When I feel like doing something, I pick up a book." I also lowered `MIN_DENSE` from 0.12 to 0.10 so the question still works if the LLM call is unavailable.

## 5. Next improvement
Add a **cross-encoder reranker** that rescores the top 10 fused chunks before they go to the LLM. It would fix cases where the right chunk is retrieved but ranked third or fourth. I would also build a small hit@3 evaluation set (20 questions with known answer chunks) to measure BM25, Dense and Hybrid with numbers, and increase the embedding model's max sequence length so longer chunks are fully embedded.

## 6. Run locally
```
pip install -r requirements.txt
python build_index.py
set GROQ_API_KEY=your_key       (PowerShell: $env:GROQ_API_KEY="your_key")
streamlit run streamlit_app.py
```

## 7. Privacy and security
- All documents in `data/` are written by me about myself. They contain no phone number, address, ID number, or private details about other people.
- The clone refuses to share private details such as phone numbers, and says "I don't have that in my notes" for questions its notes do not answer.
- The LLM API key is stored only as a Streamlit secret (`GROQ_API_KEY`). It is not in the code, the data files or this repo.
