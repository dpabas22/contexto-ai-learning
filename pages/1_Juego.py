"""
Juego - a word game for kids, in simple Spanish.

Streamlit shows every file inside the `pages` folder as its own page.
This page only draws the screen. The rules live in quiz_core.py, the
characters in avatars.py and the jingles in sounds.py.
No AI is used here, and nothing about the child is saved.
"""
import io
import sys
from pathlib import Path

import streamlit as st
from gtts import gTTS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import avatars  # noqa: E402
import quiz_core as qc  # noqa: E402
import sounds  # noqa: E402

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
REST_AFTER_ROUNDS = 3        # a gentle "take a break" after this many rounds


# ---------------------------------------------------------------- audio and sound
@st.cache_data(show_spinner=False)
def word_audio(text):
    """Spanish audio for a word or phrase, kept in memory so each is fetched only once."""
    try:
        buffer = io.BytesIO()
        gTTS(text=text, lang="es").write_to_fp(buffer)
        return buffer.getvalue()
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def jingle(kind):
    return sounds.encouragement_jingle() if kind == "encourage" else sounds.celebration_jingle()


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


def show_sound_button(label, kind, phrase, color):
    """A tap-to-play jingle followed by a spoken phrase (browsers block sound that starts alone)."""
    show_html(sounds.sound_button_html(label, jingle(kind), word_audio(phrase), color), height=80)


# ---------------------------------------------------------------- actions
def set_bubble(kind):
    key = st.session_state.get("juego_avatar")
    if key:
        name = avatars.AVATARS[key]["name"]
        st.session_state["juego_bubble"] = {"kind": kind, "text": avatars.speech(kind, name)}


def start_round():
    starters = st.session_state.get("juego_wordset", "starters") == "starters"
    words = qc.load_words(st.session_state.get("juego_scenario", "market"), starters)
    st.session_state["juego_round"] = qc.Round(qc.make_round(words))
    st.session_state["juego_msg"] = None
    st.session_state["juego_bubble"] = None
    st.session_state["juego_celebrated"] = False
    set_bubble("greet")


def choose_avatar(key):
    st.session_state["juego_avatar"] = key
    start_round()


def clear_avatar():
    for name in ("juego_avatar", "juego_bubble"):
        st.session_state.pop(name, None)


def on_choose(option_id):
    result = st.session_state["juego_round"].choose(option_id)
    if result is None:
        return
    kind = {"correct": "correct", "wrong": "retry", "reveal": "reveal"}[result["status"]]
    st.session_state["juego_msg"] = {
        "kind": kind, "text": qc.pick_line(kind), "hint": result.get("hint"),
    }
    set_bubble(kind)


def on_next():
    st.session_state["juego_round"].advance()
    st.session_state["juego_msg"] = None
    st.session_state["juego_bubble"] = None


# ---------------------------------------------------------------- screens
def show_picker():
    st.subheader("Elige a tu amigo")
    columns = st.columns(len(avatars.AVATARS))
    for column, (key, info) in zip(columns, avatars.AVATARS.items()):
        with column:
            st.image(avatars.avatar_svg(key, "idle", size=150), width=150)
            st.caption(f"{info['name']}, {info['desc']}")
            st.button(f"Elegir a {info['name']}", key=f"pick_{key}",
                      on_click=choose_avatar, args=(key,), use_container_width=True)


def show_avatar_row():
    key = st.session_state["juego_avatar"]
    info = avatars.AVATARS[key]
    bubble = st.session_state.get("juego_bubble")
    mood = avatars.MOOD_FOR[bubble["kind"]] if bubble else "idle"
    picture, words = st.columns([1, 3])
    with picture:
        st.image(avatars.avatar_svg(key, mood, size=120), width=120)
    with words:
        if bubble:
            st.markdown(f"> **{info['name']}:** {bubble['text']}")


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
    show_avatar_row()
    st.progress(rnd.index / total)
    st.caption(f"Pregunta {rnd.index + 1} de {total}   ·   ⭐ {rnd.total_stars}")

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
        st.caption("Pulsa para escuchar 🎵")
        show_sound_button("💪 ¡Tú puedes!", "encourage", "¡Tú puedes!", "#2e86de")
    show_card(question["card"])
    last = rnd.index == len(rnd.questions) - 1
    st.button("Ver mi resultado 🏁" if last else "Siguiente ➡️",
              key=f"next_{rnd.index}", on_click=on_next, use_container_width=True)


def show_final(rnd):
    kind = qc.final_kind(rnd.total_stars, rnd.max_stars)
    if not st.session_state.get("juego_celebrated"):
        st.session_state["juego_final_text"] = qc.pick_line(kind)
        st.session_state["juego_rounds_done"] = st.session_state.get("juego_rounds_done", 0) + 1
        needs_rest = st.session_state["juego_rounds_done"] % REST_AFTER_ROUNDS == 0
        set_bubble("rest" if needs_rest else kind)
        if kind == "final_high":
            st.balloons()
        st.session_state["juego_celebrated"] = True

    show_avatar_row()
    st.header("¡Ronda terminada! 🎉")
    st.subheader(f"Tienes {rnd.total_stars} de {rnd.max_stars} estrellas ⭐")
    st.write(st.session_state["juego_final_text"])
    if kind == "final_high":
        st.caption("Pulsa para escuchar 🎵")
        show_sound_button("🎉 ¡Felicidades!", "celebrate", "¡Felicidades!", "#27ae60")
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
        "The audio comes from Google text-to-speech, which receives only the single word or "
        "short phrase being played. The fun voices are the same recording played faster or "
        "slower, so keep using the normal voice for pronunciation."
    )
    st.write(
        "The characters (Pipo, Misi and Lorito) and the jingles are original and made by code. "
        "Sounds play only when tapped, at a moderate volume. Motion is gentle and switches off "
        "if the device is set to reduce motion. After every third round the character suggests a "
        "short break. The Spanish lines and the word list should be checked by a native speaker."
    )
    st.selectbox("Words from", list(SCENARIO_NAMES), format_func=SCENARIO_NAMES.get,
                 key="juego_scenario", on_change=start_round)
    st.radio("Which words?", ["starters", "all"],
             format_func=lambda v: "10 starter words" if v == "starters" else "All words in this section",
             key="juego_wordset", on_change=start_round, horizontal=True)

if "juego_avatar" not in st.session_state:
    show_picker()
    st.stop()

if "juego_round" not in st.session_state:
    start_round()

current_round = st.session_state["juego_round"]
if current_round.finished:
    show_final(current_round)
else:
    show_question(current_round)

st.divider()
st.button("Cambiar de amigo", on_click=clear_avatar)
