from flask import Blueprint, render_template, request, session, redirect, url_for, flash

# login_required zorgt ervoor dat alleen ingelogde gebruikers
# hun gewicht kunnen bekijken en opslaan
from auth import login_required
from db import get_db_connection

bp = Blueprint("weight", __name__)


@bp.route("/weight", methods=["GET", "POST"])
@login_required
def weight():
	# Ingelogde gebruiker ophalen uit de sessie
    user_id = session["user_id"]

    if request.method == "POST":
		 # Formuliergegevens ophalen
        log_date = request.form.get("log_date", "").strip()
        weight_val = request.form.get("weight", "").strip()

# Simpele validatie: beide velden zijn verplicht
        if not log_date or not weight_val:
            flash("Vul datum en gewicht in.")
            return redirect(url_for("weight.weight"))
# Gewicht omzetten naar float zodat we ermee kunnen rekenen
        try:
            weight_float = float(weight_val)
        except ValueError:
            flash("Gewicht moet een getal zijn (bijv. 82.4).")
            return redirect(url_for("weight.weight"))

# Gewicht opslaan in de database
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO weight_logs (user_id, log_date, weight) VALUES (?, ?, ?)",
            (user_id, log_date, weight_float),
        )
        conn.commit()
        conn.close()

 # Feedback aan de gebruiker
 # Bron: https://flask.palletsprojects.com/en/stable/patterns/flashing/
        flash("Gewicht opgeslagen!")
        return redirect(url_for("weight.weight"))

    conn = get_db_connection()
    logs = conn.execute(
        "SELECT log_date, weight "
        "FROM weight_logs "
        "WHERE user_id = ? "
        "ORDER BY log_date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    
# Logs tonen in het template
    return render_template("weight.html", logs=logs)
