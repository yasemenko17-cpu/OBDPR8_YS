"""Допоміжні засоби перевірок: контекст прогону сценарію, повідомлення про невдачу, пошук кроків у трасі."""
import re

import pytest


class Ctx:
    """Контекст однієї перевірки: траса сценарію, параметри набору даних і функція повторного прогону."""

    def __init__(self, task, set_no, trace, cfg, rerun):
        self.task = task
        self.set_no = set_no
        self.t = trace
        self.c = cfg
        self.rerun = rerun


def fail(ctx, message, show=True):
    text = message
    if show:
        text += "\nЩо сталося у вашому сценарії:\n" + ctx.t.table()
    pytest.fail(text, pytrace=False)


def check(ctx, condition, message, show=True):
    if not condition:
        fail(ctx, message, show)


def table_rows(ctx, name):
    return ctx.t.final.get(name, [])


def item_qty(ctx, item_id=1):
    """Кількість у рядку основної таблиці (id = item_id) після сценарію."""
    for row in table_rows(ctx, ctx.c["item"]):
        if row[0] == item_id:
            return row[2]
    return None


def on_duty_ids(ctx):
    return [r[0] for r in table_rows(ctx, ctx.c["staff"]) if r[2]]


def first_step(ctx, pred):
    for s in ctx.t.steps:
        if pred(s):
            return s
    return None


def ok_commit(step):
    return step.err is None and step.status == "COMMIT"


def commits(ctx, sess):
    return [s for s in ctx.t.of(sess) if s.sql.strip().lower() in ("commit", "end", "commit work", "commit transaction")
            or s.status == "COMMIT"]


def find_id(sql):
    m = re.search(r"\bid\s*=\s*(\d+)", sql)
    return int(m.group(1)) if m else None


def reads_values(ctx, sess):
    return [s.scalar() for s in ctx.t.reads(sess)]
