"""Відкриті тести задач (приклади перевірок; повний набір є у викладача): 10 задач × 3 набори даних. Ідентифікатор тесту: T<задача>-S<набір>-<перевірка>.

Запуск повного набору: pytest. Одна задача: pytest -k T05. Один набір: pytest -k "T05-S2".
"""
import pytest
from conftest import load
from harness import run_check
from specs import SPECS

CASES = [(t, s, cid, fn) for t in sorted(SPECS) for s in (1, 2, 3) for cid, fn in SPECS[t]]


@pytest.mark.parametrize("task,set_no,cid,fn", CASES, ids=[f"T{t:02d}-S{s}-{c}" for t, s, c, _ in CASES])
def test_check(task, set_no, cid, fn):
    run_check(load(task), task, set_no, {"id": cid, "func": fn})
