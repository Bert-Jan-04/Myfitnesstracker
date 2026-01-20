-- Dit bestand maakt alle tabellen aan voor de app.
-- Door IF NOT EXISTS kan dit script veilig vaker worden uitgevoerd.


PRAGMA foreign_keys = ON; 
-- Bron: https://www.sqlite.org/foreignkeys.html

-- =========================================================
-- OEFENINGEN / WORKOUTS
-- =========================================================

-- Basis-oefeningen die je kunt kiezen in workouts
CREATE TABLE IF NOT EXISTS exercises ( -- https://www.sqlite.org/lang_createtable.html
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,          -- unieke naam zodat je geen dubbele oefeningen krijgt
  muscle_group TEXT NOT NULL,         -- bijv. "Borst", "Benen"
  equipment TEXT NOT NULL             -- bijv. "Barbell", "Dumbbell"
);

-- Activiteitsniveaus voor de caloriecalculator (TDEE multiplier)
CREATE TABLE IF NOT EXISTS activity_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,          -- bijv. "Licht actief"
  multiplier REAL NOT NULL            -- bijv. 1.55
);

-- Doelen voor de caloriecalculator (kcal + of -)
CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,          -- bijv. "Afvallen"
  kcal_adjustment INTEGER NOT NULL    -- bijv. -300 of +300
);

-- Users (login)
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Een workout is van 1 gebruiker, met datum + type + notities
CREATE TABLE IF NOT EXISTS workouts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  workout_date TEXT NOT NULL,         -- opgeslagen als "YYYY-MM-DD"
  workout_type TEXT NOT NULL,         -- bijv. "Kracht", "Cardio"
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  -- ON DELETE CASCADE: als user weg is, verwijderen we automatisch de workouts mee
);

-- Koppeltabel: welke oefeningen zitten in welke workout (+ sets/reps/weight)
CREATE TABLE IF NOT EXISTS workout_exercises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workout_id INTEGER NOT NULL,
  exercise_id INTEGER NOT NULL,
  sets INTEGER NOT NULL,
  reps INTEGER NOT NULL,
  weight REAL,                        -- mag NULL (optioneel)
  FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
  FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,

  -- Hiermee voorkom je 2x exact dezelfde oefening binnen dezelfde workout
  -- (Let op: als je dezelfde oefening 2x wil kunnen toevoegen met andere sets,
  -- dan moet deze UNIQUE eruit of je voegt een extra kolom toe zoals "order" of "variant")
  UNIQUE (workout_id, exercise_id)
);

-- Gewicht logs per gebruiker
CREATE TABLE IF NOT EXISTS weight_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  log_date TEXT NOT NULL,             -- "YYYY-MM-DD"
  weight REAL NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================================
-- VOEDING
-- =========================================================

-- Optioneel: cache van producten uit de API (waardes per 100g)
-- Voordeel: minder API calls + 1 bron van voedingswaarden
CREATE TABLE IF NOT EXISTS foods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_source TEXT NOT NULL,           -- bijv. "openfoodfacts"
  api_id TEXT NOT NULL,               -- bijv. barcode
  name TEXT NOT NULL,

  kcal_per_100 REAL,
  protein_per_100 REAL,
  carbs_per_100 REAL,
  fat_per_100 REAL,

  created_at TEXT DEFAULT CURRENT_TIMESTAMP,

  -- voorkomt dubbele producten uit dezelfde bron
  UNIQUE(api_source, api_id)
);

-- Wat de gebruiker daadwerkelijk eet (snapshot + berekende waarden)
-- Dit is expres "los" van foods: zo blijft je log correct, ook als product later verandert.
CREATE TABLE IF NOT EXISTS food_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  log_date TEXT NOT NULL,             -- "YYYY-MM-DD"

  food_id INTEGER,                    -- kan NULL (als je geen cache gebruikt)
  food_name TEXT NOT NULL,            -- snapshot van naam op moment van loggen
  amount_grams REAL NOT NULL,

  -- berekende waarden voor deze hoeveelheid (dus niet per 100g)
  kcal REAL NOT NULL,
  protein REAL NOT NULL,
  carbs REAL NOT NULL,
  fat REAL NOT NULL,

  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
  -- ON DELETE SET NULL: als een food uit cache wordt verwijderd, blijft de log bestaan
);

-- Dagdoel per gebruiker (minimaal kcal, macro's optioneel)
-- user_id is PRIMARY KEY: 1 record per gebruiker
CREATE TABLE IF NOT EXISTS daily_targets (
  user_id INTEGER PRIMARY KEY,
  kcal_target REAL NOT NULL,
  protein_target REAL,
  carbs_target REAL,
  fat_target REAL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================================
-- CALORIE CALCULATOR (profiel per gebruiker)
-- =========================================================

-- Profiel is 1 record per gebruiker (om BMR/TDEE te berekenen)
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id INTEGER PRIMARY KEY,
  sex TEXT NOT NULL CHECK (sex IN ('male', 'female')),
  birth_year INTEGER NOT NULL,
  height_cm REAL NOT NULL,
  activity_level_id INTEGER NOT NULL,
  goal_id INTEGER NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

  -- RESTRICT: je kunt een activiteit/doel niet verwijderen als iemand het nog gebruikt
  FOREIGN KEY (activity_level_id) REFERENCES activity_levels(id) ON DELETE RESTRICT,
  FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE RESTRICT
);

-- =========================================================
-- INDEXES (sneller zoeken/filteren)
-- =========================================================
-- Indexes maken zoeken/filteren sneller (handig bij dashboards en overzichten).
-- Bron: https://www.sqlite.org/lang_createindex.html

-- Sneller “workouts per user op datum”
CREATE INDEX IF NOT EXISTS idx_workouts_user_date
ON workouts(user_id, workout_date);

-- Sneller oefeningen ophalen voor 1 workout
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout
ON workout_exercises(workout_id);

-- Sneller gewicht trends per user per datum
CREATE INDEX IF NOT EXISTS idx_weight_logs_user_date
ON weight_logs(user_id, log_date);

-- Voeding: sneller dagoverzichten per user
CREATE INDEX IF NOT EXISTS idx_food_logs_user_date
ON food_logs(user_id, log_date);

-- Sneller product cache lookup (api_source + api_id)
CREATE INDEX IF NOT EXISTS idx_foods_source_id
ON foods(api_source, api_id);

