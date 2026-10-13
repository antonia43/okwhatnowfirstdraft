"""Database connection layer.

Uses Neon Postgres when DATABASE_URL is set (env var or Streamlit secret),
otherwise falls back to a local SQLite file so the app still runs on a laptop.
The rest of the code keeps writing SQL with ? placeholders; this layer translates.
"""
import os
import sqlite3
import tempfile
from pathlib import Path

DB_PATH = Path(tempfile.gettempdir()) / "career_corner.db"

try:
    import psycopg
    _PG_ERRORS = (psycopg.errors.IntegrityError,)
except ImportError:
    psycopg = None
    _PG_ERRORS = ()

# use in: except IntegrityError:
IntegrityError = (sqlite3.IntegrityError,) + _PG_ERRORS


def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    return url or None


def is_postgres():
    return bool(get_database_url()) and psycopg is not None


def _translate(sql):
    return (
        sql.replace("?", "%s")
        .replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    )


class _Cursor:
    def __init__(self, cur, pg):
        self._cur = cur
        self._pg = pg

    def execute(self, sql, params=()):
        if self._pg:
            sql = _translate(sql)
        self._cur.execute(sql, params)
        return self

    def __iter__(self):
        return iter(self._cur)

    def __getattr__(self, name):
        return getattr(self._cur, name)


class _Connection:
    def __init__(self, raw, pg):
        self._raw = raw
        self._pg = pg

    def cursor(self):
        return _Cursor(self._raw.cursor(), self._pg)

    def execute(self, sql, params=()):
        return self.cursor().execute(sql, params)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        return False


def connect():
    """Return a connection (Neon Postgres if configured, else local SQLite)."""
    if is_postgres():
        raw = psycopg.connect(get_database_url(), prepare_threshold=None)
        return _Connection(raw, True)
    raw = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _Connection(raw, False)
