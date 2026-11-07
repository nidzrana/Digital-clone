"""Clone logic (retrieval + LLM), UI-independent."""
import html
import os
import re

import requests

from retrieval import MODES, retrieve

NAME = "Nida Farooq Rana"
# Keys come from environment variables / Space secrets, never from code.
GROQ_KEY = os.environ.get("GROQ_API_KEY")  # free tier at console.groq.com
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
HF_TOKEN = os.environ.get("HF_TOKEN")  # fallback: Hugging Face Inference API
MODEL_ID = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
client = None
if HF_TOKEN:
    from huggingface_hub import InferenceClient
    client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)
HAS_LLM = bool(GROQ_KEY or client)

NO_ANSWER = "I don't have that in my notes."

INTRO = (
    f"Hi! I'm the AI clone of {NAME}. Not the real Nida, just a bot that answers from her notes. 🙂\n\n"
    "You can ask me about:\n"
    "- **My projects**: SentinelGuard (FYP), MindBridge, Campus Marketplace, Kharchay, my research paper\n"
    "- **Studies and work habits**: my favourite subject, how I study, deadlines, advice for juniors\n"
    "- **Books and music**: Peer-e-Kamil, thrillers, what I'm reading\n"
    "- **Food, travel and hobbies**: comfort food, places I want to visit, baking, table tennis\n"
    "- **Career**: what internship I'm looking for\n\n"
    "Tap a bubble below, or just type a question."
)

EXAMPLES = [
    ("🚀", "What is your final year project?"),
    ("🧠", "What is MindBridge?"),
    ("📚", "What are you reading right now?"),
    ("🍛", "What's your comfort food?"),
    ("⏰", "How do you handle deadlines?"),
    ("🛡️", "Which cyber attacks did your paper cover?"),
    ("🏓", "Do you play any sports?"),
    ("💼", "What kind of internship are you looking for?"),
]

GREET = re.compile(
    r"^\s*(hi+|hello+|hey+|hola|salam|assalam[\w\s-]*|aoa|yo|sup|"
    r"good\s+(morning|evening|afternoon|night)|how are you.*|what'?s up.*)\W*$", re.I)
HELP = re.compile(
    r"^\s*(help|menu|topics?|what can i (ask|talk).*|what can you (do|talk).*|"
    r"who are you|what are you)\W*$", re.I)
THANKS = re.compile(
    r"^\s*(thanks?|thank you.*|thx|ok(ay)?|cool|nice|great|awesome|bye|goodbye|see you.*)\W*$", re.I)
FOLLOWUP = re.compile(r"\b(it|that|this|those|them|more|why|else|also|again)\b", re.I)

REWRITE_PROMPT = """You rewrite a user's message into a search query for a personal knowledge base about {name} (a CS student).
- Use the previous questions to resolve follow-ups like "tell me more" or "why?".
- If the message is short or vague, add at most 4 specific keywords or synonyms that would appear in a personal answer (example: "food?" -> "favourite food comfort meal burger"). Never add generic words like overview, details, description, title, information or topic.
- In the user's message, "my" or "your" both mean {name}.
Output ONLY the search query on one line, no explanation.

Previous questions: {prev}
User message: {msg}
Search query:"""

PERSONA = f"""You are the AI clone of {NAME}, a final-year Computer Science student at UMT Sialkot.
Speak in the first person ("I"). Voice: casual, warm, a little shy and humble. Short natural sentences, 1 to 4 sentences, like chatting with a friend. No bullet points, no headings, no markdown, no CV-style lists.

Rules:
1. Answer ONLY using the CONTEXT below. It comes from my own notes. The context may contain several unrelated topics: use only the part that answers the question and ignore the rest. Answer just what was asked, never list other topics.
1b. Never mention file names, chunk IDs, "context" or "notes files" in your answer.
2. If the context does not contain the answer, say: "{NO_ANSWER}" You may then suggest a topic you can talk about. Do not guess or invent facts about me.
3. Never share phone numbers, emails, addresses, ID numbers or other private details.
4. If asked whether you are the real person, say you are an AI clone of {NAME}.
5. If the question is vague (one or two words), answer from the most relevant context, or ask which topic they mean.
6. "my" or "your" in the user's question both mean me.

CONTEXT:
<<CONTEXT>>"""


