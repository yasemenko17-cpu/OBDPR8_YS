"""Допоміжні засоби тестів: підключення до PostgreSQL і тимчасова схема на кожен тест.

Параметри підключення беруться зі змінних середовища PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
(у Codespaces їх задає devcontainer; локально за замовчуванням localhost:5432, користувач postgres).
"""
import os
import uuid

import psycopg


def connect():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "postgres"),
        dbname=os.environ.get("PGDATABASE", "postgres"),
        autocommit=True,
        connect_timeout=5,
    )


class ScriptError(Exception):
    """SQL-скрипт студента завершився помилкою."""

    def __init__(self, error):
        self.state = error.sqlstate
        super().__init__(f"{error.sqlstate}: {str(error).strip().splitlines()[0]}")


class Db:
    """З'єднання з окремою тимчасовою схемою: усі таблиці тесту створюються лише в ній."""

    def __init__(self):
        self.conn = connect()
        self.schema = "t_" + uuid.uuid4().hex[:10]
        self.conn.execute(f"CREATE SCHEMA {self.schema}")
        self.conn.execute(f"SET search_path = {self.schema}")

    def close(self):
        try:
            self.conn.execute("SET search_path = public")
            self.conn.execute(f"DROP SCHEMA IF EXISTS {self.schema} CASCADE")
        finally:
            self.conn.close()

    def run(self, sql):
        """Виконує скрипт (кілька команд). Помилку перетворює на ScriptError."""
        try:
            self.conn.execute(sql)
        except psycopg.Error as error:
            raise ScriptError(error) from None

    def copy_in(self, command, text):
        """Виконує COPY ... FROM STDIN, передаючи вміст CSV-файла."""
        try:
            with self.conn.cursor() as cur:
                with cur.copy(command) as copy:
                    copy.write(text.encode("utf-8"))
        except psycopg.Error as error:
            raise ScriptError(error) from None

    def rows(self, sql, params=None):
        return self.conn.execute(sql, params).fetchall()

    def value(self, sql, params=None):
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None
