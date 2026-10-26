"""
quiz_core.py - the engine behind the kids' word game ("Juego").

No AI and no network in this file. It only reads your vocabulary files, builds a
round of questions, checks answers, hands out hints and counts stars.
The Streamlit page (pages/1_Juego.py) just shows what this file decides.

Everything the child sees is in simple Spanish. Answers to "what does it mean"
questions are in English, because the meaning is the thing being learned.
"""
import base64
import json
import random
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).parent

SCENARIO_FILES = {
    "market": "market_vocab.json",
    "papeleria": "papeleria_vocab.json",
    "school": "school_context_vocab.json",
    "hospital": "hospital_vocab.json",
}
OPTION_IDS = ["A", "B", "C", "D"]
ROUND_SIZE = 5
MAX_STARS_PER_QUESTION = 3
MODES = ("meaning", "listen")   # questions alternate: meaning, listen, meaning...


# ------------------------------------------------------------------ words
def load_words(scenario="market", starter_only=True, base=BASE):
    """Return the words of one scenario as a list of dictionaries.

    starter_only=True keeps only the hand-picked starter words listed in
    essential_words.json (10 per scenario), in that order.
    """
    base = Path(base)
    with open(base / SCENARIO_FILES[scenario], "r", encoding="utf-8") as handle:
        entries = json.load(handle)["vocabulary"]
    if starter_only:
        with open(base / "essential_words.json", "r", encoding="utf-8") as handle:
            wanted = json.load(handle)[scenario]
        by_word = {entry["spanish"]: entry for entry in entries}
        entries = [by_word[word] for word in wanted if word in by_word]
    return [
        {
            "spanish": entry["spanish"],
            "english": entry["english"],
            "pronunciation": entry.get("pronunciation", ""),
            "example_spanish": entry.get("example_spanish", ""),
            "example_english": entry.get("example_english", ""),
        }
        for entry in entries
    ]


# ------------------------------------------------------------------ text helpers
def _plain(text):
    """lowercase and without accents, so 'Árbol' and 'arbol' compare equal"""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _same_word(a, b):
    return _plain(a).strip() == _plain(b).strip()


def _has_word(text, answer):
    """True if `answer` appears in `text` as a whole word or phrase."""
    pattern = r"\b" + re.escape(_plain(answer).strip()) + r"\b"
    return re.search(pattern, _plain(text)) is not None


# ------------------------------------------------------------------ hints
def _hint_letter(text):
    """First useful letter of an answer: skips 'to', 'the', 'a', 'an' and accents."""
    words = text.lower().split()
    while len(words) > 1 and words[0] in ("to", "the", "a", "an"):
        words.pop(0)
    plain = unicodedata.normalize("NFD", " ".join(words))
    for char in plain:
        if char.isalpha():
            return char
    return "?"


# ------------------------------------------------------------------ questions
def _build_question(index, mode, word, all_words, rng):
    field_name = "english" if mode == "meaning" else "spanish"
    correct_text = word[field_name]

    pool, seen = [], {correct_text.strip().lower()}
    for other in all_words:
        text = other[field_name]
        if text.strip().lower() not in seen:
            seen.add(text.strip().lower())
            pool.append(text)
    if len(pool) < 3:
        raise ValueError("Not enough different words to build 4 options")

    texts = [correct_text] + rng.sample(pool, 3)
    rng.shuffle(texts)
    options = [{"id": OPTION_IDS[k], "text": text} for k, text in enumerate(texts)]
    correct_id = next(o["id"] for o in options if o["text"] == correct_text)

    if mode == "meaning":
        prompt = f"¿Qué significa «{word['spanish']}»?"
        instruction = "Elige el significado en inglés."
        # first clue that does NOT contain the answer (some words are the same in both languages)
        candidates = []
        if word["example_spanish"]:
            candidates.append(f"Mira la frase: «{word['example_spanish']}»")
        if word["pronunciation"]:
            candidates.append(f"Se dice «{word['pronunciation']}».")
        candidates.append("Piensa en cómo suena la palabra.")
        hint1 = next(c for c in candidates if not _has_word(c, correct_text))
    else:
        prompt = "🎧 Escucha y elige la palabra."
        instruction = "Pulsa el altavoz. ¡Puedes oírla con voz de ardilla o de gigante!"
        hint1 = "Escucha otra vez. ¡Prueba la voz de gigante! 🐘"
    hint2 = f"Empieza con la letra «{_hint_letter(correct_text)}»."

    return {
        "id": f"q{index + 1}",
        "mode": mode,
        "prompt": prompt,
        "instruction": instruction,
        "audio_text": word["spanish"],
        "options": options,
        "correct": correct_id,
        "hint1": hint1,
        "hint2": hint2,
        "card": dict(word),
    }


def make_round(words, n=ROUND_SIZE, rng=None):
    """Pick n different words and turn each into a 4-option question."""
    rng = rng or random.Random()
    if len(words) < 4:
        raise ValueError("Need at least 4 words to make a round")
    n = min(n, len(words))
    chosen = rng.sample(words, n)
    questions = []
    for i, word in enumerate(chosen):
        mode = MODES[i % len(MODES)]
        # a word that is spelled the same in both languages (like "diabetes") would make
        # a "what does it mean" question trivial, so it becomes a listening question
        if mode == "meaning" and _same_word(word["spanish"], word["english"]):
            mode = "listen"
        questions.append(_build_question(i, mode, word, words, rng))
    return questions


