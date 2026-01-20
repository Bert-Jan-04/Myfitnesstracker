import sqlite3
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from auth import login_required
from db import get_db_connection

bp = Blueprint("workouts", __name__)


@bp.route("/workouts", methods=["GET", "POST"])
@login_required
def workouts():
	# Ingelogde gebruiker ophalen
    user_id = session["user_id"]

    if request.method == "POST":
		# Formuliergegevens ophalen
        workout_date = request.form.get("workout_date", "").strip()
        workout_type = request.form.get("workout_type", "").strip()
        notes = request.form.get("notes", "").strip()

# Simpele validatie: datum en type zijn verplicht
        if not workout_date or not workout_type:
            flash("Vul datum en type workout in.")
            return redirect(url_for("workouts.workouts"))

# Workout opslaan in de database
        conn = get_db_connection()
        cur = conn.execute(
            "INSERT INTO workouts (user_id, workout_date, workout_type, notes) "
            "VALUES (?, ?, ?, ?)",
            (user_id, workout_date, workout_type, notes),
        )
        conn.commit()
        workout_id = cur.lastrowid
        conn.close()

        flash("Workout aangemaakt! Voeg nu oefeningen toe.")
        return redirect(url_for("workouts.workout_detail", workout_id=workout_id))

    conn = get_db_connection()
    recent = conn.execute(
        "SELECT id, workout_date, workout_type, notes "
        "FROM workouts "
        "WHERE user_id = ? "
        "ORDER BY workout_date DESC "
        "LIMIT 20",
        (user_id,),
    ).fetchall()
    conn.close()

    return render_template("workouts.html", recent=recent)


@bp.route("/workouts/<int:workout_id>")
@login_required
def workout_detail(workout_id):
    user_id = session["user_id"]
    conn = get_db_connection()

# Workout ophalen en checken of deze bij de user hoort
    workout = conn.execute(
        "SELECT id, workout_date, workout_type, notes "
        "FROM workouts "
        "WHERE id = ? AND user_id = ?",
        (workout_id, user_id),
    ).fetchone()

    if workout is None:
        conn.close()
        flash("Workout niet gevonden.")
        return redirect(url_for("workouts.workouts"))

 # Alle oefeningen ophalen voor de dropdown / zoekfunctie
    exercises = conn.execute(
        "SELECT id, name FROM exercises ORDER BY name"
    ).fetchall()

# Oefeningen die al aan deze workout gekoppeld zijn (koppeltabel + JOIN)
    items = conn.execute(
        "SELECT we.id, e.name, we.sets, we.reps, we.weight "
        "FROM workout_exercises we "
        "JOIN exercises e ON e.id = we.exercise_id "
        "WHERE we.workout_id = ? "
        "ORDER BY we.id ASC",
        (workout_id,),
    ).fetchall()

    conn.close()
    return render_template(
        "workout_detail.html",
        workout=workout,
        exercises=exercises,
        items=items,
    )


@bp.route("/workouts/<int:workout_id>/add-exercise", methods=["POST"])
@login_required
def workout_add_exercise(workout_id):
    user_id = session["user_id"]

# Formuliergegevens ophalen
    exercise_id = request.form.get("exercise_id", "").strip()
    sets_val = request.form.get("sets", "").strip()
    reps_val = request.form.get("reps", "").strip()
    weight_val = request.form.get("weight", "").strip()

# Validatie: oefening, sets en reps zijn verplicht
    if not exercise_id or not sets_val or not reps_val:
        flash("Kies een oefening en vul sets + reps in.")
        return redirect(url_for("workouts.workout_detail", workout_id=workout_id))

 # Omzetten naar getallen (anders kan het niet in de database)
    try:
        sets_int = int(sets_val)
        reps_int = int(reps_val)
        weight_float = float(weight_val) if weight_val else None
    except ValueError:
        flash("Sets/reps moeten hele getallen zijn, gewicht een getal.")
        return redirect(url_for("workouts.workout_detail", workout_id=workout_id))

    conn = get_db_connection()

# Extra check: hoort deze workout wel bij deze user?
    ok = conn.execute(
        "SELECT 1 FROM workouts WHERE id = ? AND user_id = ?",
        (workout_id, user_id),
    ).fetchone()

    if ok is None:
        conn.close()
        flash("Geen toegang tot deze workout.")
        return redirect(url_for("workouts.workouts"))

# Nieuwe oefening toevoegen aan koppeltabel workout_exercises
    try:
        conn.execute(
            "INSERT INTO workout_exercises (workout_id, exercise_id, sets, reps, weight) "
            "VALUES (?, ?, ?, ?, ?)",
            (workout_id, int(exercise_id), sets_int, reps_int, weight_float),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Dit gebeurt o.a. door UNIQUE(workout_id, exercise_id)
        flash("Deze oefening staat al in deze workout. Pas de bestaande aan of kies een andere.")
    finally:
        conn.close()

    return redirect(url_for("workouts.workout_detail", workout_id=workout_id))


@bp.route("/api/exercises")
@login_required
def api_exercises():
    q = request.args.get("q", "").strip()
    limit = 25

    conn = get_db_connection()

    if not q:
        rows = conn.execute(
            "SELECT id, name FROM exercises ORDER BY name LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        like = f"%{q}%"
        rows = conn.execute(
            "SELECT id, name FROM exercises WHERE name LIKE ? ORDER BY name LIMIT ?",
            (like, limit),
        ).fetchall()

    conn.close()
    # JSON response teruggeven
    return {"results": [{"id": r["id"], "name": r["name"]} for r in rows]}
