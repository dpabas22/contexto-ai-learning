"""Tests for lookup, keyword search and the router. Run:  pytest -q test_retrieval.py"""
import pytest

from lesson_index import build_units
from retrieval import KeywordIndex, lookup, normalize, route, tokens

UNITS = build_units()
INDEX = KeywordIndex(UNITS)


def ids(results):
    return [unit_id for unit_id, _ in results]


# ---------------------------------------------------------------- text handling
def test_normalize_removes_accents_case_and_punctuation():
    assert normalize("¿Cuánto cuesta el Camarón?") == "cuanto cuesta el camaron"
    assert normalize("  3:45 p.m.!  ") == "3 45 p m"


def test_tokens_drop_stopwords_and_light_plurals():
    assert tokens("How do I say the numbers?") == ["number"]
    assert tokens("pesos") == ["peso"]
    assert "the" not in tokens("the market")


# ---------------------------------------------------------------- lookup
@pytest.mark.parametrize("query, expected", [
    ("Show me the verb ser", "verb:ser"),
    ("what does kilo mean", "vocab:market:kilo"),
    ("what does fiebre mean", "vocab:hospital:fiebre"),
    ("open the market conversation", "conv:conv001"),
    ("where can I find the hundreds numbers", "numbers:hundreds"),
    ("days of the week", "time:days"),
    ("the phrase ¿Cuánto cuesta?", "phrase:p048"),
])
def test_lookup_finds_explicit_requests(query, expected):
    assert ids(lookup(query, UNITS))[0] == expected


def test_english_meanings_count_only_when_the_question_asks_for_a_meaning():
    assert "verb:decir" not in ids(lookup("how to say what time it is", UNITS))
    assert "verb:decir" not in ids(lookup("how do I tell the doctor my head hurts", UNITS))
    assert "verb:decir" in ids(lookup("what does to tell mean", UNITS))


def test_scenario_names_need_the_word_conversation():
    assert "conv:conv001" not in ids(lookup("I am at the market", UNITS))
    assert "conv:conv001" in ids(lookup("the market conversation", UNITS))


def test_lookup_returns_nothing_when_no_name_appears():
    assert lookup("how do I rent an apartment", UNITS) == []


def test_generic_section_words_do_not_trigger_lookup_alone():
    assert lookup("what are the rules", UNITS) == []
    assert "numbers:rules" in ids(lookup("number rules", UNITS))


# ---------------------------------------------------------------- keyword search
def test_keyword_search_finds_descriptive_questions():
    top = ids(INDEX.search("how do I ask for a discount", k=3))
    assert "phrase:p050" in top or "vocab:market:descuento" in top


def test_scores_are_between_zero_and_one_and_sorted():
    results = INDEX.search("how do I pay with a card", k=5)
    scores = [s for _, s in results]
    assert results and all(0 < s <= 1 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_nonsense_and_empty_questions_return_nothing():
    assert INDEX.search("qwxz zzv", k=3) == []
    assert INDEX.search("", k=3) == []
    assert INDEX.search("how do i", k=3) == []          # only stopwords


def test_threshold_makes_the_search_more_cautious():
    loose = INDEX.search("how do I ask for a discount", k=3, min_score=0.0)
    strict = INDEX.search("how do I ask for a discount", k=3, min_score=0.99)
    assert loose and strict == []


def test_search_is_deterministic():
    assert INDEX.search("how do I count money in pesos") == INDEX.search("how do I count money in pesos")


# ---------------------------------------------------------------- router
def test_router_uses_lookup_for_explicit_questions():
    method, results = route("Show me the verb ser", UNITS, INDEX)
    assert method == "lookup" and ids(results)[0] == "verb:ser"


def test_router_falls_back_to_keyword_search():
    method, results = route("how do I ask for a discount", UNITS, INDEX)
    assert method == "keyword" and results


def test_router_can_say_nothing_is_covered():
    method, results = route("qwxz zzv", UNITS, INDEX, min_score=0.1)
    assert results == []
