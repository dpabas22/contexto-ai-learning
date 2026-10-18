"""
Tests for mentor_core.py.   Run:  pytest -q test_mentor_core.py

Each test group matches one function. Write the functions in the order
they appear in mentor_core.py and watch the groups turn green.
"""
import json
from pathlib import Path

import pytest

from mentor_core import (
    check_choice, diagnose_choice, diagnose_number, expected_number,
    next_step, parse_number,
)

DATA = json.loads((Path(__file__).parent / "mentor_questions.json").read_text(encoding="utf-8"))
BY_ID = {q["id"]: q for q in DATA["questions"]}
Q1, Q3, Q5, Q6 = BY_ID["mkt-q1"], BY_ID["mkt-q3"], BY_ID["mkt-q5"], BY_ID["mkt-q6"]


# ------------------------------------------------------------ 1. parse_number
@pytest.mark.parametrize("typed, expected", [
    ("120", 120),
    ("  120  ", 120),
    ("1,020", 1020),
    ("1,200,000", 1200000),
    ("$120", 120),
    ("$ 120", 120),
    ("120 pesos", 120),
    ("120 PESOS", 120),
    ("1 peso", 1),
    ("0", 0),
])
def test_parse_number_accepts(typed, expected):
    assert parse_number(typed) == expected


@pytest.mark.parametrize("typed", [
    "", "   ", "abc", "12.5", "-5", "1,2,3", "10,20", "ciento veinte", "12 34", "$",
])
def test_parse_number_rejects(typed):
    assert parse_number(typed) is None


# ------------------------------------------------------------ 2. check_choice
def test_check_choice_right_and_wrong():
    assert check_choice(Q1, "B") is True
    assert check_choice(Q1, "A") is False
    assert check_choice(Q1, "C") is False
    assert check_choice(Q3, "A") is True      # Q3's correct option is A


def test_check_choice_unknown_option():
    with pytest.raises(ValueError):
        check_choice(Q1, "Z")


# ------------------------------------------------------------ 3. diagnose_choice
def test_diagnose_choice_wrong_options_give_tag_and_reason():
    result = diagnose_choice(Q1, "C")
    assert result["tag"] == "too_blunt"
    assert "usted" in result["why_not"]
    assert diagnose_choice(Q3, "B")["tag"] == "tu_instead_of_usted"


def test_diagnose_choice_correct_option_gives_none():
    assert diagnose_choice(Q1, "B") is None


def test_diagnose_choice_unknown_option():
    with pytest.raises(ValueError):
        diagnose_choice(Q1, "Z")


# ------------------------------------------------------------ 4. expected_number
def test_expected_number_for_price():
    assert expected_number(Q5, 120) == 120


def test_expected_number_for_change():
    assert expected_number(Q6, 350) == 150
    assert expected_number(Q6, 175) == 325


# ------------------------------------------------------------ 5. diagnose_number
def test_diagnose_number_correct_answers_give_none():
    assert diagnose_number(Q5, 120, 120) is None
    assert diagnose_number(Q6, 350, 150) is None


@pytest.mark.parametrize("price, given, tag", [
    (120, 20, "missed_hundreds"),
    (340, 40, "missed_hundreds"),
    (120, 100, "missed_tens"),
    (340, 300, "missed_tens"),
    (120, 1200, "ciento_vs_mil"),
    (120, 1020, "ciento_vs_mil"),
    (340, 1040, "ciento_vs_mil"),
    (120, 999, "other"),
])
def test_diagnose_number_price_mistakes(price, given, tag):
    assert diagnose_number(Q5, price, given) == tag


@pytest.mark.parametrize("price, given, tag", [
    (350, 850, "added_instead_of_subtracted"),
    (350, 350, "repeated_price"),
    (350, 1, "other"),
])
def test_diagnose_number_change_mistakes(price, given, tag):
    assert diagnose_number(Q6, price, given) == tag


# ------------------------------------------------------------ 6. next_step
def test_next_step_level_1():
    step = next_step(Q1, 1)
    assert step == {"level": 1, "text": Q1["hints"][0], "show_links": False, "reveal": False}


def test_next_step_level_2_shows_links_but_does_not_reveal():
    step = next_step(Q1, 2)
    assert step == {"level": 2, "text": Q1["hints"][1], "show_links": True, "reveal": False}


@pytest.mark.parametrize("attempts", [3, 4, 10])
def test_next_step_level_3_reveals(attempts):
    step = next_step(Q1, attempts)
    assert step == {"level": 3, "text": Q1["explanation"], "show_links": True, "reveal": True}


def test_show_me_jumps_to_the_answer():
    assert next_step(Q1, 1, show_me=True)["level"] == 3


def test_next_step_needs_at_least_one_wrong_attempt():
    for attempts in (0, -1):
        with pytest.raises(ValueError):
            next_step(Q1, attempts)


def test_hints_shown_before_level_3_never_contain_the_answer():
    """The ladder must not leak. Uses the same check as the data tests."""
    from test_mentor_data import correct_text, leaks
    for question in DATA["questions"]:
        if question["format"] in ("best_reply", "fill_blank"):
            for attempts in (1, 2):
                step = next_step(question, attempts)
                assert not leaks(step["text"], correct_text(question))
