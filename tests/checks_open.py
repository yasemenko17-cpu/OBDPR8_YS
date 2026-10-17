"""Відкриті перевірки: по дві на кожну пару «задача + набір даних». Кожна приймає контекст і перевіряє спостережений результат сценарію."""
import re

from ctxutil import check, fail, first_step, item_qty, on_duty_ids, table_rows, find_id


def _update_b(x):
    upd = first_step(x, lambda s: s.sess == "B" and s.sql.lower().startswith("update") and s.err is None and s.rowcount == 1)
    check(x, upd is not None, "Сеанс B має виконати UPDATE, що змінює один рядок позиції.")
    return upd


def _end_of(x, sess, after):
    return first_step(x, lambda s: s.sess == sess and s.n > after and s.status in ("ROLLBACK", "COMMIT"))


def _reads_a(x, count):
    vals = [s for s in x.t.reads("A")]
    check(x, len(vals) >= count, f"Сеанс A має виконати щонайменше {count} читань (SELECT, що повертає одне значення), виконано {len(vals)}.")
    return vals


# --- задача 1 ---------------------------------------------------------------------------------------------
def t01_nodirty(x):
    c = x.c
    upd = _update_b(x)
    check(x, upd.txn == "INTRANS", "UPDATE сеансу B має виконуватися всередині відкритої транзакції (після BEGIN).")
    own = [s for s in x.t.reads("B") if s.n > upd.n]
    check(x, own and own[0].scalar() != c["q1"],
          "Після UPDATE сеанс B має прочитати власне нове значення: воно відрізняється від початкового " f"{c['q1']}.")
    end = _end_of(x, "B", upd.n)
    check(x, end is not None, "Сеанс B має завершити транзакцію (ROLLBACK) після читання сеансу A.")
    window = [s for s in x.t.reads("A") if upd.n < s.n < end.n]
    check(x, window, "Сеанс A має прочитати значення в той час, поки транзакція B ще відкрита й не зафіксована.")
    for s in window:
        check(x, s.scalar() != own[0].scalar() or own[0].scalar() == c["q1"],
              "Сеанс A побачив незафіксоване значення сеансу B: брудне читання. У PostgreSQL воно неможливе, перевірте кроки.")
        check(x, s.scalar() == c["q1"], f"Сеанс A прочитав {s.scalar()}, а очікувалось зафіксоване значення {c['q1']}.")


def t01_final(x):
    c = x.c
    upd = _update_b(x)
    end = _end_of(x, "B", upd.n)
    check(x, end is not None and end.status == "ROLLBACK", "Транзакцію B потрібно скасувати командою ROLLBACK, а не зафіксувати.")
    check(x, item_qty(x) == c["q1"], f"Після скасування B у таблиці має лишитися початкове значення {c['q1']}, а є {item_qty(x)}.")


# --- задача 2 ---------------------------------------------------------------------------------------------
def t02_nonrepeatable(x):
    c = x.c
    v = [s.scalar() for s in _reads_a(x, 4)]
    check(x, v[0] == c["q1"], f"Перше читання кількості в A має дати початкове значення {c['q1']}, отримано {v[0]}.")
    check(x, v[2] != v[0], "Друге читання кількості в тій самій транзакції A дало те саме значення: непідтверджуваного читання "
                           "немає. Чи зафіксував B зміну між читаннями?")
    check(x, v[2] == item_qty(x), "Друге читання має збігатися із зафіксованим значенням у таблиці.")


def t02_phantom(x):
    c = x.c
    v = [s.scalar() for s in _reads_a(x, 4)]
    check(x, v[1] == c["lcount0"], f"Перший підрахунок записів має дати {c['lcount0']}, отримано {v[1]}.")
    check(x, v[3] == v[1] + 1, f"Другий підрахунок має бути на 1 більшим ({v[1] + 1}): у A з'являється фантомний рядок; отримано {v[3]}.")


# --- задача 3 ---------------------------------------------------------------------------------------------
def _t03_reads(x):
    err = first_step(x, lambda s: s.err == "40001")
    check(x, err is not None, "Помилки 40001 у сценарії немає: сеанс A має змінити рядок, який після його знімка змінив і зафіксував B.")
    before = [s for s in x.t.reads("A") if s.n < err.n]
    check(x, len(before) >= 4, f"До помилки сеанс A має виконати чотири читання (кількість, число записів, ще раз кількість, ще раз число записів), виконано {len(before)}.")
    return err, [s.scalar() for s in before]


