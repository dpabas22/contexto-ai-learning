"""
mentor_engine.py - a WORKING copy of the six rules, so the adult page runs
while you write your own mentor_core.py. No AI in here.

Tip: try your own functions first. Peek here only after you finish,
to compare. Later, the page can switch to mentor_core with one import line.
"""
import re


def parse_number(text):
    t = str(text).strip().lower()
    if t.startswith("$"):
        t = t[1:].strip()
    t = re.sub(r"\s*pesos?$", "", t).strip()
    if re.fullmatch(r"\d{1,3}(,\d{3})+", t) or re.fullmatch(r"\d+", t):
        return int(t.replace(",", ""))
    return None


def _find(question, chosen_id):
    for opt in question["options"]:
        if opt["id"] == chosen_id:
            return opt
    raise ValueError(f"unknown option id: {chosen_id!r}")


def check_choice(question, chosen_id):
    _find(question, chosen_id)
    return chosen_id == question["correct"]


def diagnose_choice(question, chosen_id):
    opt = _find(question, chosen_id)
    if chosen_id == question["correct"]:
        return None
    return {"tag": opt.get("tag"), "why_not": opt.get("why_not")}


def expected_number(question, price):
    if question["task"] == "change":
        return question["generator"]["paid"] - price
    return price


def diagnose_number(question, price, given):
    if given == expected_number(question, price):
        return None
    if question["task"] == "price":
        if given == price % 100:
            return "missed_hundreds"
        if given == (price // 100) * 100:
            return "missed_tens"
        if given in (price * 10, 1000 + price % 100):
            return "ciento_vs_mil"
    elif question["task"] == "change":
        if given == question["generator"]["paid"] + price:
            return "added_instead_of_subtracted"
        if given == price:
            return "repeated_price"
    return "other"


def next_step(question, wrong_attempts, show_me=False):
    if wrong_attempts < 1:
        raise ValueError("wrong_attempts must be at least 1")
    if show_me or wrong_attempts >= 3:
        return {"level": 3, "text": question["explanation"], "show_links": True, "reveal": True}
    if wrong_attempts == 1:
        return {"level": 1, "text": question["hints"][0], "show_links": False, "reveal": False}
    return {"level": 2, "text": question["hints"][1], "show_links": True, "reveal": False}
