from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth import login_required

# Client voor externe recepten via TheMealDB API.
# https://rapidapi.com/thecocktaildb/api/themealdb/playground/apiendpoint_e6fe139e-587b-46f8-b3d8-589816e1fdbe
from services.mealdb_client import MealDBClient

bp = Blueprint("recipes", __name__)


@bp.route("/recipes", methods=["GET"])
@login_required
def recipes():
    """Lijstpagina: zoek op naam (q) of fallback op eerste letter (f)."""
    client = MealDBClient()

# request.args = query parameters uit de URL
# Bron: https://www.geeksforgeeks.org/python/using-request-args-for-a-variable-url-in-flask/
    q = request.args.get("q", "").strip()
    first_letter = request.args.get("f", "").strip().lower()

    meals = []
    title = "Recepten"

    try:
        if q:
			# Zoeken op naam
            meals = client.search_by_name(q)
            title = f"Recepten voor: {q}"
        else:
            # Geen zoekterm? Dan zoeken op eerste letter (fallback)
            if not first_letter:
                first_letter = "a"
            meals = client.search_by_first_letter(first_letter)
            title = f"Recepten (letter: {first_letter})"
    except Exception:
		# Als de API faalt, blijft de pagina werken en tonen we een melding
        flash("Kon recepten niet ophalen. Probeer het later nog eens.")
        meals = []

    return render_template(
        "recipes.html",
        meals=meals,
        title=title,
        q=q,
        f=first_letter,
    )


@bp.route("/recipes/<meal_id>", methods=["GET"])
@login_required
def recipe_detail(meal_id):
    """Detailpagina: haalt 1 recept op via id."""
    client = MealDBClient()

    meal = None
    try:
        meal = client.lookup_by_id(meal_id)
    except Exception:
        meal = None

    if not meal:
        flash("Recept niet gevonden.")
        return redirect(url_for("recipes.recipes"))

    # q meenemen zodat je 'terug' netjes naar dezelfde zoekopdracht kan
    q = request.args.get("q", "").strip()

    return render_template("recipe_detail.html", meal=meal, q=q)
