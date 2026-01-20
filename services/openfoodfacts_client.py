import requests


def get_product_by_barcode(barcode: str) -> dict | None:
    """
    Haalt productinformatie op via Open Food Facts op basis van een barcode.
    Geeft een dictionary terug met voedingswaarden per 100 gram,
    of None als het product niet gevonden wordt.
    """

    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    headers = {
        "User-Agent": "MyFitnessTracker (student project)"
    }

    try:
        # HTTP request naar de API
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        # Bij netwerkfouten of timeouts None teruggeven
        return None

    # status == 1 betekent dat het product is gevonden
    if data.get("status") != 1:
        return None

    product = data.get("product", {})
    nutriments = product.get("nutriments", {})

    # Alle velden ophalen die nodig zijn
    return {
        "barcode": barcode,
        "name": product.get("product_name")
                or product.get("product_name_nl")
                or product.get("product_name_en")
                or "Onbekend product",
        "kcal_100g": nutriments.get("energy-kcal_100g"),
        "fat_100g": nutriments.get("fat_100g"),
        "carbs_100g": nutriments.get("carbohydrates_100g"),
        "protein_100g": nutriments.get("proteins_100g"),
    }
