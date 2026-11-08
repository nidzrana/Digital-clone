import json
import os
import pathlib
from urllib.parse import quote

import streamlit as st  # pyright: ignore[reportMissingImports]

st.set_page_config(page_title="Nida's AI Clone", page_icon="🤖", layout="wide")

# Streamlit secrets -> environment variables (keys are never in the code or repo).
try:
    for _k in ("GROQ_API_KEY", "GROQ_MODEL", "HF_TOKEN", "LLM_MODEL"):
        if _k in st.secrets and _k not in os.environ:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass  # no secrets file locally: fall back to real environment variables

from core import EMPTY_PANEL, EXAMPLES, HAS_LLM, INTRO, MODES, respond  # noqa: E402


def _stats():
    """Live numbers for the stats row (notes, chunks) read from the index."""
    try:
        path = pathlib.Path(__file__).resolve().parent / "chunks.json"
        data = json.load(open(path, encoding="utf-8"))
        return len({c["source"] for c in data}), len(data)
    except Exception:
        return "-", "-"


N_NOTES, N_CHUNKS = _stats()

# ---------- Header artwork ----------
# Illustrated girl avatar (generic, original artwork), drawn in code. No photo file is used.
_AVATAR_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<rect width='100' height='100' fill='#F3DDE3'/>
<path d='M24 58C19 28 36 12 50 12C64 12 81 28 76 58L77 90L23 90Z' fill='#2B1B1B'/>
<path d='M12 100C15 78 33 72 50 72C67 72 85 78 88 100Z' fill='#7B1E3A'/>
<rect x='43' y='62' width='14' height='14' rx='5' fill='#E2AE8E'/>
<ellipse cx='50' cy='46' rx='19' ry='22' fill='#EDBB9C'/>
<path d='M30 45C29 26 41 19 51 19C61 19 71 27 70 45C62 37 53 33 45 28C41 35 35 41 30 45Z' fill='#2B1B1B'/>
<circle cx='43' cy='48' r='1.9' fill='#2B1B1B'/>
<circle cx='57' cy='48' r='1.9' fill='#2B1B1B'/>
<path d='M44 56Q50 61.5 56 56' stroke='#9B4A4A' stroke-width='2' fill='none' stroke-linecap='round'/>
</svg>"""

_WARN_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='#3B0A1C' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'>
<path d='M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z'/>
<line x1='12' y1='9' x2='12' y2='13'/><line x1='12' y1='17' x2='12.01' y2='17'/></svg>"""


def _svg_src(svg: str) -> str:
    return "data:image/svg+xml;utf8," + quote(svg)


AVATAR_SRC = _svg_src(_AVATAR_SVG)
WARN_SRC = _svg_src(_WARN_SVG)

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap');

/*
  Palette
  wine       #7B1E3A   primary actions, user bubbles, accents
  wine-deep  #3B0A1C   hero surface
  sage-teal  #4E7064   secondary accent
  amber      #F0B24A   warning badge
  mist       #F2F4F1   page background (cool, not yellow)
  white      #FFFFFF   cards, bubbles, inputs
  ink        #1F1A1C   text
*/
:root {
  --ink: #1F1A1C;
  --muted: #5E666A;
  --wine: #7B1E3A;
  --wine-hover: #62152D;
  --wine-deep: #3B0A1C;
  --rose: #F8EBEE;
  --sage: #4E7064;
  --amber: #F0B24A;
  --mist: #F2F4F1;
  --well: #E6EAE4;
  --card: #FFFFFF;
  --line: #DCE1DB;
  --on-dark: #FFFFFF;
  --on-dark-muted: #DCC6CD;
  --focus: rgba(123, 30, 58, .20);
  --shadow-sm: 0 1px 2px rgba(31,26,28,.06);
  --shadow-md: 0 1px 2px rgba(31,26,28,.05), 0 10px 28px -16px rgba(59,10,28,.30);
}

