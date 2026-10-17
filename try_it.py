"""Ручний прогін вашого сценарію без тестів.

Використання:  python try_it.py <номер_задачі>
Скрипт створює тимчасову схему, завантажує схему й дані вашого набору (за VARIANT у файлі variants/variant_NN.py),
виконує сценарій у двох сеансах A і B та друкує, що відбулося на кожному кроці: результат, помилку, очікування
блокування, стан транзакції й рівень ізоляції. Наприкінці друкує стан таблиць. Тимчасова схема видаляється.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))

import pgutil  # noqa: E402
import txsim  # noqa: E402
from conftest import load  # noqa: E402
from schemas import SCHEMAS  # noqa: E402


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(__doc__)
        return 1
    task = int(sys.argv[1])
    mod = load(task)
    variant = getattr(mod, "VARIANT", 0)
    if not variant or (variant - 1) // 3 + 1 != task:
        print(f"Вкажіть у variant_{task:02d}.py змінну VARIANT зі значенням {3 * task - 2}-{3 * task}.")
        return 1
    set_no = (variant - 1) % 3 + 1
    db = pgutil.Db()
    try:
        db.run(SCHEMAS[set_no])
        trace = txsim.run_scenario(db.schema, mod.scenario())
    except NotImplementedError:
        print("Функція scenario() ще не реалізована.")
        return 1
    except txsim.ScenarioError as error:
        print("Помилка сценарію:", error)
        return 1
    finally:
        db.close()
    print(f"Сеанси: A = процес {trace.pids['A']}, B = процес {trace.pids['B']}\n")
    for s in trace.steps:
        sql = " ".join(s.sql.split())
        print(f"{s.n:>2}. {s.sess}: {sql}")
        if s.err:
            print(f"      помилка {s.err}: {s.errmsg}")
        elif s.rows is not None:
            print(f"      результат: {s.rows}")
        elif s.status:
            print(f"      {s.status}")
        extra = []
        if s.blocked:
            extra.append(f"оператор чекав блокування й завершився після кроку {s.finished_after}")
        extra.append(f"транзакція: {s.txn}")
        if s.iso:
            extra.append(f"рівень: {s.iso}")
        print("      (" + "; ".join(extra) + ")")
    print("\nСтан таблиць після сценарію:")
    for table, rows in trace.final.items():
        print(f"  {table}: {rows}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