def hint_for(question, wrong_attempts):
    """The hint ladder: 1 = clue, 2 = first letter, 3 or more = show the answer."""
    if wrong_attempts < 1:
        raise ValueError("wrong_attempts must be at least 1")
    if wrong_attempts == 1:
        return {"level": 1, "text": question["hint1"], "reveal": False}
    if wrong_attempts == 2:
        return {"level": 2, "text": question["hint2"], "reveal": False}
    return {"level": 3, "text": "", "reveal": True}


def stars_for(wrong_attempts, revealed):
    """3 stars first try, 2 after one mistake, 1 after two, 0 if the answer was shown."""
    if revealed:
        return 0
    return max(0, MAX_STARS_PER_QUESTION - wrong_attempts)


# ------------------------------------------------------------------ one round
@dataclass
class QuestionState:
    wrong: int = 0
    disabled: set = field(default_factory=set)
    solved: bool = False
    revealed: bool = False
    stars: int = 0

    @property
    def done(self):
        return self.solved or self.revealed


class Round:
    """Keeps track of where the child is in a round."""

    def __init__(self, questions):
        self.questions = questions
        self.index = 0
        self.states = [QuestionState() for _ in questions]

    @property
    def finished(self):
        return self.index >= len(self.questions)

    @property
    def current(self):
        return self.questions[self.index]

    @property
    def state(self):
        return self.states[self.index]

    @property
    def total_stars(self):
        return sum(state.stars for state in self.states)

    @property
    def max_stars(self):
        return MAX_STARS_PER_QUESTION * len(self.questions)

    def choose(self, option_id):
        """The child taps an option. Returns what happened, or None if the tap is ignored."""
        if self.finished or self.state.done or option_id in self.state.disabled:
            return None
        question, state = self.current, self.state
        if option_id == question["correct"]:
            state.solved = True
            state.stars = stars_for(state.wrong, revealed=False)
            return {"status": "correct", "stars": state.stars}
        state.wrong += 1
        state.disabled.add(option_id)
        step = hint_for(question, state.wrong)
        if step["reveal"]:
            state.revealed = True
            state.stars = 0
            return {"status": "reveal", "stars": 0}
        return {"status": "wrong", "hint": step["text"], "level": step["level"]}

    def advance(self):
        """Go to the next question, but only once this one is finished."""
        if not self.finished and self.state.done:
            self.index += 1


# ------------------------------------------------------------------ friendly lines (Spanish)
LINES = {
    "correct": ["¡Muy bien! 🎉", "¡Genial! 🌟", "¡Fantástico! 🥳", "¡Eres una estrella! ⭐",
                "¡Olé! 💃", "¡Bravo! 👏"],
    "retry": ["¡Casi! Inténtalo otra vez. 🦜", "¡Uy! Prueba otra vez. 🙈",
              "¡Casi, casi! Una vez más. 🐢"],
    "reveal": ["No pasa nada. ¡Ahora ya sabes la respuesta! 💪",
               "¡Ay! Esta era difícil. ¡La próxima vez la sabrás! 🌈"],
    "final_high": ["¡Eres un campeón! 🏆", "¡Increíble! ¡Eres un campeón de las palabras! 🥇"],
    "final_mid": ["¡Muy bien! ¡Sigue practicando! 💪"],
    "final_low": ["¡Buen intento! Juega otra vez y verás cómo mejoras. 🌱"],
}


def pick_line(kind, rng=None):
    return (rng or random).choice(LINES[kind])


def final_kind(total_stars, max_stars):
    ratio = total_stars / max_stars if max_stars else 0
    if ratio >= 0.8:
        return "final_high"
    if ratio >= 0.5:
        return "final_mid"
    return "final_low"


# ------------------------------------------------------------------ silly voices
def audio_player_html(mp3_bytes):
    """Three buttons that play the same recording at different speeds.

    Speed and pitch move together (turning off 'preservesPitch'), so a fast
    recording sounds like a squirrel and a slow one like a giant.
    """
    encoded = base64.b64encode(mp3_bytes).decode("ascii")
    return f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;font-family:sans-serif">
  <audio id="voz" src="data:audio/mpeg;base64,{encoded}"></audio>
  <button onclick="play(1)"   style="{_BUTTON_STYLE}background:#2e86de">🔊 Normal</button>
  <button onclick="play(1.7)" style="{_BUTTON_STYLE}background:#e67e22">🐿️ Ardilla</button>
  <button onclick="play(0.6)" style="{_BUTTON_STYLE}background:#8e44ad">🐘 Gigante</button>
</div>
<script>
  const voz = document.getElementById('voz');
  function play(rate) {{
    voz.pause();
    voz.currentTime = 0;
    const keep = (rate === 1);
    voz.preservesPitch = keep;
    voz.mozPreservesPitch = keep;
    voz.webkitPreservesPitch = keep;
    voz.playbackRate = rate;
    voz.play();
  }}
</script>
"""


_BUTTON_STYLE = ("border:none;color:white;font-size:18px;padding:12px 18px;"
                 "border-radius:12px;cursor:pointer;")
