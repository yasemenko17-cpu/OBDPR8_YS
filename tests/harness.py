"""Виконання сценарію студента на PostgreSQL і запуск перевірок над спостереженим результатом (трасою)."""
import inspect

import pytest

import pgutil
import txsim
from ctxutil import Ctx, fail
from schemas import CFG, SCHEMAS

_TRACES = {}


class Boom(Exception):
    pass


def call(mod, task, set_no):
    """Викликає scenario() варіанта. Еталон приймає номер набору; студентська функція без параметрів
    працює для набору, що випливає з константи VARIANT."""
    fn = getattr(mod, "scenario", None)
    if fn is None:
        pytest.fail("У файлі варіанта немає функції scenario()", pytrace=False)
    if inspect.signature(fn).parameters:
        return fn(set_no)
    variant = getattr(mod, "VARIANT", 0)
    if not variant:
        pytest.fail("Змінну VARIANT не задано: впишіть номер свого варіанта (1-30) на початку файла", pytrace=False)
    if (variant - 1) // 3 + 1 != task:
        pytest.fail(f"VARIANT = {variant} не відповідає задачі {task}: файл variant_{task:02d}.py призначений "
                    f"для варіантів {3 * task - 2}-{3 * task}", pytrace=False)
    if (variant - 1) % 3 + 1 != set_no:
        pytest.skip("перевірка іншого набору даних")
    try:
        return fn()
    except NotImplementedError:
        pytest.fail("Функція scenario() ще не реалізована (NotImplementedError)", pytrace=False)


def _run_once(mod, task, set_no):
    steps = call(mod, task, set_no)
    try:
        db = pgutil.Db()
    except Exception as error:  # noqa: BLE001
        pytest.fail("Немає підключення до PostgreSQL (" + str(error).strip().splitlines()[0] + "). Запустіть сервер і перевірте "
                    "змінні PGHOST, PGPORT, PGUSER, PGPASSWORD (див. README.md).", pytrace=False)
    try:
        db.run(SCHEMAS[set_no])
        return txsim.run_scenario(db.schema, steps)
    except txsim.ScenarioError as error:
        pytest.fail(str(error), pytrace=False)
    finally:
        db.close()


def trace_of(mod, task, set_no):
    key = (getattr(mod, "__file__", id(mod)), task, set_no)
    if key not in _TRACES:
        _TRACES[key] = _run_once(mod, task, set_no)
    return _TRACES[key]


def run_check(mod, task, set_no, chk):
    trace = trace_of(mod, task, set_no)
    ctx = Ctx(task, set_no, trace, CFG[set_no], lambda: _run_once(mod, task, set_no))
    chk["func"](ctx)
