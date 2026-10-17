"""Двосеансовий симулятор транзакцій: виконує сценарій (упорядкований список кроків «сеанс, SQL») на PostgreSQL.

Порядок кроків детермінований і не залежить від швидкості машини:
* кожен сеанс (A або B) працює у власному з'єднанні й власному потоці;
* крок вважається завершеним, коли сервер повернув відповідь, АБО коли сеанс стоїть в очікуванні блокування
  (pg_stat_activity: wait_event_type = 'Lock'); у другому випадку сценарій іде далі, а відповідь заблокованого
  оператора надходить пізніше, коли інший сеанс зніме блокування;
* перед наступним кроком сеансу, який ще чекає, симулятор дочікується завершення його оператора;
* після кожного кроку симулятор дочікується, доки сеанси, яких блокування вже не тримає, завершать свої оператори.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import psycopg
from psycopg.pq import TransactionStatus

import pgutil

STEP_TIMEOUT = 8.0      # секунд на один крок
AWAIT_TIMEOUT = 5.0     # скільки чекати завершення оператора, що вже стоїть в очікуванні
POLL = 0.01
TXN_NAMES = {TransactionStatus.IDLE: "IDLE", TransactionStatus.INTRANS: "INTRANS",
             TransactionStatus.INERROR: "INERROR", TransactionStatus.ACTIVE: "ACTIVE",
             TransactionStatus.UNKNOWN: "UNKNOWN"}


class ScenarioError(Exception):
    """Сценарій неможливо виконати як задумано (зависання, неправильний формат кроків)."""


class Step:
    def __init__(self, number, sess, sql):
        self.n = number              # номер кроку, з 1
        self.sess = sess
        self.sql = sql
        self.rows = None             # рядки результату (список кортежів) або None
        self.status = None           # тег команди: 'SELECT 1', 'UPDATE 1', 'COMMIT', 'ROLLBACK', ...
        self.rowcount = None
        self.err = None              # SQLSTATE помилки або None
        self.errmsg = None
        self.blocked = False         # оператор чекав блокування, коли сценарій пішов далі
        self.finished_after = None   # номер кроку, після якого оператор завершився
        self.txn = None              # стан транзакції сеансу після оператора: IDLE / INTRANS / INERROR
        self.iso = None              # рівень ізоляції транзакції (SHOW transaction_isolation), якщо вона відкрита

    def scalar(self):
        if self.rows and len(self.rows) == 1 and len(self.rows[0]) == 1:
            return self.rows[0][0]
        return None

    def is_select(self):
        return self.sql.lstrip().lower().startswith(("select", "with", "table"))


class Trace:
    """Результат виконання сценарію: кроки, номери серверних процесів, стан таблиць після сценарію."""

    def __init__(self):
        self.steps = []
        self.pids = {}
        self.final = {}              # назва таблиці -> список рядків (відсортовано за першим стовпцем)
        self.end_txn = {}

    def of(self, sess):
        return [s for s in self.steps if s.sess == sess]

    def reads(self, sess):
        """Прості читання сеансу: SELECT, що завершився без помилки й повернув рівно одне значення."""
        return [s for s in self.of(sess) if s.is_select() and s.err is None and s.scalar() is not None]

    def errors(self):
        return [s for s in self.steps if s.err]

    def sig(self):
        """Підпис результатів для порівняння двох прогонів (без номерів процесів)."""
        def diag(step):  # системні подання на спільному сервері показують і чужі сеанси, тому їх результат не порівнюється
            return "pg_stat" in step.sql.lower() or "pg_locks" in step.sql.lower()
        return [(s.sess, s.sql, "diag" if diag(s) else s.status, "diag" if diag(s) else s.rows,
                 s.err, s.blocked, s.txn, s.iso) for s in self.steps], self.final

    def table(self, limit=14):
        """Короткий текстовий звіт про кроки для повідомлень про помилки."""
        lines = []
        for s in self.steps[:limit]:
            sql = " ".join(s.sql.split())
            sql = sql if len(sql) <= 62 else sql[:59] + "..."
            if s.err:
                res = f"ПОМИЛКА {s.err}"
            elif s.rows is not None and len(s.rows) <= 2:
                res = str(s.rows)
            elif s.status:
                res = s.status
            else:
                res = ""
            mark = " (чекав)" if s.blocked else ""
            lines.append(f"  {s.n:>2}. {s.sess}: {sql}  ->  {res}{mark}")
        if len(self.steps) > limit:
            lines.append(f"  ... ще кроків: {len(self.steps) - limit}")
        return "\n".join(lines)


def _execute(conn, step):
    """Виконується у потоці сеансу: оператор, потім службові запити про стан."""
    try:
        cur = conn.execute(step.sql)
        step.status = cur.statusmessage
        step.rowcount = cur.rowcount
        step.rows = [tuple(r) for r in cur.fetchall()] if cur.description else None
    except psycopg.Error as error:
        step.err = error.sqlstate or "XXXXX"
        step.errmsg = str(error).strip().splitlines()[0] if str(error).strip() else ""
    status = conn.info.transaction_status
    step.txn = TXN_NAMES.get(status, "UNKNOWN")
    if status == TransactionStatus.INTRANS:
        try:  # SHOW не бере знімка даних, тому не змінює поведінку REPEATABLE READ
            step.iso = conn.execute("SHOW transaction_isolation").fetchone()[0]
        except psycopg.Error:
            step.iso = None


class Session:
    def __init__(self, name, schema):
        self.name = name
        self.conn = pgutil.connect()
        self.conn.execute(f"SET search_path = {schema}")
        try:  # потрібні права суперкористувача; без них діє стандартне значення 1 с, сценарії теж працюють
            self.conn.execute("SET deadlock_timeout = '500ms'")
        except psycopg.Error:
            pass
        self.conn.execute("SET statement_timeout = '20s'")
        self.pid = self.conn.info.backend_pid
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pending = None          # (Step, Future) оператора, що чекає блокування

    def close(self):
        try:
            self.conn.cancel()
        except Exception:  # noqa: BLE001
            pass
        self.pool.shutdown(wait=False, cancel_futures=True)
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass


def _check_steps(steps):
    if not isinstance(steps, (list, tuple)) or not steps:
        raise ScenarioError("scenario() має повертати непорожній список кроків [(\"A\", \"SQL\"), ...]")
    out = []
    for i, item in enumerate(steps, 1):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ScenarioError(f"Крок {i}: потрібна пара (сеанс, SQL), отримано {item!r}")
        sess, sql = item
        if sess not in ("A", "B"):
            raise ScenarioError(f"Крок {i}: сеанс має бути \"A\" або \"B\", отримано {sess!r}")
        if not isinstance(sql, str) or not sql.strip():
            raise ScenarioError(f"Крок {i}: SQL має бути непорожнім рядком")
        text = sql.strip()
        while text.endswith(";"):
            text = text[:-1].rstrip()
        import re
        if ";" in re.sub(r"'(?:[^']|'')*'", "''", text):
            raise ScenarioError(f"Крок {i}: один крок містить кілька команд; розбийте їх на окремі кроки")
        out.append((sess, text))
    return out


def run_scenario(schema, steps):
    """Виконує сценарій у схемі schema. Повертає Trace."""
    steps = _check_steps(steps)
    trace = Trace()
    sessions = {name: Session(name, schema) for name in ("A", "B")}
    monitor = pgutil.connect()
    trace.pids = {name: s.pid for name, s in sessions.items()}
    lock = threading.Lock()

    def waiting(pid):
        row = monitor.execute("SELECT wait_event_type, pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid = %s",
                              (pid,)).fetchone()
        return row is not None and row[0] == "Lock" and len(row[1]) > 0

    def finish(sess, number):
        step, fut = sess.pending
        fut.result()
        step.finished_after = number
        sess.pending = None

    def settle(number):
        """Дочекатися сеансів, яких уже ніхто не блокує: їхні оператори мають завершитися до наступного кроку."""
        deadline = time.time() + AWAIT_TIMEOUT
        while True:
            again = False
            for sess in sessions.values():
                if sess.pending is None:
                    continue
                if sess.pending[1].done():
                    finish(sess, number)
                elif not waiting(sess.pid):
                    again = True
            if not again:
                return
            if time.time() > deadline:
                return
            time.sleep(POLL)

    try:
        for number, (name, sql) in enumerate(steps, 1):
            sess = sessions[name]
            if sess.pending is not None:     # попередній оператор цього сеансу ще чекає
                deadline = time.time() + AWAIT_TIMEOUT
                while not sess.pending[1].done():
                    if time.time() > deadline:
                        raise ScenarioError(
                            f"Крок {number}: сеанс {name} ще чекає блокування від кроку {sess.pending[0].n}, а ви "
                            f"надсилаєте йому новий крок. Спершу інший сеанс має зняти блокування (COMMIT або ROLLBACK).")
                    time.sleep(POLL)
                finish(sess, number - 1)
            step = Step(number, name, sql)
            trace.steps.append(step)
            fut = sess.pool.submit(_execute, sess.conn, step)
            deadline = time.time() + STEP_TIMEOUT
            while True:
                if fut.done():
                    fut.result()
                    step.finished_after = number
                    break
                if waiting(sess.pid):
                    step.blocked = True
                    sess.pending = (step, fut)
                    break
                if time.time() > deadline:
                    raise ScenarioError(f"Крок {number}: сервер не відповідає понад {STEP_TIMEOUT:.0f} с")
                time.sleep(POLL)
            settle(number)
        deadline = time.time() + AWAIT_TIMEOUT
        for sess in sessions.values():
            if sess.pending is not None:
                while not sess.pending[1].done():
                    if time.time() > deadline:
                        raise ScenarioError(
                            f"Кінець сценарію: сеанс {sess.name} усе ще чекає блокування від кроку {sess.pending[0].n}. "
                            f"Завершіть транзакції (COMMIT або ROLLBACK) у тому порядку, щоб ніхто не лишився в очікуванні.")
                    time.sleep(POLL)
                finish(sess, len(steps))
        for name, sess in sessions.items():
            trace.end_txn[name] = TXN_NAMES.get(sess.conn.info.transaction_status, "UNKNOWN")
        tables = [r[0] for r in monitor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY 1", (schema,)).fetchall()]
        for table in tables:
            rows = monitor.execute(f'SELECT * FROM {schema}."{table}" ORDER BY 1').fetchall()
            trace.final[table] = [tuple(r) for r in rows]
    finally:
        for sess in sessions.values():
            sess.close()
        monitor.close()
    return trace
