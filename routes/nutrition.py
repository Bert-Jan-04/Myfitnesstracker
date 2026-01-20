from datetime import date

from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from auth import login_required
from db import get_db_connection
from utils import safe_float, calc_from_100g

# Productinfo ophalen via barcode uit Open Food Facts (externe API).
# API docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
from services.openfoodfacts_client import get_product_by_barcode

bp = Blueprint("nutrition", __name__)


@bp.route("/nutrition/target", methods=["POST"])
@login_required
def set_kcal_target():
    """Slaat het kcal-doel op voor de ingelogde gebruiker."""
    user_id = session["user_id"]
    kcal_target = request.form.get("kcal_target", "").strip()

    # next_url wordt meegegeven via een hidden input.
    # Zo kan de gebruiker terug naar dezelfde pagina na opslaan.
    next_url = request.form.get("next")

    if not kcal_target:
        flash("Vul een kcal-doel in.")
        return redirect(next_url) if next_url else redirect(url_for("dashboard.home"))

# Invoer omzetten naar float (anders kan er niet gerekend worden)
    try:
        kcal_val = float(kcal_target)
    except ValueError:
        flash("Kcal-doel moet een getal zijn.")
        return redirect(next_url) if next_url else redirect(url_for("dashboard.home"))

# Simpele check op realistische waarden
    if kcal_val < 500 or kcal_val > 10000:
        flash("Kies een realistisch kcal-doel (tussen 500 en 10.000).")
        return redirect(next_url) if next_url else redirect(url_for("dashboard.home"))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO daily_targets (user_id, kcal_target)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
          kcal_target = excluded.kcal_target
        """,
        (user_id, kcal_val),
    )
    
    # Dit is een 'upsert': als het record al bestaat, wordt het bijgewerkt.
    # Bron (SQLite upsert): https://sqlite.org/lang_upsert.html
    conn.commit()
    conn.close()

# flash = korte melding voor de gebruiker (feedback in de UI)
    # Bron: https://flask.palletsprojects.com/en/stable/patterns/flashing/
    flash("Caloriedoel opgeslagen!")
    return redirect(next_url) if next_url else redirect(url_for("dashboard.home"))


@bp.route("/food/search", methods=["GET", "POST"])
@login_required
def food_search():
    """Zoek een product op barcode via Open Food Facts."""
    product = None
    error = None

    if request.method == "POST":
        barcode = request.form.get("barcode", "").strip()

# Barcode check: Open Food Facts werkt met numerieke barcodes
        if not barcode.isdigit():
            error = "Barcode moet alleen cijfers bevatten."
            # API call: product ophalen op barcode
        else:
            product = get_product_by_barcode(barcode)
            if product is None:
                error = "Product niet gevonden (of API tijdelijk niet bereikbaar)."

    return render_template(
        "food_search.html",
        product=product,
        error=error,
        today=date.today().isoformat(),
    )


@bp.route("/food/log", methods=["POST"])
@login_required
def food_log():
    """Slaat een eetmoment op (berekend op basis van per-100g waarden + gram-invoer)."""
    user_id = session["user_id"]

# Basisinfo uit het formulier (komt van de zoekpagina / API-resultaat)
    api_source = request.form.get("api_source", "openfoodfacts").strip()
    api_id = request.form.get("api_id", "").strip()
    name = request.form.get("name", "").strip()

# safe_float voorkomt crashes bij lege of ongeldige invoer
    grams = safe_float(request.form.get("grams", ""), default=0.0)
    log_date = request.form.get("log_date", "").strip() or date.today().isoformat()

    if not name:
        flash("Productnaam ontbreekt.")
        return redirect(url_for("nutrition.food_search"))

    if grams <= 0:
        flash("Vul een geldige hoeveelheid in (gram).")
        return redirect(url_for("nutrition.food_search"))

    # per 100g waarden (van API) -> omrekenen naar jouw grams
    kcal_100 = safe_float(request.form.get("kcal_per_100"), default=0.0)
    p_100 = safe_float(request.form.get("protein_per_100"), default=0.0)
    c_100 = safe_float(request.form.get("carbs_per_100"), default=0.0)
    f_100 = safe_float(request.form.get("fat_per_100"), default=0.0)

# calc_from_100g rekent per-100g waarden om naar de ingevoerde hoeveelheid
    kcal = calc_from_100g(kcal_100, grams)
    protein = calc_from_100g(p_100, grams)
    carbs = calc_from_100g(c_100, grams)
    fat = calc_from_100g(f_100, grams)

    conn = get_db_connection()

    # Optioneel: product cachen in foods (per 100g), zodat je het later kunt hergebruiken
    food_id = None
    if api_id:
        conn.execute(
            """
            INSERT INTO foods (api_source, api_id, name, kcal_per_100, protein_per_100, carbs_per_100, fat_per_100)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(api_source, api_id) DO UPDATE SET
              name=excluded.name,
              kcal_per_100=excluded.kcal_per_100,
              protein_per_100=excluded.protein_per_100,
              carbs_per_100=excluded.carbs_per_100,
              fat_per_100=excluded.fat_per_100
            """,
            (api_source, api_id, name, kcal_100, p_100, c_100, f_100),
        )

        row = conn.execute(
            "SELECT id FROM foods WHERE api_source = ? AND api_id = ?",
            (api_source, api_id),
        ).fetchone()
        if row:
            food_id = row["id"]

    # Dit is de echte logregel: snapshot + berekende macro’s voor die dag
    conn.execute(
        """
        INSERT INTO food_logs (user_id, log_date, food_id, food_name, amount_grams, kcal, protein, carbs, fat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, log_date, food_id, name, grams, kcal, protein, carbs, fat),
    )
    conn.commit()
    conn.close()

    flash("Voeding toegevoegd!")
    return redirect(url_for("nutrition.nutrition_day", day=log_date))


