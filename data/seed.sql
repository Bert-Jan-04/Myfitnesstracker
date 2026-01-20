-- seed.sql
-- Dit bestand vult de database met vaste startdata (lookup-tabellen).
-- Wordt veilig meerdere keren uitgevoerd door: INSERT OR IGNORE.

PRAGMA foreign_keys = ON;

-- =========================================================
-- 1) Activiteitsniveaus (voor caloriecalculator)
-- =========================================================
-- Deze waarden worden gebruikt om BMR → TDEE te berekenen.
-- multiplier = hoe actief iemand gemiddeld is.

-- https://www.sqlite.org/lang_conflict.html voor de INSERT OR IGNORE
INSERT OR IGNORE INTO activity_levels (name, multiplier) VALUES
('Sedentary', 1.2),        -- weinig beweging (bureauwerk, geen sport)
('Light', 1.375),          -- lichte beweging / paar keer per week sport
('Moderate', 1.55),        -- gemiddeld actief (3–5x per week)
('Active', 1.725),         -- veel sport / fysiek werk
('Very active', 1.9);      -- topsport / zware fysieke arbeid

-- =========================================================
-- 2) Doelen (calorie-aanpassing)
-- =========================================================
-- Deze waarden worden opgeteld bij of afgetrokken van TDEE.
-- Zo ontstaat het persoonlijke calorie-doel.

INSERT OR IGNORE INTO goals (name, kcal_adjustment) VALUES
('Cut', -300),             -- afvallen: calorie-tekort
('Maintain', 0),           -- gewicht behouden
('Bulk', 300);             -- aankomen: calorie-overschot

