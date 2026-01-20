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


def init_db():
    """
    Maakt database + tabellen aan vanuit schema.sql
    en vult vaste data vanuit seed.sql.
    """
    if not os.path.exists(SCHEMA_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    conn.commit()
    conn.close()
