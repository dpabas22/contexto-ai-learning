"""
mentor_core.py - the mentor's rules engine (no AI in here).

YOUR TURN: replace each `raise NotImplementedError` with working code.
Do them in this order. Run the tests after each one:

    pytest -q test_mentor_core.py

A test turns green when its function is right. Don't worry about the red
ones: they are the functions you haven't written yet.

A "question" below is one dictionary from mentor_questions.json.
"""
import re


def parse_number(text):
    """
    Turn what a learner typed into a whole number, or return None.

    Accept:   "120"   " 120 "   "1,020"   "$120"   "120 pesos"   "120 PESOS"
    Reject (return None):   ""   "abc"   "12.5"   "-5"   "1,2,3"   "10,20"

    Rules to follow:
      * a comma is a thousands separator, so it must sit in groups of
        exactly three digits:  1,020 is fine,  10,20 is not
      * remove a leading "$" and a trailing "peso" or "pesos" (any case)
      * decimals and negative numbers are not allowed

    Tools you may find useful: str.strip(), str.lower(), str.replace(),
    str.endswith(), re.fullmatch(), int()
    """
    raise NotImplementedError


def check_choice(question, chosen_id):
    """
    For best_reply and fill_blank questions: return True if chosen_id is the
    correct option, otherwise False.

    If chosen_id is not one of the question's option ids, raise ValueError.
    """
    raise NotImplementedError


def diagnose_choice(question, chosen_id):
    """
    For a WRONG choice return {"tag": ..., "why_not": ...} copied from that
    option. For the correct choice return None.
    Raise ValueError if chosen_id is not an option id.
    """
    raise NotImplementedError


def expected_number(question, price):
    """
    For hear_and_pay questions, the number the learner should type.

      task "price"  -> the price itself
      task "change" -> question["generator"]["paid"] minus the price
    """
    raise NotImplementedError


def diagnose_number(question, price, given):
    """
    Compare what the learner typed (`given`, an int) with the right answer.
    Return None if it is right, otherwise a tag naming the likely mistake:

      task "price":
        "missed_hundreds"  given equals price % 100            (120 -> 20)
        "missed_tens"      given equals only the hundreds part (120 -> 100)
        "ciento_vs_mil"    given equals price * 10, or 1000 + price % 100
                           (120 -> 1200 or 1020)
      task "change":
        "added_instead_of_subtracted"   given equals paid + price
        "repeated_price"                given equals the price

      anything else that is wrong -> "other"

    Check the specific tags first, then fall back to "other".
    """
    raise NotImplementedError


def next_step(question, wrong_attempts, show_me=False):
    """
    The hint ladder. `wrong_attempts` is how many wrong answers the learner
    has given so far on this question (1, 2, 3, ...).

    Return a dictionary:

      wrong_attempts == 1:
          {"level": 1, "text": <first hint>, "show_links": False, "reveal": False}
      wrong_attempts == 2:
          {"level": 2, "text": <second hint>, "show_links": True, "reveal": False}
      wrong_attempts >= 3, or show_me is True:
          {"level": 3, "text": <the explanation>, "show_links": True, "reveal": True}

    Raise ValueError if wrong_attempts is less than 1.
    The hints and explanation live in question["hints"] and
    question["explanation"].
    """
    raise NotImplementedError
