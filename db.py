import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

SCHEMA_PATH = os.path.join(BASE_DIR, "data", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "data", "seed.sql")


def _connect():
    """
    Maakt een SQLite connectie die beter werkt op Render.
    - timeout/busy_timeout: wacht bij lock i.p.v. direct crashen
    - WAL: betere read/write concurrency
    """
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def get_db_connection():
    """Gebruik deze in routes."""
    return _connect()


def _exercises_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM exercises").fetchone()
    return int(row["c"]) if row else 0


def seed_exercises_from_api(conn: sqlite3.Connection, max_total: int = 150, page_size: int = 50) -> int:
    if _exercises_count(conn) > 0:
        return 0

    from services.exercisedb_client import ExerciseDBClient

    client = ExerciseDBClient()
    inserted = 0
    offset = 0

    while inserted < max_total:
        batch = client.fetch_exercises_page(offset=offset, limit=page_size)
        if not batch:
            break

        for ex in batch:
            name = (ex.get("name") or "").strip()
            if not name:
                continue

            muscle_group = (ex.get("target") or ex.get("bodyPart") or "Unknown").strip()
            equipment = (ex.get("equipment") or "Unknown").strip()

            conn.execute(
                "INSERT OR IGNORE INTO exercises (name, muscle_group, equipment) VALUES (?, ?, ?)",
                (name.title(), muscle_group.title(), equipment.title()),
            )
            inserted += 1
            if inserted >= max_total:
                break

        offset += page_size

    return inserted


def init_db():
    if not os.path.exists(SCHEMA_PATH):
        return

    conn = _connect()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    # Seed oefeningen via API (alleen als leeg)
    try:
        inserted = seed_exercises_from_api(conn, max_total=150, page_size=50)
        if inserted > 0:
            print(f"ExerciseDB seed: {inserted} oefeningen toegevoegd aan exercises.")
        else:
            print("ExerciseDB seed: exercises was al gevuld (of niets toegevoegd).")
    except Exception as e:
        print("ExerciseDB seed mislukt:", e)

    conn.commit()
    conn.close()
