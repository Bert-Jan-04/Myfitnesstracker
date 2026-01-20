import os
import sqlite3

# BASE_DIR bepaalt de map waarin dit bestand staat.
# Hierdoor werkt het project overal hetzelfde, ongeacht waar het wordt gestart.
# Bron (os paths): https://docs.python.org/3/library/os.path.html
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pad naar het databasebestand (SQLite)
DB_PATH = os.path.join(BASE_DIR, "database.db")

# Pad naar het SQL-bestand met de tabellen
SCHEMA_PATH = os.path.join(BASE_DIR, "data", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "data", "seed.sql")


def get_db_connection():
    """Maakt een verbinding met de SQLite-database.
    Deze functie wordt gebruikt wanneer de app data wil ophalen of opslaan."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Zet foreign keys aan zodat relaties tussen tabellen worden gecontroleerd
    # Bron: https://www.sqlite.org/foreignkeys.html
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _exercises_count(conn: sqlite3.Connection) -> int:
    """Hulpfunctie: telt hoeveel oefeningen er in de exercises tabel staan."""
    row = conn.execute("SELECT COUNT(*) AS c FROM exercises").fetchone()
    return int(row["c"]) if row else 0


def seed_exercises_from_api(conn: sqlite3.Connection, max_total: int = 150, page_size: int = 50) -> int:
    """
    Vult de tabel exercises met data uit ExerciseDB (RapidAPI),
    maar alleen als de tabel nu leeg is.

    Return: aantal (poging tot) ingevoegde oefeningen.
    """
    # Als er al oefeningen in zitten, niets doen
    if _exercises_count(conn) > 0:
        return 0

    # Import hier zodat init_db niet meteen crasht als je service file ooit stuk is
    from services.exercisedb_client import ExerciseDBClient

    client = ExerciseDBClient()

    inserted = 0
    offset = 0

    while inserted < max_total:
        batch = client.fetch_exercises_page(offset=offset, limit=page_size)

        if not batch:
            break

        for ex in batch:
            # Velden die ExerciseDB meestal teruggeeft:
            # name, bodyPart, target, equipment
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
    """
    Maakt database + tabellen aan vanuit schema.sql,
    vult vaste data vanuit seed.sql,
    en vult (eenmalig) de exercises tabel via ExerciseDB API als die leeg is.
    """
    if not os.path.exists(SCHEMA_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1) schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # 2) seed (lookup tabellen, evt basis data)
    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    # 3) oefeningen vullen vanuit API (alleen als exercises leeg is)
    try:
        inserted = seed_exercises_from_api(conn, max_total=150, page_size=50)
        if inserted > 0:
            print(f"ExerciseDB seed: {inserted} oefeningen toegevoegd aan exercises.")
        else:
            print("ExerciseDB seed: exercises tabel was al gevuld (of niets toegevoegd).")
    except Exception as e:
        # App blijft draaien, maar je ziet in Render logs wat er mis ging
        print("ExerciseDB seed mislukt:", e)

    conn.commit()
    conn.close()
