"""Every lesson link in the quiz must exist in the registry and the index."""
import json
from pathlib import Path

import lesson_index
import mentor_registry

ROOT = Path(__file__).parent
QS = json.loads((ROOT / "mentor_questions.json").read_text(encoding="utf-8"))["questions"]


def test_every_related_link_resolves():
    reg = mentor_registry.build_registry(ROOT)
    units = {u.id for u in lesson_index.build_units(ROOT)}
    for q in QS:
        for tid in q.get("related", []):
            assert tid in reg, (q["id"], tid)
            assert tid in units, (q["id"], tid)
