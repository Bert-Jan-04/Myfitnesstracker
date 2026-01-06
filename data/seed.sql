-- seed.sql
-- Vaste data voor jouw fitness app (SQLite)
-- Run: sqlite3 database.db < seed.sql

PRAGMA foreign_keys = ON;

-- =========================
-- 1) Tabellen (vaste data)
-- =========================

CREATE TABLE IF NOT EXISTS exercises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  muscle_group TEXT NOT NULL,
  equipment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  multiplier REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  kcal_adjustment INTEGER NOT NULL
);

-- =========================
-- 2) Activiteitsniveaus
-- =========================

INSERT OR IGNORE INTO activity_levels (name, multiplier) VALUES
('Sedentary', 1.2),
('Light', 1.375),
('Moderate', 1.55),
('Active', 1.725),
('Very active', 1.9);

-- =========================
-- 3) Doelen
-- =========================

INSERT OR IGNORE INTO goals (name, kcal_adjustment) VALUES
('Cut', -300),
('Maintain', 0),
('Bulk', 300);

-- =========================
-- 4) Oefeningen (Top 60)
-- =========================
-- Velden: name, muscle_group, equipment
-- muscle_group is vereenvoudigd (Chest/Back/Legs/Shoulders/Arms/Core)

INSERT OR IGNORE INTO exercises (name, muscle_group, equipment) VALUES
-- Chest (10)
('Barbell Bench Press', 'Chest', 'Barbell'),
('Dumbbell Bench Press', 'Chest', 'Dumbbell'),
('Incline Barbell Bench Press', 'Chest', 'Barbell'),
('Incline Dumbbell Bench Press', 'Chest', 'Dumbbell'),
('Decline Bench Press', 'Chest', 'Barbell'),
('Dumbbell Chest Fly', 'Chest', 'Dumbbell'),
('Cable Chest Fly', 'Chest', 'Cable'),
('Low Cable Crossover', 'Chest', 'Cable'),
('Push-up', 'Chest', 'Bodyweight'),
('Machine Chest Press', 'Chest', 'Machine'),

-- Back (10)
('Deadlift', 'Back', 'Barbell'),
('Lat Pulldown', 'Back', 'Machine'),
('Pull-up', 'Back', 'Bodyweight'),
('Chin-up', 'Back', 'Bodyweight'),
('Barbell Row', 'Back', 'Barbell'),
('One-Arm Dumbbell Row', 'Back', 'Dumbbell'),
('Seated Cable Row', 'Back', 'Cable'),
('T-Bar Row', 'Back', 'Machine'),
('Straight-Arm Pulldown', 'Back', 'Cable'),
('Face Pull', 'Back', 'Cable'),

-- Legs (10)
('Back Squat', 'Legs', 'Barbell'),
('Front Squat', 'Legs', 'Barbell'),
('Romanian Deadlift', 'Legs', 'Barbell'),
('Leg Press', 'Legs', 'Machine'),
('Walking Lunges', 'Legs', 'Dumbbell'),
('Bulgarian Split Squat', 'Legs', 'Dumbbell'),
('Leg Extension', 'Legs', 'Machine'),
('Leg Curl', 'Legs', 'Machine'),
('Standing Calf Raise', 'Legs', 'Machine'),
('Seated Calf Raise', 'Legs', 'Machine'),

-- Shoulders (10)
('Overhead Barbell Press', 'Shoulders', 'Barbell'),
('Dumbbell Shoulder Press', 'Shoulders', 'Dumbbell'),
('Arnold Press', 'Shoulders', 'Dumbbell'),
('Lateral Raise', 'Shoulders', 'Dumbbell'),
('Front Raise', 'Shoulders', 'Dumbbell'),
('Rear Delt Fly', 'Shoulders', 'Dumbbell'),
('Upright Row', 'Shoulders', 'Barbell'),
('Cable Lateral Raise', 'Shoulders', 'Cable'),
('Push Press', 'Shoulders', 'Barbell'),
('Seated Dumbbell Press', 'Shoulders', 'Dumbbell'),

-- Arms (10)
('Barbell Bicep Curl', 'Arms', 'Barbell'),
('Dumbbell Bicep Curl', 'Arms', 'Dumbbell'),
('Hammer Curl', 'Arms', 'Dumbbell'),
('Preacher Curl', 'Arms', 'Machine'),
('Tricep Pushdown', 'Arms', 'Cable'),
('Skull Crushers', 'Arms', 'Barbell'),
('Overhead Tricep Extension', 'Arms', 'Dumbbell'),
('Close-Grip Bench Press', 'Arms', 'Barbell'),
('Dips', 'Arms', 'Bodyweight'),
('Concentration Curl', 'Arms', 'Dumbbell'),

-- Core (10)
('Plank', 'Core', 'Bodyweight'),
('Hanging Leg Raise', 'Core', 'Bodyweight'),
('Crunch', 'Core', 'Bodyweight'),
('Cable Crunch', 'Core', 'Cable'),
('Russian Twist', 'Core', 'Bodyweight'),
('Ab Wheel Roll-out', 'Core', 'Bodyweight'),
('Sit-up', 'Core', 'Bodyweight'),
('Bicycle Crunch', 'Core', 'Bodyweight'),
('Side Plank', 'Core', 'Bodyweight'),
('Mountain Climbers', 'Core', 'Bodyweight');
