def calc_from_100g(per_100: float | None, grams: float) -> float:
    """Rekent een voedingswaarde per 100 gram om
    naar de hoeveelheid die de gebruiker invoert.
    De uitkomst wordt afgerond op 2 decimalen."""
    if per_100 is None:
        return 0.0
    try:
        return round((float(per_100) * float(grams)) / 100.0, 2)
    except (TypeError, ValueError):
		# Als de invoer niet geldig is, wordt 0 teruggegeven
        return 0.0


def safe_float(val, default=0.0):
    """Zet een waarde veilig om naar float. Lukt het niet? Dan default."""
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age_years: int) -> float:
    """
    Mifflin-St Jeor formule: https://reference.medscape.com/calculator/846/mifflin-st-jeor-equation
    - Man:    10*w + 6.25*h - 5*a + 5
    - Vrouw:  10*w + 6.25*h - 5*a - 161
    """
    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age_years)
    if sex == "male":
        return base + 5.0
    return base - 161.0