html, body, .stApp, p, label, li, summary, button, input, textarea,
div[data-testid="stMarkdownContainer"] {
  font-family: 'Hanken Grotesk', system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: var(--ink);
}
/* keep Streamlit's icon font so arrows render as icons, not text */
span[data-testid="stIconMaterial"],
.material-icons, .material-symbols-rounded, .material-symbols-outlined {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
}

.stApp {background: var(--mist);}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {display: none;}
.block-container {max-width: 1280px; padding: 2rem 2.5rem 3rem;}

/* keyboard focus */
button:focus-visible, input:focus-visible, summary:focus-visible {
  outline: 2px solid var(--wine); outline-offset: 2px;
}

/* ---------- Header card ---------- */
.hero {
  position: relative; overflow: hidden;
  background-color: var(--wine-deep);
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 32px 32px;
  border-radius: 20px; padding: 32px 36px 28px; margin-bottom: 24px;
  box-shadow: inset 0 5px 0 var(--sage), var(--shadow-md);
}
.hero-top {display: flex; align-items: center; gap: 24px;}
.avatar {
  width: 92px; height: 92px; border-radius: 50%; flex: none; overflow: hidden;
  background: #F3DDE3;
  box-shadow: 0 0 0 4px var(--wine-deep), 0 0 0 7px rgba(255,255,255,.28);
}
.avatar img {width: 100%; height: 100%; object-fit: cover; display: block; margin: 0;}
.hero h1 {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif; font-weight: 800;
  font-size: 2.6rem; line-height: 1.05; letter-spacing: -.025em;
  margin: 0; padding: 0; color: var(--on-dark);
}
.hero .sub {color: var(--on-dark-muted); font-size: 1.05rem; font-weight: 400; margin-top: 8px;}

.notice {
  display: flex; align-items: center; gap: 14px; margin-top: 26px;
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14);
  border-radius: 12px; padding: 12px 16px; font-size: .93rem; line-height: 1.4; color: var(--on-dark);
}
.notice .badge {
  display: inline-flex; align-items: center; gap: 6px; flex: none;
  background: var(--amber); color: var(--wine-deep); font-weight: 800; font-size: .74rem;
  letter-spacing: .06em; border-radius: 8px; padding: 6px 10px 6px 8px;
}
.notice .badge img {width: 16px; height: 16px; display: block; margin: 0;}
.notice b {color: var(--on-dark);}
.notice span.t {display: block; color: var(--on-dark-muted); font-size: .86rem; margin-top: 2px;}
.notice span.warn {display: block; color: var(--amber); font-weight: 300; font-size: .86rem; margin-top: 5px;}

/* ---------- Stats row ---------- */
.stats {display: flex; gap: 14px; margin-top: 18px;}
.stat {
  flex: 1; text-align: left; padding: 14px 18px;
  background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.12); border-radius: 14px;
}
.stat .n {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif; font-weight: 700;
  font-size: 2.1rem; color: var(--on-dark); line-height: 1.05; letter-spacing: -.02em;
}
.stat .l {font-size: .78rem; color: var(--on-dark-muted); letter-spacing: .04em; text-transform: uppercase; margin-top: 5px;}

