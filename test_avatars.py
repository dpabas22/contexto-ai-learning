"""Tests for the characters. Run:  pytest -q test_avatars.py"""
import re
import xml.etree.ElementTree as ET

import pytest

import avatars

COMBOS = [(key, mood) for key in avatars.AVATARS for mood in avatars.MOODS]


@pytest.mark.parametrize("key, mood", COMBOS)
def test_every_drawing_is_valid_svg_with_a_label(key, mood):
    svg = avatars.avatar_svg(key, mood)
    root = ET.fromstring(svg)                                   # raises if the XML is broken
    assert root.tag.endswith("svg")
    name = avatars.AVATARS[key]["name"]
    assert name in root.attrib["aria-label"] and root.attrib["role"] == "img"
    assert f"<title>{name}" in svg


@pytest.mark.parametrize("key, mood", COMBOS)
def test_drawings_are_self_contained_and_safe(key, mood):
    svg = avatars.avatar_svg(key, mood)
    assert "<script" not in svg.lower() and "href" not in svg.lower()
    assert "onload" not in svg.lower()
    assert svg.count("http") == 1 and "http://www.w3.org/2000/svg" in svg   # only the namespace


@pytest.mark.parametrize("key", list(avatars.AVATARS))
def test_motion_is_gentle_and_can_be_switched_off(key):
    svg = avatars.avatar_svg(key)
    assert "prefers-reduced-motion: reduce" in svg
    durations = [float(d) for d in re.findall(r"animation:[a-z0-9]+ ([0-9.]+)s", svg)]
    assert durations and min(durations) >= 1.0                  # nothing flickers quickly


def test_characters_and_moods_look_different():
    drawings = {(k, m): avatars.avatar_svg(k, m) for k, m in COMBOS}
    assert len(set(drawings.values())) == len(COMBOS)


def test_unknown_character_or_mood_is_refused():
    with pytest.raises(ValueError):
        avatars.avatar_svg("dragon")
    with pytest.raises(ValueError):
        avatars.avatar_svg("pipo", "angry")


def test_all_speech_is_supportive_and_complete():
    assert set(avatars.SPEECH) == set(avatars.MOOD_FOR)
    assert set(avatars.MOOD_FOR.values()) <= set(avatars.MOODS)
    for kind in avatars.SPEECH:
        line = avatars.speech(kind, "Pipo")
        assert line.strip() and "{" not in line
    assert "Pipo" in avatars.speech("greet", "Pipo")
    banned = ("mal", "tonto", "error", "fallaste")             # no scolding words
    for lines in avatars.SPEECH.values():
        assert not any(word in line.lower() for line in lines for word in banned)
    assert any("Tú puedes" in line for line in avatars.SPEECH["retry"])


def test_reduce_motion_rule_can_be_left_out_by_a_parent():
    with_rule = avatars.avatar_svg("pipo")
    without_rule = avatars.avatar_svg("pipo", respect_reduced_motion=False)
    assert "prefers-reduced-motion" in with_rule
    assert "prefers-reduced-motion" not in without_rule
    ET.fromstring(without_rule)                       # still valid SVG
    assert "@keyframes bob" in without_rule           # the motion itself is still there