@bp.route("/nutrition/today")
@login_required
def nutrition_today():
    """Shortcut: redirect naar het dagoverzicht van vandaag."""
    return redirect(url_for("nutrition.nutrition_day", day=date.today().isoformat()))


@bp.route("/nutrition/<day>")
@login_required
def nutrition_day(day):
    """Dagoverzicht: alle logs + totalen + resterend t.o.v. kcal-doel."""
    user_id = session["user_id"]
    conn = get_db_connection()

# Alle logs van deze dag ophalen
    logs = conn.execute(
        """
        SELECT id, food_name, amount_grams, kcal, protein, carbs, fat, created_at
        FROM food_logs
        WHERE user_id = ? AND log_date = ?
        ORDER BY created_at DESC
        """,
        (user_id, day),
    ).fetchall()

# Totalen berekenen (COALESCE zorgt dat je 0 krijgt i.p.v. NULL)
    totals = conn.execute(
        """
        SELECT
          COALESCE(SUM(kcal), 0) AS kcal,
          COALESCE(SUM(protein), 0) AS protein,
          COALESCE(SUM(carbs), 0) AS carbs,
          COALESCE(SUM(fat), 0) AS fat
        FROM food_logs
        WHERE user_id = ? AND log_date = ?
        """,
        (user_id, day),
    ).fetchone()
# Bron (COALESCE): https://www.sqlitetutorial.net/sqlite-functions/sqlite-coalesce/

# Doelen ophalen
    target = conn.execute(
        """
        SELECT kcal_target, protein_target, carbs_target, fat_target
        FROM daily_targets
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    kcal_target = float(target["kcal_target"]) if target else 0.0
    remaining = round(kcal_target - float(totals["kcal"]), 2) if totals else kcal_target

    conn.close()

    return render_template(
        "nutrition_day.html",
        day=day,
        logs=logs,
        totals=totals,
        kcal_target=kcal_target,
        remaining=remaining,
    )


@bp.route("/food/log/<int:log_id>/delete", methods=["POST"])
@login_required
def food_log_delete(log_id):
    """Verwijdert 1 voedsel-log en gaat terug naar dezelfde dag."""
    user_id = session["user_id"]
    conn = get_db_connection()

# Eerst checken of deze log bij deze user hoort
    row = conn.execute(
        "SELECT log_date FROM food_logs WHERE id = ? AND user_id = ?",
        (log_id, user_id),
    ).fetchone()

    if row is None:
        conn.close()
        flash("Log niet gevonden.")
        return redirect(url_for("nutrition.nutrition_today"))

    log_date = row["log_date"]

    conn.execute(
        "DELETE FROM food_logs WHERE id = ? AND user_id = ?",
        (log_id, user_id),
    )
    conn.commit()
    conn.close()

    flash("Log verwijderd.")
    return redirect(url_for("nutrition.nutrition_day", day=log_date))
