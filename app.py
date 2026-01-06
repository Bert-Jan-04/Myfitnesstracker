cat << 'EOF' > app.py
from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SEED_PATH = os.path.join(BASE_DIR, "data", "seed.sql")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Maakt database.db aan en vult 'm met vaste data via data/seed.sql.
    Dit is nodig op Render, omdat database.db niet in GitHub staat.
    """
    if not os.path.exists(SEED_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# 1x bij opstarten uitvoeren
init_db()


@app.route("/")
def home():
    conn = get_db_connection()
    exercises = conn.execute("SELECT id, name FROM exercises ORDER BY name").fetchall()
    conn.close()
    return render_template("fitnesstracker.html", exercises=exercises)


if __name__ == "__main__":
    app.run(debug=True)
EOF
