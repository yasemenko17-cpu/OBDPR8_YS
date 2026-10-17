"""Реєстр відкритих перевірок студента: для кожної задачі пари (ідентифікатор, функція). Закриті перевірки є лише у викладача."""
import checks_open as o

SPECS = {
    1: [("nodirty", o.t01_nodirty), ("final", o.t01_final)],
    2: [("nonrepeatable", o.t02_nonrepeatable), ("phantom", o.t02_phantom)],
    3: [("snapshot", o.t03_snapshot), ("serialization", o.t03_serialization)],
    4: [("lost", o.t04_lost), ("stale", o.t04_stale)],
    5: [("blocked", o.t05_blocked), ("noloss", o.t05_noloss)],
    6: [("both", o.t06_both), ("violated", o.t06_violated)],
    7: [("onefails", o.t07_onefails), ("invariant", o.t07_invariant)],
    8: [("nowait", o.t08_nowait), ("skip", o.t08_skip)],
    9: [("deadlock", o.t09_deadlock), ("survivor", o.t09_survivor)],
    10: [("diag", o.t10_diag), ("final", o.t10_final)],
}
