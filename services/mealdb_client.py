import os
import requests


class MealDBClient:
	# Basis-URL van TheMealDB API via RapidAPI
    BASE_URL = "https://themealdb.p.rapidapi.com"

    def __init__(self):
		# API key ophalen uit environment variables.
        # Zo staat de sleutel niet hardcoded in de code.
        key = os.getenv("RAPIDAPI_KEY")
        if not key:
            # Duidelijke fout tijdens development
            raise RuntimeError(
                "RAPIDAPI_KEY ontbreekt. Zet hem in je environment "
                "(bijv. export RAPIDAPI_KEY=...)."
            )

        self.headers = {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "themealdb.p.rapidapi.com",
        }

    
    # Zoeken
    
    def search_by_first_letter(self, letter: str):
        """Zoek recepten op eerste letter (a-z)"""
        r = requests.get(
            f"{self.BASE_URL}/search.php",
            headers=self.headers,
            params={"f": letter.lower()},
            timeout=10, # voorkomt eindeloos wachten bij trage API, https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts
        )
        r.raise_for_status()
        data = r.json()
        return data.get("meals") or []

    def search_by_name(self, name: str):
        """Zoek recepten op naam"""
        r = requests.get(
            f"{self.BASE_URL}/search.php",
            headers=self.headers,
            params={"s": name},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("meals") or []

    
    # Detail
   
    def lookup_by_id(self, meal_id: str):
        """Haal 1 recept op via idMeal"""
        r = requests.get(
            f"{self.BASE_URL}/lookup.php",
            headers=self.headers,
            params={"i": str(meal_id)},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        meals = data.get("meals") or []
        return meals[0] if meals else None

   
    # Inspiratie (dashboard)
   
    def random_meal(self):
        """Haal 1 random recept op"""
        r = requests.get(
            f"{self.BASE_URL}/random.php",
            headers=self.headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        meals = data.get("meals") or []
        return meals[0] if meals else None
