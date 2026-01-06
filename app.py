from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    conn = get_db_connection()
    exercises = conn.execute(
        "SELECT id, name FROM exercises ORDER BY name"
    ).fetchall()
    conn.close()

    return render_template("fitnesstracker.html", exercises=exercises)

if __name__ == "__main__":
    app.run(debug=True)
