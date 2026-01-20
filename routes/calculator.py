from datetime import date

# SimpleNamespace wordt gebruikt om meerdere waarden
# netjes te bundelen in één object (bijv. result.bmr).
# Dit maakt het doorgeven aan de template overzichtelijker.
# Bron: https://docs.python.org/3/library/types.html
from types import SimpleNamespace

# Blueprint om deze routes te groeperen binnen de calculator-functionaliteit
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

# login_required zorgt ervoor dat alleen ingelogde gebruikers
# deze pagina kunnen openen
from auth import login_required

# Database helper voor het ophalen en opslaan van gegevens
from db import get_db_connection

# Hulpfuncties voor veilige invoer en BMR-berekening
from utils import safe_float, mifflin_st_jeor

bp = Blueprint("calculator", __name__)


@bp.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():
	# Ingelogde gebruiker ophalen uit de sessie
    user_id = session["user_id"]
    conn = get_db_connection()

# Activiteitsniveaus ophalen voor de keuzelijst
    activity_levels = conn.execute(
        "SELECT id, name, multiplier FROM activity_levels ORDER BY id"
    ).fetchall()

# Doelen ophalen voor de keuzelijst
    goals = conn.execute(
        "SELECT id, name, kcal_adjustment FROM goals ORDER BY id"
    ).fetchall()

 # Bestaand profiel ophalen (als dat er is)
    profile = conn.execute(
        """
        SELECT user_id, sex, birth_year, height_cm, activity_level_id, goal_id
        FROM user_profiles
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

# Laatst bekende gewicht ophalen (voor gebruik als standaardwaarde)
    latest_weight_row = conn.execute(
        "SELECT weight FROM weight_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    weight_kg_default = float(latest_weight_row["weight"]) if latest_weight_row else None
    weight_kg_for_form = weight_kg_default

    result = None

    if request.method == "POST":
		# Ingevoerde waarden ophalen
        sex = request.form.get("sex", "").strip()

        # Veilig: voorkomt crash als birth_year leeg of niet-numeriek is
        birth_year = int(safe_float(request.form.get("birth_year"), default=0))

        height_cm = safe_float(request.form.get("height_cm"), default=0.0)
        weight_kg = safe_float(request.form.get("weight_kg"), default=0.0)

        activity_level_id = int(safe_float(request.form.get("activity_level_id"), default=0))
        goal_id = int(safe_float(request.form.get("goal_id"), default=0))

        weight_kg_for_form = weight_kg

# Leeftijd berekenen op basis van het huidige jaar
        current_year = date.today().year
        age_years = current_year - birth_year

        # ---- Validatie (simpel + duidelijk) ----
        if sex not in ("male", "female"):
            flash("Kies een geldig geslacht.")
            conn.close()
            return redirect(url_for("calculator.calculator"))

        if age_years < 10 or age_years > 100:
            flash("Geboortejaar lijkt niet te kloppen.")
            conn.close()
            return redirect(url_for("calculator.calculator"))

        if height_cm < 120 or height_cm > 230:
            flash("Lengte lijkt niet te kloppen.")
            conn.close()
            return redirect(url_for("calculator.calculator"))

        if weight_kg < 30 or weight_kg > 250:
            flash("Gewicht lijkt niet te kloppen.")
            conn.close()
            return redirect(url_for("calculator.calculator"))

 # Gekozen activiteit en doel ophalen uit de database
        activity = conn.execute(
            "SELECT multiplier FROM activity_levels WHERE id = ?",
            (activity_level_id,),
        ).fetchone()

        goal = conn.execute(
            "SELECT kcal_adjustment FROM goals WHERE id = ?",
            (goal_id,),
        ).fetchone()

        if activity is None or goal is None:
            flash("Kies een geldig activiteitsniveau en doel.")
            conn.close()
            return redirect(url_for("calculator.calculator"))

        multiplier = float(activity["multiplier"])
        kcal_adjustment = float(goal["kcal_adjustment"])

        # ---- Berekeningen ----
        bmr = mifflin_st_jeor(sex, weight_kg, height_cm, age_years)
        tdee = bmr * multiplier
        target_kcal = max(1200.0, tdee + kcal_adjustment)

        # ---- Profiel opslaan ----
        conn.execute(
            """
            INSERT INTO user_profiles (user_id, sex, birth_year, height_cm, activity_level_id, goal_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              sex=excluded.sex,
              birth_year=excluded.birth_year,
              height_cm=excluded.height_cm,
              activity_level_id=excluded.activity_level_id,
              goal_id=excluded.goal_id
            """,
            (user_id, sex, birth_year, height_cm, activity_level_id, goal_id),
        )
        conn.commit()

        # Resultaat voor template (werkt als result.bmr, result.tdee, result.target)
        result = SimpleNamespace(bmr=bmr, tdee=tdee, target=target_kcal)

        # Profiel opnieuw ophalen zodat select-boxes meteen “selected” staan
        profile = conn.execute(
            """
            SELECT user_id, sex, birth_year, height_cm, activity_level_id, goal_id
            FROM user_profiles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    conn.close()

# Template renderen met alle benodigde data
    return render_template(
        "calculator.html",
        activity_levels=activity_levels,
        goals=goals,
        profile=profile,
        weight_kg=weight_kg_for_form,
        result=result,
    )


@bp.route("/calculator/save", methods=["POST"])
@login_required
def calculator_save():
    user_id = session["user_id"]
     # Veilig uitlezen van het kcal-doel
    kcal_target = safe_float(request.form.get("kcal_target"), default=0.0)

    if kcal_target <= 0:
        flash("Kon kcal-doel niet opslaan.")
        return redirect(url_for("calculator.calculator"))

    conn = get_db_connection()
    
     # Kcal-doel opslaan of bijwerken
    conn.execute(
        """
        INSERT INTO daily_targets (user_id, kcal_target)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
          kcal_target=excluded.kcal_target
        """,
        (user_id, kcal_target),
    )
    conn.commit()
    conn.close()

    flash("Kcal-doel opgeslagen! Je dashboard en voeding-overzicht zijn nu bijgewerkt.")
    return redirect(url_for("dashboard.home"))
