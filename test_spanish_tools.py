"""Run with:  pytest -q
Expected values below are written by hand from Spanish spelling rules,
NOT produced by the code, so the tests can catch real mistakes."""
import pytest
from spanish_tools import (
    number_to_spanish, number_to_english, time_to_spanish, time_variants,
    period_of_day, clock_svg,
)


@pytest.mark.parametrize("n, expected", [
    (0, "cero"), (1, "uno"), (10, "diez"), (15, "quince"), (16, "dieciséis"),
    (20, "veinte"), (21, "veintiuno"), (22, "veintidós"), (23, "veintitrés"),
    (26, "veintiséis"), (29, "veintinueve"), (30, "treinta"),
    (31, "treinta y uno"), (45, "cuarenta y cinco"), (99, "noventa y nueve"),
    (100, "cien"), (101, "ciento uno"), (115, "ciento quince"),
    (121, "ciento veintiuno"), (200, "doscientos"), (500, "quinientos"),
    (700, "setecientos"), (900, "novecientos"),
    (999, "novecientos noventa y nueve"),
    (1000, "mil"), (1001, "mil uno"), (1250, "mil doscientos cincuenta"),
    (2000, "dos mil"), (2026, "dos mil veintiséis"), (10000, "diez mil"),
    (15000, "quince mil"), (21000, "veintiún mil"), (100000, "cien mil"),
    (101000, "ciento un mil"), (250000, "doscientos cincuenta mil"),
    (999999, "novecientos noventa y nueve mil novecientos noventa y nueve"),
    (1_000_000, "un millón"), (1_000_001, "un millón uno"),
    (2_000_000, "dos millones"), (2_500_000, "dos millones quinientos mil"),
    (21_000_000, "veintiún millones"), (100_000_000, "cien millones"),
    (1_000_000_000, "mil millones"),
    (1_500_000_000, "mil quinientos millones"),
    (-5, "menos cinco"),
])
def test_numbers(n, expected):
    assert number_to_spanish(n) == expected


def test_before_noun_forms():
    assert number_to_spanish(1, before_noun=True) == "un"
    assert number_to_spanish(1, "f", before_noun=True) == "una"
    assert number_to_spanish(21, before_noun=True) == "veintiún"
    assert number_to_spanish(21, "f", before_noun=True) == "veintiuna"
    assert number_to_spanish(31, before_noun=True) == "treinta y un"
    assert number_to_spanish(201, "f", before_noun=True) == "doscientas una"
    assert number_to_spanish(200_000, "f", before_noun=True) == "doscientas mil"
    # 'millones' is masculine, so its multiplier stays masculine
    assert number_to_spanish(200_000_000, "f", before_noun=True) == "doscientos millones"


def test_number_limits():
    with pytest.raises(ValueError):
        number_to_spanish(10**12)
    with pytest.raises(TypeError):
        number_to_spanish("5")
    with pytest.raises(TypeError):
        number_to_spanish(True)


@pytest.mark.parametrize("n, expected", [
    (0, "zero"), (13, "thirteen"), (21, "twenty-one"), (100, "one hundred"),
    (1250, "one thousand two hundred fifty"),
    (2026, "two thousand twenty-six"),
    (1_000_000, "one million"), (1_000_000_000, "one billion"),
])
def test_english(n, expected):
    assert number_to_english(n) == expected


@pytest.mark.parametrize("h, m, expected", [
    (12, 0, "Es mediodía"),
    (0, 0, "Es medianoche"),
    (12, 30, "Son las doce y media del día"),
    (0, 30, "Son las doce y media de la noche"),
    (13, 0, "Es la una de la tarde"),
    (1, 0, "Es la una de la madrugada"),
    (1, 15, "Es la una y cuarto de la madrugada"),
    (15, 45, "Son las cuatro menos cuarto de la tarde"),
    (3, 45, "Son las cuatro menos cuarto de la madrugada"),
    (16, 55, "Son las cinco menos cinco de la tarde"),
    (4, 55, "Son las cinco menos cinco de la madrugada"),
    (6, 15, "Son las seis y cuarto de la mañana"),
    (21, 5, "Son las nueve y cinco de la noche"),
    (22, 40, "Son las once menos veinte de la noche"),
    (23, 50, "Son las doce menos diez de la noche"),
    (12, 45, "Es la una menos cuarto del día"),
    (14, 10, "Son las dos y diez de la tarde"),
])
def test_times(h, m, expected):
    assert time_to_spanish(h, m) == expected


def test_time_validation():
    with pytest.raises(ValueError):
        time_to_spanish(24, 0)
    with pytest.raises(ValueError):
        time_to_spanish(10, 60)


def test_time_variants():
    assert "Faltan quince para las cuatro de la tarde" in time_variants(15, 45)
    assert "Un cuarto para las cuatro de la tarde" in time_variants(15, 45)
    assert "Faltan cinco para las cinco de la tarde" in time_variants(16, 55)
    assert "Son las cuatro cuarenta y cinco de la tarde" in time_variants(16, 45)
    assert "Faltan diez para la una del día" in time_variants(12, 50)
    assert "Falta un minuto para las tres de la tarde" in time_variants(14, 59)
    assert "Son las tres en punto de la tarde" in time_variants(15, 0)


def test_period_of_day():
    assert [period_of_day(h) for h in (0, 3, 9, 12, 15, 22)] == [
        "de la noche", "de la madrugada", "de la mañana", "del día",
        "de la tarde", "de la noche",
    ]


def test_clock_svg_hands():
    svg = clock_svg(3, 0)   # hour hand points right (3 o'clock), minute hand up
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert 'x2="148.0" y2="100.0"' in svg      # hour hand: 100 + 48, same height
    assert 'x2="100.0" y2="28.0"' in svg       # minute hand: straight up, length 72
    assert "a. m." in svg and "p. m." in clock_svg(15, 0)
