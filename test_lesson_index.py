"""Tests for the lesson index. Run:  pytest -q test_lesson_index.py"""
from collections import Counter

from lesson_index import SECTION_HINTS, build_units
from mentor_registry import TAB_KEYS, build_registry

UNITS = build_units()
REGISTRY = build_registry()


def test_one_unit_for_every_registry_target_and_nothing_else():
    ids = [u.id for u in UNITS]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(REGISTRY)


def test_counts_by_type():
    counts = Counter(u.type for u in UNITS)
    assert counts["vocab"] == 120 and counts["verb"] == 18
    assert counts["phrase"] == 50 and counts["conv"] == 4 and counts["pronoun"] == 7


def test_every_unit_is_complete():
    for unit in UNITS:
        assert unit.title.strip() and unit.text.strip(), unit.id
        assert unit.tab in TAB_KEYS and unit.section, unit.id
        assert (unit.tab, unit.section) == (REGISTRY[unit.id]["tab"], REGISTRY[unit.id]["section"])


def test_only_content_the_app_shows_is_indexed():
    # the expanded vocabulary (restaurants, banking, medical...) is not shown in any tab yet
    assert not any(u.id.startswith("expanded") for u in UNITS)
    texts = " ".join(u.text for u in UNITS).lower()
    assert "cajero automático" not in texts          # a banking word that no tab displays


def test_every_hint_belongs_to_a_real_section_and_is_used():
    by_id = {u.id: u for u in UNITS}
    for target_id, hint in SECTION_HINTS.items():
        assert target_id in REGISTRY, target_id
        assert hint.split()[0] in by_id[target_id].text


def test_vocab_has_english_glosses_and_conversations_have_scoped_names():
    by_id = {u.id: u for u in UNITS}
    assert "kilogram" in by_id["vocab:market:kilo"].glosses
    assert "to say" in [g.lower() for g in by_id["verb:decir"].glosses]
    assert "market" in [s.lower() for s in by_id["conv:conv001"].scoped_aliases]
    assert by_id["conv:conv001"].aliases == ()


def test_index_is_deterministic():
    assert build_units() == UNITS
