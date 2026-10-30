"""Tests for the evaluation set and the scoring code. Run:  pytest -q test_evaluate.py"""
from collections import Counter

import pytest

import evaluate_retrieval as ev
from mentor_registry import build_registry

QUERIES = ev.load_queries()
REGISTRY = build_registry()


# ---------------------------------------------------------------- the question set
def test_forty_queries_with_the_planned_mix():
    assert len(QUERIES) == 40
    assert Counter(q["type"] for q in QUERIES) == {
        "explicit": 10, "descriptive": 15, "confusion": 10, "uncovered": 5}


def test_ids_are_unique_and_both_splits_exist():
    ids = [q["id"] for q in QUERIES]
    assert len(ids) == len(set(ids))
    assert {q["split"] for q in QUERIES} == {"dev", "test"}
    for kind in ("explicit", "descriptive", "confusion", "uncovered"):
        assert {q["split"] for q in QUERIES if q["type"] == kind} == {"dev", "test"}


def test_every_expected_target_exists():
    for q in QUERIES:
        for target in q["expected"]:
            assert target in REGISTRY, (q["id"], target)
        assert (q["type"] == "uncovered") == (q["expected"] == [])


# ---------------------------------------------------------------- scoring
def test_score_on_a_tiny_example():
    queries = [
        {"id": "a", "type": "explicit", "expected": ["x"]},
        {"id": "b", "type": "explicit", "expected": ["y"]},
        {"id": "c", "type": "descriptive", "expected": ["z"]},
        {"id": "d", "type": "uncovered", "expected": []},
        {"id": "e", "type": "uncovered", "expected": []},
    ]
    results = {"a": ["x", "q"], "b": ["q", "y"], "c": [], "d": [], "e": ["w"]}
    metrics = ev.score(queries, results)
    assert metrics["hit@1"] == pytest.approx(1 / 3)          # only "a" has the answer first
    assert metrics["hit@3"] == pytest.approx(2 / 3)          # "a" and "b"
    assert metrics["false_refusal"] == pytest.approx(1 / 3)  # "c" returned nothing
    assert metrics["correct_refusal"] == pytest.approx(1 / 2)
    assert metrics["hit@3_by_type"] == {"descriptive": 0.0, "explicit": 1.0}


def test_balanced_score_weights_both_halves_equally():
    assert ev.balanced({"hit@3": 1.0, "correct_refusal": 0.0}) == 0.5


# ---------------------------------------------------------------- the whole run
def test_baseline_run_is_complete_and_sensible():
    outcome = ev.run_baseline()
    assert outcome["n_units"] == len(REGISTRY)
    assert outcome["n_dev"] + outcome["n_test"] == 40
    assert set(outcome["methods"]) == set(ev.RETRIEVERS)
    for data in outcome["methods"].values():
        assert data["threshold"] in ev.THRESHOLDS
        for split in ("dev", "test"):
            for key in ("hit@1", "hit@3", "false_refusal", "correct_refusal"):
                assert 0.0 <= data[split][key] <= 1.0
            assert data[split]["hit@1"] <= data[split]["hit@3"]


def test_lookup_is_cautious_and_good_at_explicit_requests():
    methods = ev.run_baseline()["methods"]
    assert methods["lookup"]["test"]["hit@3_by_type"]["explicit"] == 1.0
    assert methods["lookup"]["test"]["correct_refusal"] == 1.0


def test_threshold_is_chosen_on_dev_only():
    outcome = ev.run_baseline()
    units = ev.build_units()
    index = ev.KeywordIndex(units)
    dev = [q for q in QUERIES if q["split"] == "dev"]
    assert outcome["methods"]["keyword"]["threshold"] == ev.choose_threshold("keyword", dev, units, index)


def test_results_are_repeatable():
    first = ev.run_baseline()["methods"]["router"]["test"]
    second = ev.run_baseline()["methods"]["router"]["test"]
    for key in ("hit@1", "hit@3", "false_refusal", "correct_refusal"):
        assert first[key] == second[key]


def test_report_names_every_method_and_warns_about_optimism():
    report = ev.format_report(ev.run_baseline())
    for name in ev.RETRIEVERS:
        assert f"| {name} |" in report
    assert "optimistic" in report
