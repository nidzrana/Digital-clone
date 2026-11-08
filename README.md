# Digital Clone (Hybrid RAG): AI clone, not the real person

An AI clone of **Nida Farooq Rana** (final-year BSCS, UMT Sialkot). It answers in the first person, using only documents I wrote about myself.
**This is an AI clone, not the real person.**

- **Live app:** 
- **Code:** https://github.com/nidzrana/Digital-clone
- **Hosting note:** deployed on Streamlit Community Cloud from this GitHub repo (Streamlit instead of a Hugging Face Space was approved by my instructor).
- **Secrets:** the LLM key is stored as a Streamlit secret (`GROQ_API_KEY`), never in the code or repo.

## 1. Knowledge base and why
Sixteen first-person Markdown files in `data/` (about 4,250 words, roughly 8 to 9 pages), all written by me. They contain no phone number, address, ID number, or names or private details of my family and friends.

| File | What it holds | Why |
|---|---|---|
| `bio.md` | Who I am, education, interests | Basic identity questions |
| `cv.md` | Education, skills, experience, achievements | Factual, keyword-rich (names, tools, dates) |
| `projects.md` | SentinelGuard, MindBridge, Campus Marketplace, Kharchay, research paper | Project overview |
| `projects_deep.md` | MindBridge, Campus Marketplace and Kharchay in detail | Long-form project write-up |
| `sentinelguard.md` | My part of the final year project | Technical questions (ESP32, MQTT, fail-safes) |
| `study_notes.md` | Operating Systems notes: Round Robin, Banker's algorithm | Study notes and technical vocabulary |
| `opinions.md` | Personality, books, music, food, travel, views on AI | Personal, paraphrase-style questions |
| `books_and_writers.md` | Why I love Umera Ahmad's writing | Opinion and paraphrase questions |
| `how_i_work.md` | Study habits, deadlines, advice for juniors | "How do you work" questions |
| `daily_routine.md` | My night routine | Daily-life questions |
| `teamwork.md` | How I work in a team | Teamwork questions |
| `wellbeing.md` | How I cope when I feel low | Personal, paraphrase-style questions |
| `values_and_goals.md` | Career goals, views, advice | Future-focused questions |
| `about_and_boundaries.md` | Basic facts and what I do not share | Privacy: makes the clone refuse politely |
| `sports.md` | Table tennis, football | Hobby questions |
| `faq.md` | About 30 first-person Q&As | Direct questions people actually ask |

**Chunking:** about 200 words per chunk with 30 words of overlap. Each chunk keeps its source file name and a chunk ID (for example `faq-3`), which the app shows in the sources panel. The result is 29 chunks.

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
| Q1. What is MQTT used for? (exact rare keyword) | `sentinelguard-0`, `faq-3`, `about_and_boundaries-0` | `faq-3`, `sentinelguard-0`, `projects_deep-0` | `faq-3`, `sentinelguard-0`, `projects_deep-1` | **BM25 / Hybrid.** "MQTT" is a rare exact token, so keyword search puts the two chunks that really explain it on top. BM25's third result is noise (no MQTT in it), and dense's third is only loosely related. |
| Q2. How do you unwind? (paraphrase, no shared words) | nothing: no chunk shares a word with the question | `daily_routine-0` (0.204), `books_and_writers-0`, `faq-1` | `daily_routine-0`, `books_and_writers-0`, `faq-1` | **Dense / Hybrid.** Only embeddings connect "unwind" to my night routine and reading. BM25 returns zero results. |
| Q3. What do you do when a submission date is close? | `faq-5`, `how_i_work-0`, `teamwork-0` | `faq-5`, `how_i_work-0`, `teamwork-0` | `faq-5`, `how_i_work-0`, `teamwork-0` | **All equal.** All modes find the two deadline notes first. The third chunk (`teamwork-0`) is related but weaker. |
| Q4. Which cyber attacks did your paper cover? | `faq-4`, `projects-1`, `projects_deep-2` | `projects-1`, `cv-1`, `projects_deep-2` | `projects-1`, `projects_deep-2`, `faq-4` | **Hybrid.** It keeps `projects-1` (best for dense) and `faq-4` (best for BM25) in its top 3, and leaves out `cv-1`. |
| Q5. Which university course did you enjoy most? | `faq-5`, `how_i_work-1`, `how_i_work-0` | `how_i_work-1`, `faq-0`, `faq-5` | `how_i_work-1`, `faq-5`, `faq-0` | **Dense / Hybrid.** The question says "course" but my notes say "favourite subject: Operating Systems". All of these chunks mention Operating Systems, and dense puts the best one first. |

**Summary:** BM25 is strongest on exact keywords (Q1) and fails completely on a paraphrase (Q2). Dense handles paraphrases but its scores are low, and some of its lower-ranked chunks are only loosely related. Hybrid (RRF) was never worse than the better of the two and was best or tied on every question, which is why it is the default.

## 4. Failure case
**Question:** "How do you unwind?"

**What happened:** with the raw question, BM25 returned nothing, because my notes say "doing nothing", "switch off", "pick up a book", and share no words with "unwind". Dense search was also weak at first. Before I added more notes, its best chunk (`faq-1`) scored only 0.113 and was barely above the similarity cutoff (`MIN_DENSE = 0.10`) that drops unrelated chunks. At my first cutoff of 0.12, even dense returned nothing, so the clone would have said "I don't have that in my notes" about a question my notes do answer.

**Why:** a vocabulary gap (BM25) plus long, multi-topic chunks that dilute the embedding similarity (dense). Off-topic questions such as "Who won the cricket world cup?" scored higher in dense search (0.142) than this on-topic one, so no similarity cutoff can separate them. The LLM prompt (answer only from the notes) handles those.

**Fix:** (1) Query rewriting in the app. For short or vague questions, the LLM expands the query into a few related keywords before retrieval, so "How do you unwind" also searches for words like relax and free time. With this the clone answers correctly: "I usually just do nothing, lie around and switch off. When I feel like doing something, I pick up a book." (2) I lowered `MIN_DENSE` from 0.12 to 0.10. (3) Adding focused notes (`daily_routine.md`, `books_and_writers.md`) raised the best dense score for this question from 0.113 to 0.204, which shows that more specific, plain-language notes help retrieval as much as tuning does. BM25 still returns nothing for this question without the rewrite.

## 5. Next improvement
Add a **cross-encoder reranker** that rescores the top 10 fused chunks before they go to the LLM. It would fix cases where the right chunk is retrieved but ranked third or fourth. I would also build a small hit@3 evaluation set (20 questions with known answer chunks) to measure BM25, Dense and Hybrid with numbers, and fix chunk length: 16 chunks are longer than about 180 words, so the embedding model truncates their tails. Splitting them at about 150 words would embed every chunk fully.

## 6. Run locally
```
pip install -r requirements.txt
python build_index.py
set GROQ_API_KEY=your_key       (PowerShell: $env:GROQ_API_KEY="your_key")
streamlit run streamlit_app.py
```

## 7. Privacy and security
- All documents in `data/` are written by me about myself. They contain no phone number, address, ID number, or names or private details of other people.
- A dedicated notes file (`about_and_boundaries.md`) tells the clone to refuse questions about family members' names, friends' names and contact details.
- The clone refuses to share private details such as phone numbers, and says "I don't have that in my notes" for questions its notes do not answer.
- The LLM API key is stored only as a Streamlit secret (`GROQ_API_KEY`). It is not in the code, the data files or this repo.