"""Задача 8. Черга завдань: NOWAIT і SKIP LOCKED.

Опис і умови: student.md, розділ «Опис задач», задача 8; картка вашого варіанта.
Відкриті тести: pytest -k "T08"
"""

# Впишіть номер свого варіанта (22-24).
VARIANT = 23


def scenario():
    return [
        # 1. Сеанс А відкриває транзакцію та заблоковує завдання 1
        ("A", "BEGIN"),
        ("A", "SELECT id FROM order_job WHERE state = 'new' ORDER BY id LIMIT 1 FOR UPDATE"),

        # 2. Сеанс В без BEGIN пробує взяти завдання через NOWAIT (отримує помилку 55P03, не чекає)
        ("B", "SELECT id FROM order_job WHERE state = 'new' ORDER BY id LIMIT 1 FOR UPDATE NOWAIT"),

        # 3. Сеанс В відкриває транзакцію та бере вільне завдання 2 через SKIP LOCKED
        ("B", "BEGIN"),
        ("B", "SELECT id FROM order_job WHERE state = 'new' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED"),

        # 4. Позначення виконаних завдань
        ("A", "UPDATE order_job SET state = 'done', handler = 'A' WHERE id = 1"),
        ("B", "UPDATE order_job SET state = 'done', handler = 'B' WHERE id = 2"),

        # 5. Завершення транзакцій
        ("A", "COMMIT"),
        ("B", "COMMIT"),
    ]
