"""TP06 - monkeypatch : modifier temporairement l'environnement d'un test.

La fixture intégrée `monkeypatch` permet de remplacer attributs, variables
d'environnement, entrées de dictionnaire, répertoire courant, sys.path...
TOUTES les modifications sont annulées automatiquement à la fin du test.
"""

import os
import sys

import pytest

from tp06_monkeypatch import meteo

# ---------------------------------------------------------------------------
# 1. setenv / delenv : variables d'environnement
# ---------------------------------------------------------------------------


def test_cle_api_presente(monkeypatch):
    monkeypatch.setenv("METEO_API_KEY", "secret-de-test")
    assert meteo.cle_api() == "secret-de-test"


def test_cle_api_absente(monkeypatch):
    # raising=False : pas d'erreur si la variable n'existait pas déjà
    monkeypatch.delenv("METEO_API_KEY", raising=False)
    with pytest.raises(meteo.ConfigError, match="manquante"):
        meteo.cle_api()


def test_env_restaure():
    # Preuve que les tests précédents n'ont rien laissé traîner
    assert "METEO_API_KEY" not in os.environ or os.environ["METEO_API_KEY"] != "secret-de-test"


# ---------------------------------------------------------------------------
# 2. setattr : remplacer une fonction d'un module (couper le réseau)
# ---------------------------------------------------------------------------


def test_temperature_sans_reseau(monkeypatch):
    # Arranger le test pour qu'il ne fasse pas d'appel réseau réel
    def faux_appel(ville):
        assert ville == "Paris"
        return {"temp": 21.0, "ville": ville}

    # On remplace `appeler_api` LÀ OÙ ELLE EST UTILISÉE : dans le module meteo
    monkeypatch.setattr(meteo, "appeler_api", faux_appel)

    assert meteo.temperature("Paris") == 21.0


def test_setattr_par_chaine(monkeypatch):
    # Forme "module.attribut" en chaîne : évite d'importer le module
    monkeypatch.setattr("tp06_monkeypatch.meteo.appeler_api",
                        lambda ville: {"temp": -5.0})
    assert meteo.temperature("Oslo") == -5.0


def test_patcher_plus_bas_urlopen(monkeypatch):
    """On peut aussi patcher urllib lui-même, pour tester appeler_api()."""

    class FausseReponse:
        def __init__(self, corps: bytes):
            self._corps = corps

        def read(self):
            return self._corps

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    urls_appelees = []

    def faux_urlopen(url, timeout=None):
        urls_appelees.append((url, timeout))
        return FausseReponse(b'{"temp": 30.5}')

    monkeypatch.setenv("METEO_API_KEY", "k")
    monkeypatch.setattr(meteo.urllib.request, "urlopen", faux_urlopen)

    assert meteo.appeler_api("Lyon") == {"temp": 30.5}
    assert urls_appelees == [("https://api.meteo.example/v1/Lyon?key=k", 5)]


# ---------------------------------------------------------------------------
# 3. setattr sur une classe : remplacer une méthode
# ---------------------------------------------------------------------------


def test_methode_de_classe(monkeypatch):
    # Patch sur la CLASSE : toutes les instances sont affectées
    monkeypatch.setattr(meteo.Station, "lire_capteur", lambda self: 18.25)
    assert meteo.Station("Toit").rapport() == "Toit: 18.2°C"


def test_methode_d_instance(monkeypatch):
    station = meteo.Station("Cave")
    autre = meteo.Station("Grenier")

    # Patch sur UNE instance seulement
    monkeypatch.setattr(station, "lire_capteur", lambda: 12.0)
    assert station.rapport() == "Cave: 12.0°C"
    with pytest.raises(RuntimeError):
        autre.rapport()


# ---------------------------------------------------------------------------
# 4. setitem / delitem : dictionnaires (config globale)
# ---------------------------------------------------------------------------


