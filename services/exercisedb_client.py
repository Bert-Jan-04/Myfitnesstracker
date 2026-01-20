# services/exercisedb_client.py
import os
import requests

BASE_URL = "https://exercisedb.p.rapidapi.com"


class ExerciseDBClient:
    def __init__(self):
		 # API key haal ik uit environment variables (veilig: niet hardcoded in de code)
		 # Bron: https://docs.python.org/3/library/os.html
        api_key = os.environ.get("RAPIDAPI_KEY")
        if not api_key:
			# Als de key ontbreekt, kan de app de API niet gebruiken
            raise RuntimeError("RAPIDAPI_KEY ontbreekt in je environment variables.")

        self.headers = {
    "x-rapidapi-key": api_key,
    "x-rapidapi-host": "exercisedb.p.rapidapi.com",
}


    def fetch_exercises_page(self, offset: int = 0, limit: int = 10) -> list[dict]:
        """
        Haalt 1 pagina op. (ExerciseDB gebruikt paginatie met offset/limit.)
        """
        url = f"{BASE_URL}/exercises"
        params = {"offset": offset, "limit": limit}
        
        # requests.get() maakt een HTTP request naar de API.
        # timeout zorgt dat de app niet eindeloos blijft wachten als de API traag is.
        # Bron: https://requests.readthedocs.io/en/master/user/advanced/
        r = requests.get(url, headers=self.headers, params=params, timeout=30)
        
        # raise_for_status() geeft een fout als de server een 4xx/5xx teruggeeft.
        # Hierdoor merk je meteen dat er iets mis is met de call.
        # Bron: https://3.python-requests.org/user/quickstart/
        r.raise_for_status()

# JSON response uitlezen (ExerciseDB geeft een lijst met oefeningen terug)
        data = r.json()
        
        # Extra check: als de API iets onverwachts teruggeeft, stop ik netjes met een fout.
        if not isinstance(data, list):
            raise RuntimeError(f"Onverwachte response: {data}")

        return data
