import sqlite3
# Blueprint wordt gebruikt om login- en registratie-routes
# te groeperen in een apart bestand.
# Bron: https://www.geeksforgeeks.org/python/flask-blueprints/
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

# Werkzeug wordt gebruikt voor veilig opslaan en controleren van wachtwoorden.
# Wachtwoorden worden gehasht en nooit als platte tekst opgeslagen.
# Bron: https://werkzeug.palletsprojects.com/en/stable/tutorial/
from werkzeug.security import generate_password_hash, check_password_hash

# Database helper voor het maken van een database-verbinding
from db import get_db_connection

# Aanmaken van een blueprint voor authenticatie
bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    # Als je al ingelogd bent, ga je naar dashboard
    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
		# Formuliergegevens ophalen
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Simpele validatie: lege velden niet toestaan
        if not email or not password:
            flash("Vul e-mail en wachtwoord in.")
            return redirect(url_for("auth.register"))

# Minimale wachtwoordlengte
        if len(password) < 8:
            flash("Wachtwoord moet minimaal 8 tekens zijn.")
            return redirect(url_for("auth.register"))

# Wachtwoord wordt veilig gehasht voordat het wordt opgeslagen
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
			# Nieuwe gebruiker opslaan in de database
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # UNIQUE email -> bestaat al
            conn.close()
            flash("Dit e-mailadres bestaat al. Probeer in te loggen.")
            return redirect(url_for("auth.login"))

        # Nieuwe user ophalen voor sessie
        user = conn.execute(
            "SELECT id, email FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

# Nieuwe sessie starten
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        flash("Account aangemaakt. Je bent nu ingelogd!")
        return redirect(url_for("dashboard.home"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Als je al ingelogd bent, ga je naar dashboard
    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
		 # Ingevoerde gegevens ophalen
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        
        # Gebruiker zoeken op e-mailadres
        user = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

# Controle of gebruiker bestaat en wachtwoord klopt
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Onjuiste inloggegevens.")
            return redirect(url_for("auth.login"))

# Login succesvol: sessie starten
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        flash("Je bent ingelogd.")
        return redirect(url_for("dashboard.home"))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Je bent uitgelogd.")
    return redirect(url_for("auth.login"))