def test_unite_fahrenheit(monkeypatch):
    monkeypatch.setattr(meteo, "appeler_api", lambda ville: {"temp": 100.0})
    monkeypatch.setitem(meteo.CONFIG, "unite", "fahrenheit")
    assert meteo.temperature("X") == 212.0


def test_config_restauree():
    assert meteo.CONFIG["unite"] == "celsius"


# ---------------------------------------------------------------------------
# 5. Contrôler le temps : time.time et datetime.now
# ---------------------------------------------------------------------------


def test_cache_expire(monkeypatch):
    appels = []
    monkeypatch.setattr(meteo, "appeler_api",
                        lambda ville: appels.append(ville) or {"temp": 1.0})
    monkeypatch.setattr(meteo, "_CACHE", {})  # cache neuf pour ce test

    horloge = {"t": 1_000.0}
    monkeypatch.setattr(meteo.time, "time", lambda: horloge["t"])

    meteo.temperature_en_cache("Nice")
    meteo.temperature_en_cache("Nice")  # < 60 s : servi par le cache
    assert appels == ["Nice"]

    horloge["t"] += 61  # on "avance" le temps
    meteo.temperature_en_cache("Nice")
    assert appels == ["Nice", "Nice"]


@pytest.mark.parametrize("heure, attendu", [(8, "Bonjour"), (17, "Bonjour"), (18, "Bonsoir"), (23, "Bonsoir")])
def test_salutation(monkeypatch, heure, attendu):
    # datetime.now est une méthode d'un type C : on ne peut pas la patcher
    # directement. On remplace la classe `datetime` VUE PAR le module meteo.
    class FauxDatetime:
        @classmethod
        def now(cls):
            from datetime import datetime

            return datetime(2024, 1, 1, heure, 0)

    monkeypatch.setattr(meteo, "datetime", FauxDatetime)
    assert meteo.salutation() == attendu


# ---------------------------------------------------------------------------
# 6. chdir : répertoire courant (combiné avec tmp_path)
# ---------------------------------------------------------------------------


def test_config_locale_absente(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # répertoire vide et jetable
    assert meteo.lire_config_locale() == {}


def test_config_locale_presente(monkeypatch, tmp_path):
    (tmp_path /
     "meteo.json").write_text('{"ville": "Brest"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert meteo.lire_config_locale() == {"ville": "Brest"}


# ---------------------------------------------------------------------------
# 7. syspath_prepend : rendre importable un module de test
# ---------------------------------------------------------------------------


def test_get_value():
    assert meteo.get_value() == 44


def test_syspath_prepend(monkeypatch, tmp_path):
    (tmp_path / "some_values.py").write_text("VALEUR = 42\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    import some_values  # type: ignore[import-not-found]

    assert some_values.VALEUR == 42
    # Nettoyage de sys.modules pour ne pas polluer les autres tests
    monkeypatch.delitem(sys.modules, "some_values")


# ---------------------------------------------------------------------------
# 8. monkeypatch.context() : annuler AVANT la fin du test
# ---------------------------------------------------------------------------


def test_context(monkeypatch):
    with monkeypatch.context() as m:
        m.setitem(meteo.CONFIG, "unite", "kelvin")
        assert meteo.CONFIG["unite"] == "kelvin"
    # Restauré dès la sortie du bloc `with`
    assert meteo.CONFIG["unite"] == "celsius"


# ---------------------------------------------------------------------------
# 9. Fixture réutilisable construite sur monkeypatch
# ---------------------------------------------------------------------------


@pytest.fixture
def api_factice(monkeypatch):
    """Coupe le réseau et permet de définir la réponse depuis le test."""
    reponses = {}
    monkeypatch.setattr(meteo, "appeler_api", lambda ville: reponses[ville])
    monkeypatch.setenv("METEO_API_KEY", "fixture")
    return reponses


def test_avec_fixture_api(api_factice):
    api_factice["Rome"] = {"temp": 28.0}
    assert meteo.temperature("Rome") == 28.0
