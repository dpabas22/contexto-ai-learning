"""
Adulto - guided market practice for adults (usted with vendors).
Rules live in mentor_engine.py. Questions and hints are authored in
mentor_questions.json. No AI and no search here: each wrong answer shows
its own written reason, and lesson cards come from a fixed list per question.
Nothing is saved unless the learner downloads the progress file.
"""
import io
import json
import random
import sys
from pathlib import Path

import streamlit as st
from gtts import gTTS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import lesson_index  # noqa: E402
import mentor_engine as me  # noqa: E402
import mentor_registry  # noqa: E402
import spanish_tools  # noqa: E402

st.set_page_config(page_title="Adulto", page_icon="🛒")

NUMBER_TAG_TEXT = {
    "missed_hundreds": "You may have missed the hundreds. Listen for the first word.",
    "missed_tens": "You may have caught only the hundreds. Listen for what comes after.",
    "ciento_vs_mil": "Check ciento (100) versus mil (1,000).",
    "added_instead_of_subtracted": "Change is what you pay minus the price, not plus.",
    "repeated_price": "That is the price. Change is what you pay minus the price.",
    "other": "Not quite. Try once more.",
}


@st.cache_data
def load_data():
    d = json.loads((ROOT / "mentor_questions.json").read_text(encoding="utf-8"))
    return d["metadata"], d["questions"]


@st.cache_resource
def load_lessons():
    units = {u.id: u for u in lesson_index.build_units(ROOT)}
    return units, mentor_registry.build_registry(ROOT)


@st.cache_data(show_spinner=False)
def speak(text):
    buf = io.BytesIO()
    gTTS(text=text, lang="es", tld="com.mx").write_to_fp(buf)
    return buf.getvalue()


meta, QUESTIONS = load_data()
UNITS, REGISTRY = load_lessons()
S = st.session_state
if "i" not in S:
    S.i, S.wrong, S.attempt, S.done, S.show_me = 0, 0, 0, False, False
    S.results, S.prices, S.tags = [], {}, []


def lesson_cards(q):
    st.markdown("**Look at these lessons**")
    for tid in q.get("related", []):
        entry, unit = REGISTRY.get(tid), UNITS.get(tid)
        if not entry or not unit:
            continue
        with st.expander(entry["label"]):
            body = unit.text[len(unit.title):].strip()
            st.write(body[:300] + ("…" if len(body) > 300 else ""))
            st.caption(f"Full lesson: tab “{entry['tab']}” in the main app.")


def next_question(stars):
    q = QUESTIONS[S.i]
    S.results.append({"id": q["id"], "wrong_attempts": S.wrong, "stars": stars})
    S.i += 1
    S.wrong, S.attempt, S.done, S.show_me = 0, 0, False, False


st.title("🛒 En el mercado")
st.caption("Practice with vendors. Use *usted* (polite).")
if meta.get("review") == "needs-review":
    st.info("Draft content: a native speaker has not reviewed the Spanish yet. "
            "Prices are illustrative.")

# ---------------------------------------------------------------- summary
if S.i >= len(QUESTIONS):
    st.header("Resumen")
    total = sum(r["stars"] for r in S.results)
    st.subheader("⭐" * total + f"  ({total}/{3 * len(QUESTIONS)})")
    first_try = sum(1 for r in S.results if r["wrong_attempts"] == 0)
    st.write(f"Right on the first try: **{first_try} of {len(QUESTIONS)}**.")
    if S.tags:
        st.write("Mistakes to watch:")
        for tag in sorted(set(S.tags)):
            st.write(f"- {tag.replace('_', ' ')} (×{S.tags.count(tag)})")
    else:
        st.write("No mistakes this round. 🎉")
    st.download_button("Download my progress (optional)",
                       json.dumps({"results": S.results, "tags": S.tags}, indent=1),
                       "contexto_progress.json", "application/json")
    if st.button("Practice again"):
        for k in list(S.keys()):
            del S[k]
        st.rerun()
    st.stop()

# --------------------------------------------------------------- question
q = QUESTIONS[S.i]
st.progress(S.i / len(QUESTIONS), text=f"Question {S.i + 1} of {len(QUESTIONS)}")
st.markdown(f"*{q['scene']}*")
is_number = q["format"] == "hear_and_pay"

if is_number:
    price = S.prices.setdefault(q["id"], random.choice(q["generator"]["prices"]))
    line = q["audio_template"].format(price_es=spanish_tools.number_to_spanish(price))
    st.markdown(f"**{q['prompt']}**")
    st.audio(speak(line), format="audio/mp3")
    st.caption("Tap play and listen. You can replay it.")
else:
    if q.get("vendor_line"):
        st.markdown(f"🗣️ **{q['vendor_line']}**")
    st.markdown(f"**{q['prompt']}**")

feedback = None
if not S.done:
    if is_number:
        typed = st.text_input("Your answer (numbers)", key=f"n-{q['id']}-{S.attempt}")
    else:
        labels = {o["id"]: f"{o['id']}.  {o['text']}" for o in q["options"]}
        chosen = st.radio("Pick one", list(labels), format_func=labels.get,
                          index=None, key=f"r-{q['id']}-{S.attempt}")
    c1, c2 = st.columns(2)
    check = c1.button("Check")
    show = c2.button("Show me")
    if show:
        S.wrong = max(S.wrong, 1)
        S.show_me, S.done = True, True
        st.rerun()
    if check:
        if is_number:
            given = me.parse_number(typed)
            if given is None:
                st.warning("Type a whole number, like 120.")
            elif me.diagnose_number(q, price, given) is None:
                S.done = True
                st.rerun()
            else:
                S.wrong += 1
                S.attempt += 1
                tag = me.diagnose_number(q, price, given)
                S.tags.append(tag)
                S.feedback = NUMBER_TAG_TEXT[tag]
                st.rerun()
        elif chosen is None:
            st.warning("Pick an answer first.")
        elif me.check_choice(q, chosen):
            S.done = True
            st.rerun()
        else:
            S.wrong += 1
            S.attempt += 1
            d = me.diagnose_choice(q, chosen)
            if d["tag"]:
                S.tags.append(d["tag"])
            S.feedback = d["why_not"]
            st.rerun()
    if S.wrong >= 1:
        step = me.next_step(q, S.wrong)
        if S.get("feedback"):
            st.error(S.feedback)
        st.info(f"💡 {step['text']}")
        if step["show_links"]:
            lesson_cards(q)
        if step["reveal"]:
            S.done = True
            st.rerun()
else:
    ans = (me.expected_number(q, price) if is_number
           else next(o["text"] for o in q["options"] if o["id"] == q["correct"]))
    if S.show_me or S.wrong >= 3:
        st.warning(f"Answer: **{ans}**. Let's understand why.")
        stars = 0
    else:
        st.success(f"¡Muy bien! **{ans}**")
        stars = 3 if S.wrong == 0 else (2 if S.wrong == 1 else 1)
    st.write(q["explanation"])
    lesson_cards(q)
    S.feedback = None
    if st.button("Next ➜"):
        next_question(stars)
        st.rerun()
