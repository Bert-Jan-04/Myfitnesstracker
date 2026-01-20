# wraps wordt gebruikt bij decorators.
# Het zorgt ervoor dat Flask de originele functie blijft herkennen.
# Zonder wraps kan dit problemen geven bij routing.
# Bron: https://stackoverflow.com/questions/308999/what-does-functools-wraps-do

from functools import wraps

# session: onthoudt of een gebruiker is ingelogd
# redirect: stuurt een gebruiker door naar een andere pagina
# url_for: maakt een link naar een andere route in de app
from flask import session, redirect, url_for


def login_required(view):
    """Zorgt dat een gebruiker ingelogd moet zijn om een pagina te openen."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
		# Check of de gebruiker is ingelogd
        if session.get("user_id") is None:
			# Zo niet, dan doorsturen naar de loginpagina
            return redirect(url_for("auth.login"))
            # Is de gebruiker wel ingelogd, dan mag de pagina worden geladen
        return view(*args, **kwargs)

    return wrapped_view

