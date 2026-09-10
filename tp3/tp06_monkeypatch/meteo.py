"""Code métier du TP06 : un client météo avec plein de dépendances externes.

Chaque dépendance (variable d'environnement, réseau, heure, cwd, config
globale) est un obstacle pour les tests : monkeypatch va les neutraliser.
"""

import json
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from tp06_monkeypatch import some_values


API_URL = "https://api.meteo.example/v1"

CONFIG = {"unite": "celsius", "timeout": 5}

_CACHE: dict[str, tuple[float, dict]] = {}
DUREE_CACHE = 60  # secondes


class ConfigError(Exception):
    pass


def get_value() -> int:
    return some_values.VALEUR


def cle_api() -> str:
    try:
        return os.environ["METEO_API_KEY"]
    except KeyError:
        raise ConfigError("METEO_API_KEY manquante") from None


def appeler_api(ville: str) -> dict:
    """Vrai appel réseau : à ne JAMAIS exécuter dans un test."""
    url = f"{API_URL}/{ville}?key={cle_api()}"
    with urllib.request.urlopen(url, timeout=CONFIG["timeout"]) as reponse:
        return json.loads(reponse.read())


def temperature(ville: str) -> float:
    donnees = appeler_api(ville)
    temp = donnees["temp"]
    if CONFIG["unite"] == "fahrenheit":
        return temp * 9 / 5 + 32
    return temp


def temperature_en_cache(ville: str) -> float:
    """Comme temperature(), mais mémorise le résultat DUREE_CACHE secondes."""
    maintenant = time.time()
    if ville in _CACHE:
        horodatage, donnees = _CACHE[ville]
        if maintenant - horodatage < DUREE_CACHE:
            return donnees["temp"]
    donnees = appeler_api(ville)
    _CACHE[ville] = (maintenant, donnees)
    return donnees["temp"]


def salutation() -> str:
    heure = datetime.now().hour
    return "Bonjour" if heure < 18 else "Bonsoir"


def lire_config_locale() -> dict:
    """Lit `meteo.json` dans le répertoire COURANT."""
    chemin = Path("meteo.json")
    if not chemin.exists():
        return {}
    return json.loads(chemin.read_text(encoding="utf-8"))


class Station:
    def __init__(self, nom: str):
        self.nom = nom

    def lire_capteur(self) -> float:
        raise RuntimeError("aucun capteur physique branché")

    def rapport(self) -> str:
        return f"{self.nom}: {self.lire_capteur():.1f}°C"
