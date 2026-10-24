"""
Juego - a word game for kids, in simple Spanish.

Streamlit shows every file inside the `pages` folder as its own page.
This page only draws the screen. The rules live in quiz_core.py.
No AI is used here.
"""
import io
import sys
from pathlib import Path

import streamlit as st
from gtts import gTTS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import quiz_core as qc  # noqa: E402

st.set_page_config(page_title="Juego", page_icon="🎮")

st.markdown(
    """
    <style>
    .stButton > button { font-size: 1.3rem; padding: 0.7rem 1rem; border-radius: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

SCENARIO_NAMES = {
    "market": "Market (mercado)",
    "papeleria": "Stationery shop (papelería)",
    "school": "School (escuela)",
    "hospital": "Hospital",
}


# ---------------------------------------------------------------- audio
@st.cache_data(show_spinner=False)
def word_audio(text):
    """Spanish audio for a word, kept in memory so each word is fetched only once."""
    try:
        buffer = io.BytesIO()
        gTTS(text=text, lang="es").write_to_fp(buffer)
        return buffer.getvalue()
    except Exception:
        return None


def show_html(html, height):
    """Show a small HTML snippet that we generated ourselves (never user-typed text).
    Newer Streamlit uses st.iframe. Older versions still have components.html."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)


def show_audio(text, fallback=""):
    """Voice buttons for a word. If the voice service is down, say so (and show a written guide)."""
    audio = word_audio(text)
    if audio:
        show_html(qc.audio_player_html(audio), height=80)
    else:
        st.caption("🔇 Sin audio por ahora." + (f"  Se dice: {fallback}" if fallback else ""))


# ---------------------------------------------------------------- actions
def start_round():
    starters = st.session_state.get("juego_wordset", "starters") == "starters"
    words = qc.load_words(st.session_state.get("juego_scenario", "market"), starters)
    st.session_state["juego_round"] = qc.Round(qc.make_round(words))
    st.session_state["juego_msg"] = None
    st.session_state["juego_celebrated"] = False


def on_choose(option_id):
    result = st.session_state["juego_round"].choose(option_id)
    if result is None:
        return
    kind = {"correct": "correct", "wrong": "retry", "reveal": "reveal"}[result["status"]]
    st.session_state["juego_msg"] = {
        "kind": kind, "text": qc.pick_line(kind), "hint": result.get("hint"),
    }


def on_next():
    st.session_state["juego_round"].advance()
    st.session_state["juego_msg"] = None


# ---------------------------------------------------------------- screens
def show_card(card):
    st.markdown(f"### {card['spanish']}  =  {card['english']}")
    if card["pronunciation"]:
        st.caption(f"Se dice: {card['pronunciation']}")
    if card["example_spanish"]:
        st.write(f"«{card['example_spanish']}»")
        if card["example_english"]:
            st.caption(card["example_english"])


def show_question(rnd):
    question, state = rnd.current, rnd.state
    total = len(rnd.questions)
    st.progress(rnd.index / total)
    st.caption(f"Pregunta {rnd.index + 1} de {total}   ·   ⭐ {rnd.total_stars}")
    if rnd.index == 0 and not st.session_state.get("juego_msg"):
        st.write("🦜 **Lorito:** ¡Hola! Soy Lorito. ¡Vamos a jugar!")

    st.subheader(question["prompt"])
    st.caption(question["instruction"])
    show_audio(question["audio_text"], question["card"]["pronunciation"])
    message = st.session_state.get("juego_msg")

    if not state.done:
        for option in question["options"]:
            st.button(
                option["text"],
                key=f"opt_{rnd.index}_{option['id']}",
                disabled=option["id"] in state.disabled,
                use_container_width=True,
                on_click=on_choose,
                args=(option["id"],),
            )
        if message and message["kind"] == "retry":
            st.warning(message["text"])
            if message["hint"]:
                st.info("💡 " + message["hint"])
        return

    if state.solved:
        st.success(message["text"] if message else "¡Muy bien! 🎉")
        st.write("⭐" * state.stars + "☆" * (qc.MAX_STARS_PER_QUESTION - state.stars))
    else:
        correct_text = next(o["text"] for o in question["options"] if o["id"] == question["correct"])
        st.info((message["text"] if message else "No pasa nada.") + f"  La respuesta es «{correct_text}».")
    show_card(question["card"])
    last = rnd.index == len(rnd.questions) - 1
    st.button("Ver mi resultado 🏁" if last else "Siguiente ➡️",
              key=f"next_{rnd.index}", on_click=on_next, use_container_width=True)


def show_final(rnd):
    st.header("¡Ronda terminada! 🎉")
    st.subheader(f"Tienes {rnd.total_stars} de {rnd.max_stars} estrellas ⭐")
    kind = qc.final_kind(rnd.total_stars, rnd.max_stars)
    if "juego_final_text" not in st.session_state or not st.session_state.get("juego_celebrated"):
        st.session_state["juego_final_text"] = qc.pick_line(kind)
    st.write(st.session_state["juego_final_text"])
    if kind == "final_high" and not st.session_state.get("juego_celebrated"):
        st.balloons()
    st.session_state["juego_celebrated"] = True
    st.button("Jugar otra vez 🔄", on_click=start_round, use_container_width=True)


# ---------------------------------------------------------------- page
st.title("🎮 ¡Juega con las palabras!")

with st.expander("👨‍👩‍👦 Para papá y mamá (English)"):
    st.write(
        "A short word game for kids: 5 questions per round, with hints before answers "
        "and stars instead of scores. Everything the child reads is in simple Spanish. "
        "Meanings are asked in English because that is what is being learned."
    )
    st.write(
        "No AI is used on this page and nothing about the child is saved. "
        "The audio comes from Google text-to-speech, which receives only the single word "
        "being played. The fun voices are the same recording played faster or slower, so "
        "keep using the normal voice for pronunciation."
    )
    st.write("The Spanish lines and the word list should be checked by a native speaker.")
    st.selectbox("Words from", list(SCENARIO_NAMES), format_func=SCENARIO_NAMES.get,
                 key="juego_scenario", on_change=start_round)
    st.radio("Which words?", ["starters", "all"],
             format_func=lambda v: "10 starter words" if v == "starters" else "All words in this section",
             key="juego_wordset", on_change=start_round, horizontal=True)

if "juego_round" not in st.session_state:
    start_round()

current_round = st.session_state["juego_round"]
if current_round.finished:
    show_final(current_round)
else:
    show_question(current_round)