def t03_snapshot(x):
    err, v = _t03_reads(x)
    check(x, v[0] == v[2], f"Знімок має бути єдиним: перше читання {v[0]}, друге {v[2]}.")
    check(x, v[1] == v[3], f"Підрахунок у межах транзакції має бути стабільним: {v[1]} і {v[3]}.")
    check(x, item_qty(x) != v[0], "Сеанс B має зафіксувати зміну кількості між читаннями A (інакше знімок нічого не доводить).")
    check(x, len([r for r in table_rows(x, x.c["lt"]) if r[1] == 1]) > v[1], "Сеанс B має додати запис у таблицю журналу між читаннями A.")


def t03_serialization(x):
    err, _ = _t03_reads(x)
    check(x, err.sess == "A" and err.sql.lower().startswith("update"), "Помилку 40001 має отримати UPDATE сеансу A.")
    check(x, err.txn == "INERROR", "Після помилки транзакція A має перейти у стан «перервана»; далі потрібен ROLLBACK.")
    check(x, len(x.t.errors()) == 1, "У сценарії має бути рівно одна помилка (40001).")


# --- задача 4 ---------------------------------------------------------------------------------------------
def _t04_pair(x):
    com = [s for s in x.t.steps if s.status == "COMMIT"]
    check(x, len(com) == 2 and {s.sess for s in com} == {"A", "B"}, "Обидві транзакції (A і B) мають бути зафіксовані командою COMMIT.")
    return sorted(com, key=lambda s: s.n)


def t04_lost(x):
    c = x.c
    com = _t04_pair(x)
    last = com[1].sess
    d = {"A": c["dA"], "B": c["dB"]}
    final = item_qty(x)
    check(x, final != c["q1"] - c["dA"] - c["dB"],
          f"Підсумок {final} враховує обидва продажі: втрати оновлення немає. Запис має бути абсолютним значенням, обчисленим із прочитаного.")
    check(x, final == c["q1"] - d[last], f"Очікувався підсумок {c['q1'] - d[last]} (виграє запис того, хто зафіксувався останнім), у таблиці {final}.")


def t04_stale(x):
    c = x.c
    com = _t04_pair(x)
    ra, rb = x.t.reads("A"), x.t.reads("B")
    check(x, ra and rb, "Кожен сеанс має прочитати кількість перед зміною.")
    check(x, ra[0].scalar() == c["q1"] and rb[0].scalar() == c["q1"], f"Обидва мають прочитати початкове значення {c['q1']}.")
    check(x, ra[0].n < com[0].n and rb[0].n < com[0].n, "Обидва читання мають відбутися до першого COMMIT.")


# --- задача 5 ---------------------------------------------------------------------------------------------
def t05_blocked(x):
    com = [s for s in x.t.steps if s.status == "COMMIT"]
    lock_b = first_step(x, lambda s: s.sess == "B" and s.blocked)
    check(x, lock_b is not None, "Читання сеансу B із блокуванням не чекало: або воно не конфліктувало з A, або у кроці немає FOR UPDATE.")
    check(x, re.search(r"\bfor\s+update\b", lock_b.sql, re.I) is not None, "Очікування має виникнути на SELECT … FOR UPDATE.")
    a_commit = first_step(x, lambda s: s.sess == "A" and s.status == "COMMIT")
    check(x, a_commit is not None and lock_b.n < a_commit.n <= lock_b.finished_after,
          "B має завершити читання лише після COMMIT сеансу A.")


def t05_noloss(x):
    c = x.c
    check(x, item_qty(x) == c["q1"] - c["dA"] - c["dB"],
          f"Обидва продажі мають бути враховані: очікувалось {c['q1'] - c['dA'] - c['dB']}, у таблиці {item_qty(x)}.")


# --- задача 6 ---------------------------------------------------------------------------------------------
def t06_both(x):
    check(x, len(x.t.errors()) == 0, "На REPEATABLE READ помилок бути не повинно: обидва сеанси мають успішно зафіксуватися.")
    ups = [s for s in x.t.steps if s.sql.lower().startswith("update") and s.err is None and s.rowcount == 1]
    check(x, len(ups) == 2 and {s.sess for s in ups} == {"A", "B"}, "Кожен сеанс має змінити по одному рядку чергового.")
    check(x, len({find_id(s.sql) for s in ups}) == 2, "Сеанси мають змінювати РІЗНІ рядки, інакше це не write skew, а звичайний конфлікт.")
    check(x, len([s for s in x.t.steps if s.status == "COMMIT"]) == 2, "Обидва сеанси мають зафіксувати зміни.")