# ----------------------------------------------------------------- helpers
def clean(text, n=450):
    t = re.sub(r"#+\s*", "", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("..." if len(t) > n else "")


_SKIP = {"what", "your", "about", "have", "does", "tell", "with", "that", "this", "from",
         "they", "them", "where", "when", "which", "were", "will", "would", "could", "should", "much"}
_SKIP_ALL = _SKIP | set(NAME.lower().split())


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _query_words(query):
    return {w for w in _words(query) if len(w) > 3 and w not in _SKIP_ALL}


def _sentences(text):
    flat = re.sub(r"\s+", " ", re.sub(r"#+\s*", "", text))
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


def _best_in(qwords, text):
    """(score, two-sentence snippet) for the part of `text` that best matches the query words."""
    sents = _sentences(text)
    if not sents:
        return -1, ""
    scores = [len(qwords & set(_words(s))) for s in sents]
    i = max(range(len(sents)), key=scores.__getitem__)
    return scores[i], " ".join(sents[i:i + 2])


def snippet(query, text, n=220):
    """The 1-2 sentences of a chunk that best match the query (name words ignored)."""
    return _best_in(_query_words(query), text)[1][:n]


def best_snippet(query, hits, n=300):
    """Fallback when no LLM: the best-matching sentence(s) across the top hits, not the chunk start."""
    if not hits:
        return NO_ANSWER
    qwords = _query_words(query)
    best, best_score = "", -1
    for h in hits[:3]:
        score, text = _best_in(qwords, h["text"])
        if score > best_score:
            best, best_score = text, score
    return (best or clean(hits[0]["text"], n))[:n]


def llm(messages, max_tokens=300, temperature=0.3):
    if GROQ_KEY:
        payload = {"model": GROQ_MODEL, "messages": messages,
                   "max_tokens": max_tokens, "temperature": temperature}
        if "gpt-oss" in GROQ_MODEL:  # reasoning model: keep thinking short, leave room for the answer
            payload["reasoning_effort"] = "low"
            payload["max_tokens"] = max_tokens + 400
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json=payload,
            timeout=40,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise RuntimeError("The Groq API returned no message content")
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
        return content.strip()
    if client is None:
        raise RuntimeError("HF_TOKEN is not configured")
    r = client.chat_completion(messages=messages, max_tokens=max_tokens, temperature=temperature)
    content = r.choices[0].message.content
    if content is None:
        raise RuntimeError("The Hugging Face Inference API returned no message content")
    return content.strip()


def real_history(history):
    """Conversation without the welcome message."""
    return [m for m in (history or []) if m.get("content") != INTRO]


def build_query(message, history):
    """Query rewriting: expand short/vague questions, resolve follow-ups. Keeps original words for BM25."""
    if not HAS_LLM:
        return message
    if len(message.split()) >= 5 and not FOLLOWUP.search(message):
        return message  # clear question: search with the user's own words
    prev = [m["content"] for m in real_history(history) if m["role"] == "user"][-2:]
    try:
        out = llm(
            [{"role": "user", "content": REWRITE_PROMPT.format(
                name=NAME, prev=" | ".join(prev) or "none", msg=message)}],
            max_tokens=60, temperature=0.0,
        )
        out = out.splitlines()[0].strip(" \"'") if out else ""
        if 3 <= len(out) <= 300:
            return f"{message} {out}"
    except Exception:
        pass
    return message


def generate(message, history, hits):
    if not hits:  # nothing retrieved: don't call the LLM or index into an empty list
        return NO_ANSWER + " Try asking about my projects, books, food or study habits."
    # Every retrieved chunk (top-k from the slider) goes to the model, in rank order.
    # No file names or chunk IDs in the prompt, so the model has nothing to cite.
    context = "\n\n---\n\n".join(h["text"] for h in hits)
    if not HAS_LLM:
        return "(No API key set, showing the closest note instead.) " + best_snippet(message, hits)
    msgs = [{"role": "system", "content": PERSONA.replace("<<CONTEXT>>", context)}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in real_history(history)[-4:]]
    msgs.append({"role": "user", "content": message})
    try:
        return llm(msgs, max_tokens=250, temperature=0.3)
    except Exception as e:
        err = str(e)[:120]
        return ("(The language model is unavailable right now: " + err + ") "
                "Closest note I have: " + best_snippet(message, hits))


def panel_md(query, hits):
    lines = [f"**Search query used:** `{query}`\n"]
    if not hits:
        lines.append("_No matching notes were found._")
    for h in hits:
        lines.append(
            f"**#{h['rank']} · `{h['source']}` · {h['chunk_id']}** · score `{h['score']}` "
            f"(BM25 rank {h['bm25_rank']}, dense rank {h['dense_rank']})\n\n"
            f"> {snippet(query, h['text'])}\n\n"
            f"<details><summary>Show full chunk</summary>\n\n{html.escape(clean(h['text'], 3000))}\n\n</details>"
        )
    return "\n\n".join(lines)


EMPTY_PANEL = "_Ask me something and I'll show which notes I used, with their source file and score._"


def respond(message, history, mode, k):
    message = (message or "").strip()
    history = history or []
    if not message:
        return history, "", EMPTY_PANEL
    prior = list(history)
    history = history + [{"role": "user", "content": message}]

    if GREET.match(message) or HELP.match(message):
        reply, panel = INTRO, "_No search needed for a greeting._"
    elif THANKS.match(message):
        reply = "Anytime! Ask me anything else about my projects, books, food or study habits."
        panel = "_No search needed._"
    else:
        query = build_query(message, prior)
        hits = retrieve(query, mode, int(k))
        reply = generate(message, prior, hits)
        panel = panel_md(query, hits)

    history.append({"role": "assistant", "content": reply})
    return history, "", panel


def reset():
    return [{"role": "assistant", "content": INTRO}], "", EMPTY_PANEL