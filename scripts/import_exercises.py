# scripts/import_exercises.py
import sys
from pathlib import Path

# Zorg dat projectroot in PYTHONPATH zit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite3
from services.exercisedb_client import ExerciseDBClient

DB_PATH = Path(__file__).resolve().parents[1] / "database.db"


def ensure_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(exercises);")
    cols = {row[1] for row in cur.fetchall()}

    required = {"name", "muscle_group", "equipment"}
    missing = required - cols
    if missing:
        raise RuntimeError(
            f"Tabel exercises mist kolommen: {missing}"
        )


def upsert_exercise(conn, name, muscle_group, equipment):
    conn.execute(
        """
        INSERT OR IGNORE INTO exercises (name, muscle_group, equipment)
        VALUES (?, ?, ?)
        """,
        (name, muscle_group, equipment),
    )


def main():
    print("DB:", DB_PATH)
    client = ExerciseDBClient()

    conn = sqlite3.connect(DB_PATH)

    try:
        ensure_columns(conn)

        limit = 10
        offset = 0
        seen_ids = set()

        before = conn.execute(
            "SELECT COUNT(*) FROM exercises"
        ).fetchone()[0]

        while True:
            page = client.fetch_exercises_page(offset=offset, limit=limit)
            if not page:
                break

            first_id = page[0].get("id")
            if first_id in seen_ids:
                print("Zelfde pagina opnieuw ontvangen → stoppen")
                break
            seen_ids.add(first_id)

            for ex in page:
                name = ex.get("name", "").strip()
                equipment = ex.get("equipment", "").strip()
                muscle_group = ex.get("target", "").strip()

                if name:
                    upsert_exercise(conn, name, muscle_group, equipment)

            conn.commit()
            print(f"Offset {offset}: opgehaald {len(page)}")
            offset += limit

        after = conn.execute(
            "SELECT COUNT(*) FROM exercises"
        ).fetchone()[0]

        print(f"Klaar. Voor: {before} | Na: {after} | Nieuw: {after - before}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