def t06_violated(x):
    check(x, on_duty_ids(x) == [], f"Правило «лишається хоч один» має бути порушене: на чергуванні {len(on_duty_ids(x))}, очікувалось 0.")


# --- задача 7 ---------------------------------------------------------------------------------------------
def t07_onefails(x):
    errs = x.t.errors()
    check(x, len(errs) == 1 and errs[0].err == "40001", "Рівно одна транзакція має отримати помилку серіалізації 40001.")
    failed = errs[0].sess
    other = "A" if failed == "B" else "B"
    check(x, any(s.sess == other and s.status == "COMMIT" for s in x.t.steps), f"Сеанс {other} має успішно зафіксуватися.")
    check(x, not any(s.sess == failed and s.status == "COMMIT" for s in x.t.steps), f"Сеанс {failed} не може зафіксуватися після 40001.")


def t07_invariant(x):
    check(x, len(on_duty_ids(x)) == 1, f"Правило має зберегтися: на чергуванні лишається 1, а їх {len(on_duty_ids(x))}.")


# --- задача 8 ---------------------------------------------------------------------------------------------
def t08_nowait(x):
    s = first_step(x, lambda st: st.sess == "B" and re.search(r"\bnowait\b", st.sql, re.I) is not None)
    check(x, s is not None, "Сеанс B має спробувати захопити рядок із NOWAIT.")
    check(x, not s.blocked, "NOWAIT не повинен чекати.")
    check(x, s.err == "55P03", f"NOWAIT на заблокованому рядку має дати помилку 55P03 (lock_not_available), отримано {s.err}.")


def t08_skip(x):
    pa = first_step(x, lambda st: st.sess == "A" and re.search(r"for\s+update", st.sql, re.I) and st.scalar() is not None)
    pb = first_step(x, lambda st: st.sess == "B" and re.search(r"skip\s+locked", st.sql, re.I) is not None)
    check(x, pa is not None, "Сеанс A має вибрати завдання через SELECT … FOR UPDATE.")
    check(x, pb is not None, "Сеанс B має вибрати завдання через FOR UPDATE SKIP LOCKED.")
    check(x, not pb.blocked and pb.err is None, "SKIP LOCKED не повинен ні чекати, ні давати помилку.")
    check(x, pb.scalar() is not None and pb.scalar() != pa.scalar(), "B має отримати інше завдання, ніж A (заблоковане пропущено).")


# --- задача 9 ---------------------------------------------------------------------------------------------
def t09_deadlock(x):
    errs = x.t.errors()
    check(x, len(errs) == 1 and errs[0].err == "40P01",
          "Рівно один сеанс має отримати помилку 40P01 (виявлено взаємне блокування); " f"помилки: {[e.err for e in errs]}.")


def t09_survivor(x):
    errs = x.t.errors()
    check(x, len(errs) == 1, "Потрібна рівно одна помилка (40P01).")
    victim = errs[0].sess
    other = "A" if victim == "B" else "B"
    com = [s for s in x.t.steps if s.sess == other and s.status == "COMMIT"]
    check(x, com, f"Сеанс {other} (не жертва) має успішно виконати COMMIT.")
    check(x, not any(s.sess == victim and s.status == "COMMIT" for s in x.t.steps), "Жертва deadlock не може зафіксуватися.")
    check(x, x.t.end_txn == {"A": "IDLE", "B": "IDLE"}, "Обидва сеанси мають завершити транзакції.")


# --- задача 10 --------------------------------------------------------------------------------------------
def _waiting(x):
    s = first_step(x, lambda st: st.blocked)
    check(x, s is not None, "Жоден оператор не чекав блокування: сеанс B має спробувати змінити рядок, який тримає A.")
    return s


def t10_diag(x):
    w = _waiting(x)
    pa, pb = x.t.pids["A"], x.t.pids["B"]
    hit = None
    for s in x.t.steps:
        if s.sess == "A" and s.rows and w.n < s.n <= w.finished_after:
            for row in s.rows:
                flat = []
                for cell in row:
                    flat += cell if isinstance(cell, list) else [cell]
                if pb in flat and pa in flat:
                    hit = s
    check(x, hit is not None, "Діагностичний запит має виконатися, поки B чекає, і показати разом номер процесу B (хто чекає) і номер процесу A (хто блокує).")


def t10_final(x):
    c = x.c
    check(x, item_qty(x) == c["q1"] - c["dA"] - c["dB"], f"Обидві зміни мають бути застосовані: очікувалось {c['q1'] - c['dA'] - c['dB']}, у таблиці {item_qty(x)}.")
