# Datumberekeningen met datetime en timedelta
# Bron: https://docs.python.org/3/library/datetime.html
from datetime import date, timedelta

# Blueprint om dashboard-routes te groeperen, https://flask.palletsprojects.com/en/stable/quickstart/
from flask import Blueprint, render_template, session

# login_required zorgt ervoor dat alleen ingelogde gebruikers
# toegang hebben tot het dashboard
from auth import login_required
from db import get_db_connection

# Client voor het ophalen van recepten via een externe API (TheMealDB)
# API:https://rapidapi.com/thecocktaildb/api/themealdb/playground/apiendpoint_e6fe139e-587b-46f8-b3d8-589816e1fdbe
from services.mealdb_client import MealDBClient

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def home():
	# Ingelogde gebruiker ophalen
    user_id = session["user_id"]

    # Datums (ISO = "YYYY-MM-DD" -> handig voor SQLite)
    today = date.today()
    today_str = today.isoformat()

# Maandag van de huidige week (voor weekoverzichten)
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.isoformat()

    conn = get_db_connection()

    # Laatst geregistreerde gewicht (voor KPI)
    latest_weight = conn.execute(
        """
        SELECT weight, log_date
        FROM weight_logs
        WHERE user_id = ?
        ORDER BY log_date DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()

 # Laatste 30 gewichtmetingen (voor grafiek)
    weight_logs = conn.execute(
        """
        SELECT log_date, weight
        FROM weight_logs
        WHERE user_id = ?
        ORDER BY log_date DESC
        LIMIT 30
        """,
        (user_id,),
    ).fetchall()

    # Aantal workouts deze week
    workouts_this_week = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM workouts
        WHERE user_id = ? AND workout_date >= ?
        """,
        (user_id, monday_str),
    ).fetchone()["cnt"]

 # Meest recente workouts voor overzicht
    recent_workouts = conn.execute(
        """
        SELECT id, workout_date, workout_type, notes
        FROM workouts
        WHERE user_id = ?
        ORDER BY workout_date DESC
        LIMIT 5
        """,
        (user_id,),
    ).fetchall()

    # Voeding kcal vandaag + doel (voor KPI)
    totals_today = conn.execute(
    #https://www.sqlite.org/lang_aggfunc.html
        """
        SELECT COALESCE(SUM(kcal), 0) AS kcal
        FROM food_logs
        WHERE user_id = ? AND log_date = ?
        """,
        (user_id, today_str),
    ).fetchone()

 # Dagelijks calorie-doel ophalen
    target = conn.execute(
        "SELECT kcal_target FROM daily_targets WHERE user_id = ?",
        (user_id,),
    ).fetchone()

# KPI-berekeningen
    kcal_today = float(totals_today["kcal"]) if totals_today else 0.0
    kcal_target = float(target["kcal_target"]) if target else 0.0
    kcal_remaining = round(kcal_target - kcal_today, 2)

    # Recepten van de dag (extern via API)
    # Er worden 3 willekeurige recepten opgehaald via TheMealDB.
    # Er wordt gecontroleerd op dubbele recepten.
    recipes_of_day = []
    try:
        client = MealDBClient()
        seen = set()
        attempts = 0

        while len(recipes_of_day) < 3 and attempts < 10:
            attempts += 1
            m = client.random_meal()
            if not m:
                continue

            mid = m.get("idMeal")
            if not mid or mid in seen:
                continue

            seen.add(mid)
            recipes_of_day.append(m)
    except Exception:
		 # Als de API faalt, blijft het dashboard gewoon werken
        recipes_of_day = []

    conn.close()

 # Alle data wordt doorgegeven aan het dashboard-template
    return render_template(
        "dashboard.html",
        latest_weight=latest_weight,
        weight_logs=weight_logs,
        workouts_this_week=workouts_this_week,
        recent_workouts=recent_workouts,
        kcal_today=kcal_today,
        kcal_target=kcal_target,
        kcal_remaining=kcal_remaining,
        today=today_str,
        recipes_of_day=recipes_of_day,
    )