/* ---------- Chat window ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stChatMessage"]) {
  background: var(--card); border: 1px solid var(--line); border-radius: 18px; box-shadow: var(--shadow-md);
}
div[data-testid="stChatMessage"] {
  background: var(--mist); border: 1px solid var(--line);
  border-radius: 16px 16px 16px 4px; padding: .8rem 1.05rem;
  width: fit-content; max-width: 88%; margin-bottom: .8rem; line-height: 1.6;
}
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {display: none;}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: var(--wine); border: none; border-radius: 16px 16px 4px 16px; margin-left: auto;
  box-shadow: var(--shadow-sm);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) * {color: #fff !important;}
div[data-testid="stChatMessage"] strong {color: var(--wine);}

/* ---------- Input row ---------- */
div[data-testid="stForm"] {border: none; padding: 0;}
div[data-testid="stForm"] div[data-baseweb="input"] {
  background: var(--card); border: 1.5px solid var(--line); border-radius: 12px;
  box-shadow: var(--shadow-sm); transition: border-color .15s, box-shadow .15s;
}
div[data-testid="stForm"] div[data-baseweb="input"]:focus-within {
  border-color: var(--wine); box-shadow: 0 0 0 4px var(--focus);
}
div[data-testid="stForm"] input {
  background: transparent; border: none; padding: .8rem 1rem; outline: none; box-shadow: none;
}
div[data-testid="stForm"] input::placeholder {color: var(--muted); opacity: .8;}
div[data-testid="stFormSubmitButton"] button {
  background: var(--wine); color: #fff; border: 1px solid var(--wine); border-radius: 12px;
  font-weight: 600; width: 100%; min-height: 3rem;
  box-shadow: var(--shadow-sm); transition: background .15s, border-color .15s;
}
div[data-testid="stFormSubmitButton"] button p {color: #fff !important;}
div[data-testid="stFormSubmitButton"] button:hover {background: var(--wine-hover); border-color: var(--wine-hover); color: #fff;}

/* ---------- Example chips ---------- */
div[data-testid="stCaptionContainer"] {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif; font-size: 1.2rem; font-weight: 600;
  color: var(--ink); margin-top: .5rem;
}
.stButton > button {
  border-radius: 12px; border: 1px solid var(--line); background: var(--card); color: var(--ink);
  font-size: .88rem; font-weight: 500; padding: .6rem .9rem; width: 100%; text-align: left;
  white-space: normal; height: auto; min-height: 3rem; line-height: 1.3;
  box-shadow: var(--shadow-sm);
  transition: border-color .15s, color .15s, background .15s;
}
.stButton > button p {white-space: normal; overflow: visible; text-overflow: clip; color: inherit;}
.stButton > button div {overflow: visible; text-overflow: clip; white-space: normal;}
.stButton > button:hover {border-color: var(--wine); color: var(--wine); background: var(--rose);}
.stButton > button:active {background: #F1DDE2;}

/* ---------- Mode toggle ---------- */
div[data-testid="stRadio"] > label p {color: var(--muted); font-weight: 600; font-size: .9rem;}
div[data-testid="stRadio"] [role="radiogroup"] {
  background: var(--well); border-radius: 999px; padding: 4px; display: inline-flex; gap: 2px;
}
div[data-testid="stRadio"] label {border-radius: 999px; padding: 5px 16px; margin: 0; transition: background .15s;}
div[data-testid="stRadio"] label:has(input:checked) {background: var(--wine); box-shadow: var(--shadow-sm);}
div[data-testid="stRadio"] label:has(input:checked) p {color: #fff; font-weight: 700;}
div[data-testid="stRadio"] label > div:first-child {display: none;}

/* ---------- Expanders ---------- */
div[data-testid="stExpander"] {
  background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--wine);
  border-radius: 14px; overflow: hidden; box-shadow: var(--shadow-md);
}
div[data-testid="stExpander"] summary {font-weight: 600; color: var(--ink);}
div[data-testid="stExpander"] summary:hover {color: var(--wine);}
div[data-baseweb="slider"] div[role="slider"] {background: var(--wine); box-shadow: 0 0 0 4px var(--focus);}
div[data-testid="stAlert"] {border-radius: 12px;}
div[data-testid="stSpinner"] {color: var(--wine); font-weight: 600;}
code {background: var(--well) !important; color: var(--ink) !important; border-radius: 5px;}

/* quiet scrollbars */
* {scrollbar-width: thin; scrollbar-color: #B8C0B6 transparent;}

.foot {text-align: center; color: var(--muted); font-size: .82rem; padding: 22px 0 4px;}

@media (max-width: 900px) {.block-container {padding: 1rem 1rem 3rem;}}
@media (max-width: 640px) {
  .hero {padding: 22px 18px 20px;}
  .hero-top {gap: 16px;}
  .hero h1 {font-size: 1.6rem;}
  .hero .sub {font-size: .95rem;}
  .avatar {width: 64px; height: 64px; box-shadow: 0 0 0 3px var(--wine-deep), 0 0 0 5px rgba(255,255,255,.28);}
  .notice {align-items: flex-start;}
  .stats {gap: 8px;}
  .stat {padding: 10px 10px;}
  .stat .n {font-size: 1.45rem;}
  .stat .l {font-size: .62rem;}
  div[data-testid="stRadio"] [role="radiogroup"] {flex-wrap: wrap; border-radius: 18px;}
}
</style>
"""

HERO = f"""
<div class="hero">
  <div class="hero-top">
    <div class="avatar"><img src="{AVATAR_SRC}" alt="Nida"></div>
    <div>
      <h1>Nida Farooq Rana</h1>
      <div class="sub">I am Nida's AI clone</div>
    </div>
  </div>
  <div class="notice">
    <span class="badge"><img src="{WARN_SRC}" alt="Warning"></span>
    <div><b>AI clone, not the real Nida.</b>
    <span class="t">Answers are generated only from my notes. Ask what you want to know about Nida.</span>
    <span class="warn">&#9888; Private information is not revealed.</span></div>
  </div>
  <div class="stats">
    <div class="stat"><div class="n">{N_NOTES}</div><div class="l">notes</div></div>
    <div class="stat"><div class="n">{N_CHUNKS}</div><div class="l">chunks indexed</div></div>
    <div class="stat"><div class="n">{len(MODES)}</div><div class="l">search modes</div></div>
  </div>
</div>
"""

st.markdown(STYLE + HERO, unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("history", [{"role": "assistant", "content": INTRO}])
ss.setdefault("panel", EMPTY_PANEL)
ss.setdefault("pending", None)
ss.setdefault("typed", None)

mode = ss.get("mode", "Hybrid (RRF)")
k = ss.get("k", 4)

question = ss.typed or ss.pending
ss.typed = ss.pending = None
if question:
    with st.spinner("Searching my notes..."):
        ss.history, _, ss.panel = respond(question, ss.history, mode, k)

left, right = st.columns([3, 2], gap="large")

with left:
    # chat window
    with st.container(height=520, border=True):
        for m in ss.history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    # input row
    with st.form("ask_form", clear_on_submit=True, border=False):
        c1, c2 = st.columns([6, 1])
        text = c1.text_input("Your question", placeholder="Ask me anything...", label_visibility="collapsed")
        if c2.form_submit_button("Ask") and text.strip():
            ss.typed = text.strip()
            st.rerun()

    st.caption("Try asking")
    cols = st.columns(2)
    for i, (emoji, q) in enumerate(EXAMPLES):
        if cols[i % 2].button(f"{emoji} {q}", key=f"ex{i}", help=q):
            ss.pending = q
            st.rerun()

with right:
    st.radio("Search mode", MODES, index=2, horizontal=True, key="mode")

    with st.expander("How I found this answer: sources and scores", expanded=True):
        with st.container(height=470, border=False):
            st.markdown(ss.panel, unsafe_allow_html=True)

    with st.expander("More settings"):
        st.slider("Chunks to retrieve (top-k)", 1, 8, 4, key="k")
        if st.button("Clear chat"):
            ss.history = [{"role": "assistant", "content": INTRO}]
            ss.panel = EMPTY_PANEL
            st.rerun()

if not HAS_LLM:
    st.warning("No LLM key configured: showing the closest note instead of a generated answer.")
st.markdown('<div class="foot">Hybrid RAG · BM25 + dense embeddings + Reciprocal Rank Fusion</div>',
            unsafe_allow_html=True)