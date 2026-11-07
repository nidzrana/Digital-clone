import os

import streamlit as st  # pyright: ignore[reportMissingImports]

st.set_page_config(page_title="Nida's AI Clone", page_icon="🤖", layout="centered")

# Streamlit secrets -> environment variables (keys are never in the code or repo).
try:
    for _k in ("GROQ_API_KEY", "GROQ_MODEL", "HF_TOKEN", "LLM_MODEL"):
        if _k in st.secrets and _k not in os.environ:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass  # no secrets file locally: fall back to real environment variables

from core import EMPTY_PANEL, EXAMPLES, HAS_LLM, INTRO, MODES, respond  # noqa: E402

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --teal: #0f9d8a;
  --teal-dark: #0b6f62;
  --teal-deep: #0a4f47;
  --ink: #14332e;
  --muted: #5b7570;
  --mint: #e3f5f0;
  --line: #cfe3de;
  --sun: #ffb84d;
  --coral: #ff7a6b;
  --blue: #2b7fe0;
  --violet: #8b5cf6;
  --pink: #ec4899;
  --lime: #84cc16;
}

html, body, .stApp, p, label, li, summary, button, input, textarea,
h1, h2, h3, h4, div[data-testid="stMarkdownContainer"] {
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
/* keep Streamlit's icon font so arrows render as icons, not text */
span[data-testid="stIconMaterial"],
[data-testid="stExpander"] summary svg + span,
.material-icons, .material-symbols-rounded, .material-symbols-outlined {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
}

/* page background: soft colour pools instead of flat white */
.stApp {
  background:
    radial-gradient(800px 500px at 0% 0%, rgba(15,157,138,.30), transparent 60%),
    radial-gradient(700px 480px at 100% 5%, rgba(139,92,246,.26), transparent 60%),
    radial-gradient(700px 520px at 100% 60%, rgba(255,184,77,.26), transparent 60%),
    radial-gradient(800px 600px at 0% 100%, rgba(236,72,153,.20), transparent 60%),
    radial-gradient(600px 400px at 50% 50%, rgba(43,127,224,.10), transparent 60%),
    #f6f9ff;
  background-attachment: fixed;
}

#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {display: none;}
.block-container {max-width: 820px; padding-top: 1.2rem; padding-bottom: 3rem;}

/* ---------- Hero card ---------- */
.hero-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(120deg, #0f9d8a 0%, #2b7fe0 38%, #8b5cf6 70%, #ec4899 100%);
  border-radius: 22px;
  padding: 20px 24px;
  box-shadow: 0 22px 44px -16px rgba(139,92,246,.6), 0 2px 6px rgba(43,127,224,.2);
  margin-bottom: 16px;
  color: #fff;
  animation: heroIn .7s cubic-bezier(.2,.8,.2,1) both;
}
.hero-card::before, .hero-card::after {
  content: ""; position: absolute; border-radius: 50%; pointer-events: none;
}
.hero-card::before {
  width: 220px; height: 220px; right: -60px; top: -90px;
  background: radial-gradient(circle, rgba(255,184,77,.55), transparent 70%);
}
.hero-card::after {
  width: 180px; height: 180px; left: 38%; bottom: -110px;
  background: radial-gradient(circle, rgba(255,255,255,.18), transparent 70%);
}
@keyframes heroIn {
  from {opacity: 0; transform: translateY(10px) scale(.985);}
  to   {opacity: 1; transform: none;}
}

.hero-top {
  position: relative; z-index: 1;
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 14px; padding-bottom: 14px;
  border-bottom: 1px solid rgba(255,255,255,.22);
}
.avatar-wrap {position: relative; flex: none; width: 58px; height: 58px;}
.avatar-wrap::before {
  content: ""; position: absolute; inset: -4px; border-radius: 50%;
  background: conic-gradient(from 0deg, #ffb84d, #ff7a6b, #fff, #ffb84d);
  animation: spin 6s linear infinite;
}
@keyframes spin {to {transform: rotate(360deg);}}
.avatar {
  position: relative;
  width: 58px; height: 58px; border-radius: 50%;
  background: #fff; color: var(--teal-dark); flex: none;
  font-weight: 800; font-size: 24px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 0 3px rgba(43,127,224,.9);
}
.avatar-wrap .live {
  position: absolute; right: -1px; bottom: 1px; z-index: 2;
  width: 14px; height: 14px; border-radius: 50%;
  background: #5cf2a3; border: 2.5px solid #2b7fe0;
  animation: pulse 2s ease-out infinite;
}
@keyframes pulse {
  0%   {box-shadow: 0 0 0 0 rgba(92,242,163,.7);}
  100% {box-shadow: 0 0 0 10px rgba(92,242,163,0);}
}
.hero-top .title {
  font-size: 1.5rem; font-weight: 800; color: #fff;
  line-height: 1.15; letter-spacing: -.02em;
}
.hero-top .sub {
  font-size: .95rem; color: rgba(255,255,255,.85); margin-top: 3px;
}

.hero-notice {
  position: relative; z-index: 1;
  display: flex; align-items: center; gap: 14px;
  background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.25);
  backdrop-filter: blur(6px);
  border-radius: 14px;
  padding: 10px 14px;
  font-size: .92rem; line-height: 1.35; color: #fff;
}
.hero-notice .ico {
  font-size: 1.3rem; width: 38px; height: 38px; flex: none;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,.2); border-radius: 12px;
}
.hero-notice b {display: block; color: #fff; font-weight: 700;}
.hero-notice span.t {color: rgba(255,255,255,.82); font-size: .85rem;}

/* ---------- Chat window ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stChatMessage"]) {
  background: rgba(255,255,255,.85);
  backdrop-filter: blur(10px);
  border: 1.5px solid transparent;
  background-image: linear-gradient(rgba(255,255,255,.9), rgba(255,255,255,.9)), linear-gradient(135deg, #0f9d8a, #2b7fe0, #8b5cf6, #ec4899);
  background-origin: border-box; background-clip: padding-box, border-box;
  border-radius: 22px;
  box-shadow: 0 18px 38px -20px rgba(139,92,246,.5);
}

/* bubbles, no avatars (like the Gradio version) */
div[data-testid="stChatMessage"] {
  background: linear-gradient(135deg, #eafaf6, #eef3ff);
  border: 1px solid #d6e6ee;
  border-radius: 18px 18px 18px 4px;
  padding: .7rem 1.05rem;
  width: fit-content; max-width: 88%;
  margin-bottom: .7rem;
  box-shadow: 0 2px 8px -4px rgba(10,79,71,.18);
  animation: bubbleIn .35s cubic-bezier(.2,.8,.2,1) both;
}
@keyframes bubbleIn {
  from {opacity: 0; transform: translateY(8px) scale(.98);}
  to   {opacity: 1; transform: none;}
}
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {display: none;}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: linear-gradient(135deg, #12b39e, #2b7fe0 55%, #8b5cf6);
  border: none;
  border-radius: 18px 18px 4px 18px;
  margin-left: auto;
  box-shadow: 0 10px 20px -8px rgba(99,102,241,.65);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) * {color: #fff !important;}

/* ---------- Input row ---------- */
div[data-testid="stForm"] {border: none; padding: 0;}
div[data-testid="stForm"] input {
  background: #fff;
  border-radius: 14px;
  border: 1.5px solid var(--line);
  padding: .65rem .9rem;
  transition: border-color .15s, box-shadow .15s;
}
div[data-testid="stForm"] input:focus {
  border-color: var(--violet);
  box-shadow: 0 0 0 4px rgba(139,92,246,.2);
  outline: none;
}
div[data-testid="stFormSubmitButton"] button {
  background: linear-gradient(135deg, #2b7fe0, #8b5cf6 60%, #ec4899);
  color: #fff; border: none;
  border-radius: 14px; font-weight: 700; width: 100%;
  min-height: 2.7rem;
  box-shadow: 0 10px 20px -8px rgba(139,92,246,.7);
  transition: transform .12s, box-shadow .12s;
}
div[data-testid="stFormSubmitButton"] button:hover {
  background: linear-gradient(135deg, #3b8ff0, #9b6cff 60%, #f559a6); color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 14px 24px -8px rgba(139,92,246,.8);
}
div[data-testid="stFormSubmitButton"] button:active {transform: translateY(0);}

/* ---------- Example chips ---------- */
div[data-testid="stCaptionContainer"] {color: var(--muted); font-weight: 600;}
.stButton > button {
  border-radius: 16px;
  border: 1.5px solid var(--line);
  background: #fff;
  color: var(--teal-dark);
  font-size: .82rem; font-weight: 600;
  padding: .45rem .75rem;
  width: 100%; white-space: normal; height: auto;
  min-height: 2.8rem; line-height: 1.25;
  box-shadow: 0 2px 6px -3px rgba(10,79,71,.2);
  transition: transform .15s, box-shadow .15s, border-color .15s, background .15s;
}
.stButton > button p {white-space: normal;}
.stButton > button:hover {
  background: #f0fbf8; border-color: var(--teal); color: var(--teal-dark);
  transform: translateY(-2px);
  box-shadow: 0 10px 18px -10px rgba(15,157,138,.55);
}
.stButton > button:active {transform: translateY(0);}

/* each chip column gets its own colour */
div[data-testid="stColumn"]:nth-child(1) div.stButton > button,
div[data-testid="column"]:nth-child(1) div.stButton > button {background: #e3f8f2; border-color: #7fd9c6; color: #0a6b5d;}
div[data-testid="stColumn"]:nth-child(2) div.stButton > button,
div[data-testid="column"]:nth-child(2) div.stButton > button {background: #efe9ff; border-color: #b9a2f8; color: #5b2fc4;}
div[data-testid="stColumn"]:nth-child(3) div.stButton > button,
div[data-testid="column"]:nth-child(3) div.stButton > button {background: #fff2d9; border-color: #ffc96b; color: #9a5a00;}
div[data-testid="stColumn"]:nth-child(4) div.stButton > button,
div[data-testid="column"]:nth-child(4) div.stButton > button {background: #ffe6ef; border-color: #f7a1c0; color: #b01f5b;}
div[data-testid="stColumn"]:nth-child(1) div.stButton > button:hover {background: #c9f2e8; border-color: #0f9d8a;}
div[data-testid="stColumn"]:nth-child(2) div.stButton > button:hover {background: #e0d5ff; border-color: #8b5cf6;}
div[data-testid="stColumn"]:nth-child(3) div.stButton > button:hover {background: #ffe6b0; border-color: #ffb84d;}
div[data-testid="stColumn"]:nth-child(4) div.stButton > button:hover {background: #ffd0e1; border-color: #ec4899;}

/* ---------- Mode toggle ---------- */
div[data-testid="stRadio"] [role="radiogroup"] {
  background: linear-gradient(90deg, #d9f3ec, #e4ebff, #f3e6ff); border-radius: 999px; padding: 4px;
  display: inline-flex; gap: 2px;
  box-shadow: inset 0 1px 3px rgba(10,79,71,.12);
}
div[data-testid="stRadio"] label {
  border-radius: 999px; padding: 5px 16px; margin: 0;
  transition: background .15s, box-shadow .15s;
}
div[data-testid="stRadio"] label:has(input:checked) {
  background: #fff; box-shadow: 0 3px 8px rgba(139,92,246,.3);
}
div[data-testid="stRadio"] label:has(input:checked) p {color: var(--violet); font-weight: 700;}
div[data-testid="stRadio"] label > div:first-child {display: none;}

/* ---------- Expanders ---------- */
div[data-testid="stExpander"] {
  background: rgba(255,255,255,.8);
  border: 1px solid #e3e6f5;
  border-left: 5px solid var(--violet);
  border-radius: 16px;
  box-shadow: 0 8px 20px -14px rgba(139,92,246,.5);
  overflow: hidden;
}
div[data-testid="stExpander"] summary {font-weight: 700; color: var(--ink);}
div[data-testid="stExpander"] summary:hover {color: var(--violet);}
div[data-testid="stExpander"]:nth-of-type(2) {border-left-color: var(--pink);}

/* ---------- Misc ---------- */
div[data-testid="stSpinner"] {color: var(--teal-dark); font-weight: 600;}
div[data-testid="stAlert"] {border-radius: 14px;}
div[data-baseweb="slider"] div[role="slider"] {background: var(--violet); box-shadow: 0 0 0 4px rgba(139,92,246,.25);}

.foot {
  text-align: center; font-size: .85rem; padding: 14px 0 4px;
  font-weight: 600;
  background: linear-gradient(90deg, #0f9d8a, #2b7fe0, #8b5cf6, #ec4899);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

@media (prefers-reduced-motion: reduce) {
  .hero-card, div[data-testid="stChatMessage"], .avatar-wrap::before, .avatar-wrap .live {animation: none;}
}
@media (max-width: 640px) {
  .hero-card {padding: 16px;}
  .hero-top .title {font-size: 1.25rem;}
}
</style>

<div class="hero-card">
  <div class="hero-top">
    <div class="avatar-wrap">
      <div class="avatar">N</div>
      <span class="live"></span>
    </div>
    <div>
      <div class="title">Hi, I'm Nida's AI clone</div>
      <div class="sub">Ask me about my projects, books, food and study habits</div>
    </div>
  </div>
  <div class="hero-notice">
    <span class="ico">⚠️</span>
    <div>
      <b>AI clone, not the real Nida.</b>
      <span class="t">Answers are generated from my notes and may be incomplete or wrong.</span>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

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

# chat window
with st.container(height=460, border=True):
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

st.caption("Try one of these:")
cols = st.columns(4)
for i, (emoji, q) in enumerate(EXAMPLES):
    if cols[i % 4].button(f"{emoji} {q}", key=f"ex{i}", help=q):
        ss.pending = q
        st.rerun()

st.radio("Search mode", MODES, index=2, horizontal=True, key="mode")

with st.expander("More settings"):
    st.slider("Chunks to retrieve (top-k)", 1, 8, 4, key="k")
    if st.button("Clear chat"):
        ss.history = [{"role": "assistant", "content": INTRO}]
        ss.panel = EMPTY_PANEL
        st.rerun()

with st.expander("How I found this answer: sources and scores", expanded=True):
    st.markdown(ss.panel, unsafe_allow_html=True)

if not HAS_LLM:
    st.warning("No LLM key configured: showing the closest note instead of a generated answer.")
st.markdown('<div class="foot">Hybrid RAG · BM25 + dense embeddings + Reciprocal Rank Fusion</div>',
            unsafe_allow_html=True)