"""
mentor_registry.py - the list of every place the mentor may send a learner.

Each target has an ID such as  vocab:market:kilo  or  verb:querer.
The registry is BUILT FROM THE DATA FILES, so if a word or verb is removed
from the content, its ID disappears and the tests fail instead of the app
quietly showing a dead button.

An entry looks like:
    {"id": "verb:querer", "label": "Verb: Querer", "tab": "grammar",
     "section": "verbs", "item": "Querer"}

`tab` and `section` are short keys. A later step maps them to the real
Streamlit tabs and widgets.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent

TAB_KEYS = {
    "conversations", "grammar", "market", "hospital", "papeleria", "school",
    "measurements", "time", "numbers", "money", "transportation",
}

SCENARIO_FILES = {
    "market": "market_vocab.json",
    "hospital": "hospital_vocab.json",
    "papeleria": "papeleria_vocab.json",
    "school": "school_context_vocab.json",
}

# which Numbers sub-tab shows each section of references.json
NUMBERS_SECTION = {
    "basic": "counting", "tens": "counting", "teens_twenties": "counting",
    "ordinals": "counting",
    "hundreds": "hundreds_millions", "thousands": "hundreds_millions",
    "millions": "hundreds_millions", "money_examples": "hundreds_millions",
    "rules": "hundreds_millions",
}
MATH_SECTIONS = ("operations", "comparisons", "questions", "fractions_percent",
                 "examples", "shopping_examples")
TIME_SECTION = {
    "clock_examples": "telling_time", "ask_and_answer": "telling_time",
    "rules": "telling_time", "days": "days_months", "months": "days_months",
}


def _load(name, base):
    with open(Path(base) / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _add(registry, target_id, label, tab, section, item=None):
    if target_id in registry:
        raise ValueError(f"Duplicate registry id: {target_id}")
    registry[target_id] = {
        "id": target_id, "label": label, "tab": tab,
        "section": section, "item": item,
    }


def build_registry(base=BASE):
    """Return {target_id: entry} for everything a learner can be sent to."""
    registry = {}

    # vocabulary words, one tab per scenario
    for scenario, filename in SCENARIO_FILES.items():
        for entry in _load(filename, base)["vocabulary"]:
            word = entry["spanish"]
            _add(registry, f"vocab:{scenario}:{word}", f"Word: {word}",
                 scenario, "vocab", word)

    # verbs (Grammar > Verbs)
    for verb in _load("grammar_verbs.json", base)["verbs"]:
        name = verb["infinitive"]
        _add(registry, f"verb:{name.lower()}", f"Verb: {name}",
             "grammar", "verbs", name)

    # pronouns and phrases (Grammar > Pronouns / Phrases)
    for pronoun in _load("pronouns.json", base)["pronouns"]:
        _add(registry, f"pronoun:{pronoun['id']}", f"Pronoun: {pronoun['person']}",
             "grammar", "pronouns", pronoun["id"])
    for phrase in _load("phrases.json", base)["phrases"]:
        _add(registry, f"phrase:{phrase['id']}", f"Phrase: {phrase['spanish']}",
             "grammar", "phrases", phrase["id"])

    # conversations
    for conversation in _load("conversations.json", base)["conversations"]:
        _add(registry, f"conv:{conversation['id']}",
             f"Conversation: {conversation['scenario']}",
             "conversations", "conversation", conversation["scenario"])

    # reference sections
    refs = _load("references.json", base)
    for key in refs["numbers"]:
        if key in NUMBERS_SECTION:
            _add(registry, f"numbers:{key}", f"Numbers: {key.replace('_', ' ')}",
                 "numbers", NUMBERS_SECTION[key], key)
    _add(registry, "numbers:say_any_number", "Numbers: say any number",
         "numbers", "say_any_number", None)
    for key in MATH_SECTIONS:
        if key in refs["math"]:
            _add(registry, f"math:{key}", f"Math phrases: {key.replace('_', ' ')}",
                 "numbers", "math", key)
    for key, section in TIME_SECTION.items():
        if key in refs["time"]:
            _add(registry, f"time:{key}", f"Time: {key.replace('_', ' ')}",
                 "time", section, key)
    for key in refs["measurements"]:
        _add(registry, f"measurements:{key}", f"Measurements: {key}",
             "measurements", key, key)

    # Money tab: the app shows currencies and payment methods
    for key in ("currencies", "payment_methods"):
        if key in refs["money"]:
            _add(registry, f"money:{key}", f"Money: {key.replace('_', ' ')}",
                 "money", key, key)

    # Transportation tab: the app shows Querétaro areas and transportation options
    expanded = _load("expanded_vocab.json", base)["neighborhoods"]
    for target, source, label in (("areas", "querétaro_areas", "Querétaro areas"),
                                  ("options", "transportation", "Transportation options")):
        if source in expanded:
            _add(registry, f"transport:{target}", f"Transportation: {label}",
                 "transportation", target, None)

    return registry


def resolve(target_id, registry):
    """Return the registry entry for an ID, or None if it does not exist."""
    return registry.get(target_id)
