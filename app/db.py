import os
import sqlite3
from pathlib import Path

# Default DB file for local runs
DEFAULT_DB_PATH = "app.db"


def get_db_path() -> str:
    """
    Returns the SQLite DB path.
    - In CI/tests you can override with env var SQLITE_DB_PATH
    - Otherwise defaults to app.db in the repo root.
    """
    return os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)


def connect(db_path: str | None = None) -> sqlite3.Connection:
    """
    Create a SQLite connection.
    We set row_factory so rows behave like dicts (row["dish"]).
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """
    Initialize DB by executing app/init.sql.
    """
    conn = connect(db_path)
    try:
        base = Path(__file__).resolve().parent
        schema=(base/ "schema.sql").read_text(encoding="utf-8")
        seed=(base/ "seed.sql").read_text(encoding="utf-8")

        conn.executescript(schema)
        conn.executescript(seed)
        conn.commit()
    finally:
        conn.close()
