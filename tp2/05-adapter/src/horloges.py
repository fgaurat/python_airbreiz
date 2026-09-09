import json
from datetime import datetime
from typing import Protocol
from urllib.request import urlopen


class Horloge(Protocol):
    """Ce dont le métier a besoin : l'heure courante, entre 0 et 23."""

    def heure(self) -> int: ...


class HeureIndisponible(RuntimeError):
    """La source d'heure n'a pas pu répondre correctement."""


class HorlogeSysteme:
    def heure(self) -> int:
        return datetime.now().hour


class HorlogeTimeApi:
    """Adapte l'API timeapi.io à l'interface Horloge.

    C'est le seul endroit qui connaît l'URL et le format JSON.
    """

    URL = "https://timeapi.io/api/time/current/zone?timeZone=Europe/Paris"

    def heure(self) -> int:
        try:
            with urlopen(self.URL, timeout=5) as reponse:
                data = json.loads(reponse.read())
            return int(data["hour"])
        except (OSError, KeyError, ValueError, TypeError) as e:
            raise HeureIndisponible(f"réponse inexploitable de {self.URL}") from e
