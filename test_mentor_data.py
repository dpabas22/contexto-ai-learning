"""
Tests for the mentor's data. Run from the repo folder with:  pytest -q

They check three promises:
1. Every link in a question points to something that really exists.
2. Hints and wrong-answer feedback never give away the correct answer.
3. Every question is complete and well formed.
"""
import json
import re
import unicodedata
from pathlib import Path

import pytest

from mentor_registry import TAB_KEYS, build_registry, resolve
from spanish_tools import number_to_spanish

BASE = Path(__file__).parent
DATA = json.loads((BASE / "mentor_questions.json").read_text(encoding="utf-8"))
QUESTIONS = DATA["questions"]
REGISTRY = build_registry(BASE)
CHOICE_FORMATS = ("best_reply", "fill_blank")


# ---------------------------------------------------------------- leak check
def normalize(text):
    """lowercase, no accents, no punctuation, single spaces"""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


def leaks(text, correct):
    """True if `text` gives away `correct` (the full answer, the single answer
    word, or any run of three words copied from a longer answer)."""
    text_n, correct_n = normalize(text), normalize(correct)
    if not correct_n:
        return False
    if "answer is" in text_n:
        return True
    words = correct_n.split()
    if len(words) == 1:
        return words[0] in text_n.split()
    if correct_n in text_n:
        return True
    return any(" ".join(words[i:i + 3]) in text_n for i in range(len(words) - 2))


def correct_text(question):
    for option in question["options"]:
        if option["id"] == question["correct"]:
            return option["text"]
    raise AssertionError("correct option missing")


# the leak check must itself be trustworthy
def test_leak_check_catches_obvious_leaks():
    assert leaks("The verb you need is tiene", "Tiene")
    assert leaks("It is Medio!", "medio")
    assert leaks("Say: ¿A cuánto es el kilo de manzanas?", "¿A cuánto es el kilo de manzanas?")
    assert leaks("Try: A cuánto es el", "¿A cuánto es el kilo de manzanas?")
    assert leaks("The answer is B", "Anything")


def test_leak_check_allows_fair_hints():
    assert not leaks("Check the present tense of Tener.", "Tiene")
    assert not leaks("Is kilo masculine or feminine?", "medio")
    assert not leaks("Which reply tells the vendor what you want?",
                     "Buenas tardes. Me da medio kilo de papaya y un kilo de plátanos, por favor.")


# ---------------------------------------------------------------- structure
def test_six_questions_with_unique_ids():
    assert len(QUESTIONS) == 6
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids))


def test_each_format_appears_twice():
    formats = [q["format"] for q in QUESTIONS]
    for name in ("best_reply", "fill_blank", "hear_and_pay"):
        assert formats.count(name) == 2


@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q["id"])
def test_common_fields(question):
    for field in ("id", "format", "concepts", "scene", "prompt", "hints",
                  "explanation", "related", "review"):
        assert question.get(field), f"{question['id']} is missing {field}"
    assert len(question["hints"]) == 2
    for concept in question["concepts"]:
        assert concept in DATA["concepts"], f"unknown concept {concept}"
    assert question["review"] in ("needs-review", "verified")


@pytest.mark.parametrize(
    "question", [q for q in QUESTIONS if q["format"] in CHOICE_FORMATS], ids=lambda q: q["id"])
def test_choice_questions_are_well_formed(question):
    options = question["options"]
    assert len(options) == 3
    option_ids = [o["id"] for o in options]
    assert len(option_ids) == len(set(option_ids))
    assert question["correct"] in option_ids
    wrong = [o for o in options if o["id"] != question["correct"]]
    assert len(wrong) == 2
    for option in wrong:
        assert option.get("tag"), f"{question['id']} option {option['id']} needs a tag"
        assert option.get("why_not"), f"{question['id']} option {option['id']} needs why_not"
    assert "tag" not in next(o for o in options if o["id"] == question["correct"])


@pytest.mark.parametrize(
    "question", [q for q in QUESTIONS if q["format"] == "hear_and_pay"], ids=lambda q: q["id"])
def test_hear_and_pay_questions_are_well_formed(question):
    assert "{price_es}" in question["audio_template"]
    assert question["task"] in ("price", "change")
    prices = question["generator"]["prices"]
    assert len(prices) >= 3
    if question["task"] == "change":
        paid = question["generator"]["paid"]
        assert all(price < paid for price in prices)
    assert question["wrong_answer_tags"]
    # every generated spoken line can really be produced
    for price in prices:
        spoken = question["audio_template"].format(price_es=number_to_spanish(price))
        assert str(price) not in spoken and len(spoken) > 10


# ---------------------------------------------------------------- links
@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q["id"])
def test_every_related_link_exists(question):
    assert 1 <= len(question["related"]) <= 4
    for target_id in question["related"]:
        assert resolve(target_id, REGISTRY), f"{question['id']}: no such target {target_id}"


def test_registry_basics():
    for target_id in ("vocab:market:kilo", "verb:querer", "verb:tener", "verb:dar",
                      "conv:conv001", "numbers:hundreds", "numbers:say_any_number",
                      "math:shopping_examples", "phrase:p048"):
        assert target_id in REGISTRY, target_id
    for entry in REGISTRY.values():
        assert entry["tab"] in TAB_KEYS
        assert entry["label"] and entry["section"]


# ---------------------------------------------------------------- no leaks
@pytest.mark.parametrize(
    "question", [q for q in QUESTIONS if q["format"] in CHOICE_FORMATS], ids=lambda q: q["id"])
def test_hints_and_feedback_do_not_give_the_answer(question):
    answer = correct_text(question)
    for hint in question["hints"]:
        assert not leaks(hint, answer), f"{question['id']} hint leaks: {hint}"
    for option in question["options"]:
        if option.get("why_not"):
            assert not leaks(option["why_not"], answer), (
                f"{question['id']} option {option['id']} why_not leaks")
