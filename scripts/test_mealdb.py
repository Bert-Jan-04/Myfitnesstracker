import sys
import os

# project root toevoegen aan python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.mealdb_client import MealDBClient


def main():
    client = MealDBClient()
    meals = client.search_by_first_letter("a")

    print(f"Gevonden recepten: {len(meals)}")
    for m in meals[:5]:
        print("-", m["strMeal"])


if __name__ == "__main__":
    main()
