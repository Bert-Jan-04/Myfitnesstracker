# scripts/test_exercisedb.py
import sys
from pathlib import Path

# Zorg dat de projectroot (Myfitnesstracker) in het import-pad zit
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.exercisedb_client import ExerciseDBClient  # noqa: E402


def main():
    client = ExerciseDBClient()
    exercises = client.fetch_exercises_page(offset=0, limit=10)

    print(f"Aantal opgehaald: {len(exercises)}")
    print("Eerste oefening:")
    print(exercises[0])


if __name__ == "__main__":
    main()
