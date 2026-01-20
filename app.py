# os wordt gebruikt om omgevingsvariabelen (environment variables) uit te lezen.
# Dit is handig voor gevoelige gegevens zoals een SECRET_KEY,
# zodat deze niet hard in de code hoeft te staan.
# Bron: https://www.digitalocean.com/community/tutorials/python-os-module

import os
from flask import Flask

from db import init_db
# Hier importeer ik de blueprints (bp) uit verschillende route-bestanden.
# Een blueprint is een manier om routes te groeperen per onderdeel van de app,
# bijvoorbeeld dashboard, workouts of authenticatie.
# Dit maakt de code overzichtelijker en beter onderhoudbaar.
# Bron: https://flask.palletsprojects.com/en/stable/tutorial/views/

from routes.dashboard import bp as dashboard_bp
from routes.nutrition import bp as nutrition_bp
from routes.calculator import bp as calculator_bp
from routes.weight import bp as weight_bp
from routes.workouts import bp as workouts_bp
from routes.recipes import bp as recipes_bp
from routes.auth_routes import bp as auth_bp

# Aanmaken van de Flask-app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bert-jan-key-2026")

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# 1x uitvoeren bij opstarten
init_db()

# Blueprints registreren
app.register_blueprint(dashboard_bp)
app.register_blueprint(nutrition_bp)
app.register_blueprint(calculator_bp)
app.register_blueprint(weight_bp)
app.register_blueprint(workouts_bp)
app.register_blueprint(recipes_bp)
app.register_blueprint(auth_bp)

# Dit zorgt ervoor dat de Flask-server alleen start
# wanneer dit bestand direct wordt uitgevoerd.
# De debug-modus helpt tijdens ontwikkelen door foutmeldingen te tonen.
if __name__ == "__main__":
    app.run(debug=True)
