import json
import urllib.request

URL = "https://timeapi.io/api/time/current/zone?timeZone=Europe/Paris"


def saluer(nom: str) -> str:
    """Hello world qui adapte la formule à l'heure qu'il est à Paris."""
    with urllib.request.urlopen(URL, timeout=5) as reponse:
        data = json.load(reponse)
    heure = int(data["hour"])  # {"hour": 14, "minute": 32, "dateTime": "2026-09-08T14:32:07", ...}
    if heure < 12:
        formule = "Bonjour"
    elif heure < 18:
        formule = "Bon après-midi"
    else:
        formule = "Bonsoir"
    return f"{formule}, {nom} !"
