"""
Tests for the kids' word game.   Run:  pytest -q test_quiz_core.py

Part 1 tests the engine in quiz_core.py.
Part 2 plays the real Streamlit page like a child would, with a fake voice
service so no internet is needed.
"""
import random
import re
import sys
import types
import unicodedata
from pathlib import Path

import pytest

import quiz_core as qc

ROOT = Path(__file__).parent
SCENARIOS = list(qc.SCENARIO_FILES)


def plain(text):
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# ------------------------------------------------------------ words
def test_ten_starter_words_for_every_scenario():
    for scenario in SCENARIOS:
        words = qc.load_words(scenario, starter_only=True)
        assert len(words) == 10, scenario
        for word in words:
            assert word["spanish"] and word["english"], (scenario, word)


def test_all_words_loads_more_than_starters():
    assert len(qc.load_words("market", starter_only=False)) > 10


# ------------------------------------------------------------ building rounds
@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("starter_only", [True, False])
@pytest.mark.parametrize("seed", range(5))
def test_rounds_are_well_formed(scenario, starter_only, seed):
    words = qc.load_words(scenario, starter_only)
    questions = qc.make_round(words, rng=random.Random(seed))
    assert len(questions) == qc.ROUND_SIZE
    for number, question in enumerate(questions):
        planned = "meaning" if number % 2 == 0 else "listen"
        if question["mode"] != planned:                    # only allowed for same-spelling words
            assert planned == "meaning" and question["mode"] == "listen"
            assert plain(question["card"]["spanish"]) == plain(question["card"]["english"])
        if question["mode"] == "meaning":
            assert plain(question["card"]["spanish"]) != plain(question["card"]["english"])
    assert len({q["card"]["spanish"] for q in questions}) == qc.ROUND_SIZE   # no repeated word
    for question in questions:
        texts = [o["text"].strip().lower() for o in question["options"]]
        assert len(question["options"]) == 4
        assert len(set(texts)) == 4                       # four different options
        assert [o["id"] for o in question["options"]] == ["A", "B", "C", "D"]
        correct = next(o for o in question["options"] if o["id"] == question["correct"])
        expected = question["card"]["english" if question["mode"] == "meaning" else "spanish"]
        assert correct["text"] == expected


def test_same_seed_gives_same_round():
    words = qc.load_words("market")
    first = qc.make_round(words, rng=random.Random(7))
    second = qc.make_round(words, rng=random.Random(7))
    assert first == second


def test_too_few_words_is_refused():
    words = qc.load_words("market")[:3]
    with pytest.raises(ValueError):
        qc.make_round(words)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_hints_never_contain_the_answer(scenario):
    words = qc.load_words(scenario, starter_only=False)
    for seed in range(20):
        for question in qc.make_round(words, rng=random.Random(seed)):
            answer = next(o["text"] for o in question["options"] if o["id"] == question["correct"])
            for hint in (question["hint1"], question["hint2"]):
                # whole words only: Spanish "firme" does not give away English "firm"
                pattern = r"\b" + re.escape(plain(answer)) + r"\b"
                assert not re.search(pattern, plain(hint)), (question["id"], answer, hint)


def test_hint_letter_skips_to_and_the():
    assert qc._hint_letter("to buy") == "b"
    assert qc._hint_letter("the market") == "m"
    assert qc._hint_letter("árbol") == "a"


# ------------------------------------------------------------ stars and the hint ladder
@pytest.mark.parametrize("wrong, revealed, stars", [(0, False, 3), (1, False, 2), (2, False, 1), (3, True, 0), (5, True, 0)])
def test_stars(wrong, revealed, stars):
    assert qc.stars_for(wrong, revealed) == stars


def test_hint_ladder_levels():
    question = qc.make_round(qc.load_words("market"), rng=random.Random(1))[0]
    assert qc.hint_for(question, 1) == {"level": 1, "text": question["hint1"], "reveal": False}
    assert qc.hint_for(question, 2) == {"level": 2, "text": question["hint2"], "reveal": False}
    assert qc.hint_for(question, 3)["reveal"] is True
    with pytest.raises(ValueError):
        qc.hint_for(question, 0)


# ------------------------------------------------------------ the round state machine
def new_round(seed=3):
    return qc.Round(qc.make_round(qc.load_words("market"), rng=random.Random(seed)))


def wrong_ids(rnd):
    return [o["id"] for o in rnd.current["options"] if o["id"] != rnd.current["correct"]]


def test_first_try_gives_three_stars():
    rnd = new_round()
    result = rnd.choose(rnd.current["correct"])
    assert result == {"status": "correct", "stars": 3}
    assert rnd.state.solved and rnd.total_stars == 3


def test_one_mistake_then_correct_gives_two_stars_and_a_hint():
    rnd = new_round()
    result = rnd.choose(wrong_ids(rnd)[0])
    assert result["status"] == "wrong" and result["level"] == 1 and result["hint"]
    assert rnd.choose(rnd.current["correct"])["stars"] == 2


def test_three_mistakes_reveal_the_answer():
    rnd = new_round()
    results = [rnd.choose(option_id) for option_id in wrong_ids(rnd)]
    assert [r["status"] for r in results] == ["wrong", "wrong", "reveal"]
    assert results[1]["level"] == 2
    assert rnd.state.revealed and rnd.state.stars == 0


def test_taps_are_ignored_when_they_should_be():
    rnd = new_round()
    first_wrong = wrong_ids(rnd)[0]
    rnd.choose(first_wrong)
    assert rnd.choose(first_wrong) is None               # same wrong option again
    rnd.choose(rnd.current["correct"])
    assert rnd.choose(rnd.current["correct"]) is None    # already solved


