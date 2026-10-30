"""
lesson_index.py - one searchable "unit" for every lesson the app really shows.

A unit has an id that matches the route registry (for example verb:ser or
vocab:market:kilo), a title, a few aliases for exact lookup, and plain text for
search. Units are built from the same data files as the app, so when content
changes the index changes with it.

Only content the app actually DISPLAYS is indexed. (The expanded vocabulary file
holds restaurants, shopping, banking and medical words that no tab shows yet, so
sending a learner there would lead nowhere.)
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from mentor_registry import SCENARIO_FILES, build_registry

BASE = Path(__file__).parent

# Short descriptions that help search find a section from a learner's own words.
# They are retrieval hints, written by hand, and are never shown to learners.
SECTION_HINTS = {
    "numbers:basic": "count numbers one to ten uno dos tres counting basics",
    "numbers:tens": "tens ten twenty thirty forty fifty diez veinte treinta counting by tens",
    "numbers:teens_twenties": "eleven to twenty nine once doce trece veinte veintiuno teens",
    "numbers:ordinals": "ordinal numbers first second third primero segundo tercero order position",
    "numbers:hundreds": "hundreds large numbers cien ciento doscientos how to say 100 200 300",
    "numbers:thousands": "thousands mil how to say 1000 2000 10000 big numbers prices",
    "numbers:millions": "millions millón mil millones how to say a million large numbers",
    "numbers:money_examples": "prices out loud say prices in pesos how much it costs reading money amounts count money",
    "numbers:rules": "number rules cien versus ciento un uno una agreement y between tens and units common number mistakes",
    "numbers:say_any_number": "type any number and hear how to say it in Spanish number converter",
    "math:operations": "plus minus times divided by más menos por entre add subtract multiply divide arithmetic words",
    "math:comparisons": "greater than less than equal mayor que menor que igual compare numbers",
    "math:questions": "how much is it total change split the bill cuánto es total cambio cuenta questions about adding",
    "math:fractions_percent": "half quarter third percent porcentaje por ciento la mitad fractions discount percent",
    "math:examples": "say a sum aloud example calculations two plus two order of operations brackets",
    "math:shopping_examples": "shopping math tacos price change from 500 pesos splitting the bill twenty percent",
    "time:clock_examples": "telling time clock examples what time is it hora son las es la una y media menos cuarto am pm",
    "time:ask_and_answer": "ask what time it is when does it open close qué hora es a qué hora abre cierra schedule",
    "time:rules": "time rules es la una son las y cuarto y media menos 24-hour clock morning afternoon night de la mañana tarde noche",
    "time:days": "days of the week monday tuesday lunes martes miércoles weekdays weekend",
    "time:months": "months of the year enero febrero meses calendar seasons dates",
    "measurements:weight": "weight gram kilogram gramo kilo how heavy buying by weight",
    "measurements:volume": "volume liter milliliter litro mililitro how much liquid",
    "measurements:length": "length centimeter meter centímetro metro distance size how long",
    "measurements:fractions": "fractions half quarter medio cuarto un tercio medio kilo quarter kilo amounts",
    "money:currencies": "currency pesos dollars money mexican peso US dollar exchange symbols",
    "money:payment_methods": "payment methods cash card credit debit efectivo tarjeta how to pay pagar",
    "transport:areas": "neighborhoods areas of Querétaro where to live colonias districts zones",
    "transport:options": "transportation taxi bus uber getting around how to travel transporte camión",
}

# section names too common to count as an exact match on their own ("rules", "examples"...)
GENERIC_KEYS = {"rules", "examples", "questions", "operations", "comparisons", "basic", "tens",
                "ask_and_answer", "clock_examples", "money_examples", "shopping_examples",
                "fractions_percent", "teens_twenties"}

SCENARIO_WORDS = {
    "market": "market mercado shopping buy food",
    "hospital": "hospital doctor medical health clinic",
    "papeleria": "papelería paper store stationery printing school supplies",
    "school": "school escuela education enrollment student",
}


@dataclass(frozen=True)
class Unit:
    """aliases        names that always count as an exact match (Spanish titles, section names)
    glosses        English meanings; they count only when the question asks what something MEANS,
                   because words like "to say" or "tell" appear in ordinary questions
    scoped_aliases names that count only when the question also names the kind of lesson,
                   for example "market" together with "conversation"
    """
    id: str
    type: str
    title: str
    aliases: tuple
    text: str
    tab: str
    section: str
    glosses: tuple = ()
    scoped_aliases: tuple = ()


def _strings(obj):
    """Every text value inside nested lists and dictionaries."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _strings(value)