def test_cannot_skip_ahead_before_finishing_a_question():
    rnd = new_round()
    rnd.advance()
    assert rnd.index == 0
    rnd.choose(rnd.current["correct"])
    rnd.advance()
    assert rnd.index == 1


def test_a_full_perfect_round():
    rnd = new_round()
    for _ in range(qc.ROUND_SIZE):
        rnd.choose(rnd.current["correct"])
        rnd.advance()
    assert rnd.finished
    assert rnd.total_stars == rnd.max_stars == 15
    assert qc.final_kind(rnd.total_stars, rnd.max_stars) == "final_high"
    assert rnd.choose("A") is None                       # nothing to choose once finished


def test_final_kinds():
    assert qc.final_kind(15, 15) == "final_high"
    assert qc.final_kind(8, 15) == "final_mid"
    assert qc.final_kind(3, 15) == "final_low"


def test_friendly_lines_exist_and_are_not_empty():
    for kind, lines in qc.LINES.items():
        assert lines and all(line.strip() for line in lines), kind
        assert qc.pick_line(kind) in lines


# ------------------------------------------------------------ silly voices
def test_audio_player_has_three_voices_and_pitch_control():
    html = qc.audio_player_html(b"fake-mp3-bytes")
    assert "Normal" in html and "Ardilla" in html and "Gigante" in html
    assert "preservesPitch" in html
    assert "base64," in html and "play(0.6)" in html and "play(1.7)" in html


# ------------------------------------------------------------ the real page, played like a child
def make_app(monkeypatch):
    import gtts
    from streamlit.testing.v1 import AppTest

    class FakeVoice:
        def __init__(self, text, lang="es"):
            self.text = text

        def write_to_fp(self, handle):
            handle.write(b"fake-mp3")

    monkeypatch.setattr(gtts, "gTTS", FakeVoice)
    sys.path.insert(0, str(ROOT))
    import streamlit as st
    st.cache_data.clear()
    return AppTest.from_file(str(ROOT / "pages" / "1_Juego.py"), default_timeout=60).run()


def option_buttons(app):
    return [b for b in app.button if b.key and b.key.startswith("opt_")]


def click_option(app, option_id):
    rnd = app.session_state["juego_round"]
    key = f"opt_{rnd.index}_{option_id}"
    next(b for b in app.button if b.key == key).click().run()


def test_page_loads_in_spanish_without_errors(monkeypatch):
    app = make_app(monkeypatch)
    assert not app.exception
    assert app.title[0].value == "🎮 ¡Juega con las palabras!"
    assert len(option_buttons(app)) == 4
    assert any("Pregunta 1 de 5" in c.value for c in app.caption)


def test_page_wrong_then_right_shows_hint_then_card(monkeypatch):
    app = make_app(monkeypatch)
    rnd = app.session_state["juego_round"]
    wrong = [o["id"] for o in rnd.current["options"] if o["id"] != rnd.current["correct"]][0]
    click_option(app, wrong)
    assert any(rnd.current["hint1"] in i.value for i in app.info)   # the first hint appears
    assert any(w.value for w in app.warning)                    # friendly retry line
    click_option(app, rnd.current["correct"])
    assert app.success and not app.exception                   # celebration line
    assert any(b.key == "next_0" for b in app.button)


def test_page_full_round_reaches_the_final_screen(monkeypatch):
    app = make_app(monkeypatch)
    for number in range(qc.ROUND_SIZE):
        rnd = app.session_state["juego_round"]
        click_option(app, rnd.current["correct"])
        next(b for b in app.button if b.key == f"next_{number}").click().run()
    assert not app.exception
    assert app.header[0].value == "¡Ronda terminada! 🎉"
    assert any("15 de 15" in s.value for s in app.subheader)
    again = next(b for b in app.button if b.label == "Jugar otra vez 🔄")
    again.click().run()
    assert not app.exception and len(option_buttons(app)) == 4
    assert app.session_state["juego_round"].index == 0


def test_page_three_mistakes_reveal_the_answer(monkeypatch):
    app = make_app(monkeypatch)
    rnd = app.session_state["juego_round"]
    for option_id in [o["id"] for o in rnd.current["options"] if o["id"] != rnd.current["correct"]]:
        click_option(app, option_id)
    assert not app.exception
    assert any("La respuesta es" in i.value for i in app.info)
    assert option_buttons(app) == []                            # options hidden once finished


def test_parent_settings_change_the_words(monkeypatch):
    app = make_app(monkeypatch)
    app.selectbox(key="juego_scenario").select("school").run()
    assert not app.exception
    words = {q["card"]["spanish"] for q in app.session_state["juego_round"].questions}
    school_words = {w["spanish"] for w in qc.load_words("school")}
    assert words <= school_words


def test_page_still_works_when_the_voice_service_is_down(monkeypatch):
    import gtts
    from streamlit.testing.v1 import AppTest

    class BrokenVoice:
        def __init__(self, text, lang="es"):
            raise RuntimeError("no internet")

    monkeypatch.setattr(gtts, "gTTS", BrokenVoice)
    sys.path.insert(0, str(ROOT))
    import streamlit as st
    st.cache_data.clear()
    app = AppTest.from_file(str(ROOT / "pages" / "1_Juego.py"), default_timeout=60).run()
    assert not app.exception
    assert any("Sin audio por ahora" in c.value for c in app.caption)
    assert len(option_buttons(app)) == 4                      # the game is still playable