def _variants(text):
    """'to search/look for (verb)' -> ['to search', 'look for']"""
    text = re.split(r"\(", text)[0]
    parts = [p.strip() for p in re.split(r"[/;,]", text)]
    return [p for p in parts if p]


def _load(name, base):
    with open(Path(base) / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_units(base=BASE):
    """Return the list of Unit objects for everything the app shows."""
    registry = build_registry(base)
    units = []

    def add(unit_id, kind, title, aliases, text, glosses=(), scoped=()):
        entry = registry[unit_id]
        units.append(Unit(unit_id, kind, title, tuple(a for a in aliases if a),
                          " ".join(text.split()), entry["tab"], entry["section"],
                          tuple(g for g in glosses if g), tuple(s for s in scoped if s)))

    for scenario, filename in SCENARIO_FILES.items():
        for word in _load(filename, base)["vocabulary"]:
            text = " ".join([word["spanish"], word["english"], word.get("example_spanish", ""),
                             word.get("example_english", ""), SCENARIO_WORDS[scenario]])
            add(f"vocab:{scenario}:{word['spanish']}", "vocab", word["spanish"],
                [word["spanish"]], text, glosses=_variants(word["english"]))

    for verb in _load("grammar_verbs.json", base)["verbs"]:
        name = verb["infinitive"]
        text = " ".join([name, verb["english"], verb.get("tips", ""),
                         "verb conjugation present preterite future tense"] + list(_strings(verb["conjugations"])))
        add(f"verb:{name.lower()}", "verb", name, [name], text, glosses=_variants(verb["english"]))

    for pronoun in _load("pronouns.json", base)["pronouns"]:
        text = " ".join([pronoun["person"], "pronoun pronouns"] + list(_strings(pronoun["pronouns"])))
        add(f"pronoun:{pronoun['id']}", "pronoun", pronoun["person"], [], text)

    for phrase in _load("phrases.json", base)["phrases"]:
        text = " ".join(str(phrase.get(k, "")) for k in
                        ("spanish", "english", "category", "context", "cultural_note", "alternative"))
        add(f"phrase:{phrase['id']}", "phrase", phrase["spanish"], [phrase["spanish"]], text)

    for conv in _load("conversations.json", base)["conversations"]:
        lines = [f"{x['spanish']} {x['english']}" for x in conv["exchanges"]]
        names = re.findall(r"[^()]+", conv["scenario"])
        text = " ".join([conv["scenario"], conv["setting"], conv["difficulty"], "conversation dialogue"]
                        + conv["learning_points"] + lines)
        add(f"conv:{conv['id']}", "conv", conv["scenario"], [], text,
            scoped=[n.strip() for n in names])

    refs = _load("references.json", base)
    sections = {
        "numbers": refs["numbers"], "math": refs["math"], "time": refs["time"],
        "measurements": refs["measurements"], "money": refs["money"],
    }
    for target_id, entry in registry.items():
        kind, _, key = target_id.partition(":")
        if kind in sections and key in sections[kind]:
            hint = SECTION_HINTS.get(target_id, "")
            name = key.replace("_", " ")
            alias = f"{kind} {name}" if key in GENERIC_KEYS else name
            add(target_id, kind, entry["label"], [alias],
                f"{entry['label']} {hint} " + " ".join(_strings(sections[kind][key])))
    for target_id in ("numbers:say_any_number",):
        add(target_id, "numbers", registry[target_id]["label"], ["say any number"],
            f"{registry[target_id]['label']} {SECTION_HINTS[target_id]}")

    expanded = _load("expanded_vocab.json", base)["neighborhoods"]
    for target_id, source in (("transport:areas", "querétaro_areas"), ("transport:options", "transportation")):
        add(target_id, "transport", registry[target_id]["label"], [],
            f"{registry[target_id]['label']} {SECTION_HINTS[target_id]} " + " ".join(_strings(expanded[source])))

    return units
