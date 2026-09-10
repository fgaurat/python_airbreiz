"""Client vers un service externe de taux de change (réseau)."""

import json
import urllib.request

URL_TAUX = "https://api.taux.example/latest"


class ServiceTauxIndisponible(Exception):
    pass


class ClientTaux:
    def __init__(self, url: str = URL_TAUX, timeout: float = 3.0):
        self.url = url
        self.timeout = timeout

    def taux(self, devise: str) -> float:
        """Renvoie le taux EUR -> devise. 1.0 pour EUR."""
        if devise == "EUR":
            return 1.0
        try:
            with urllib.request.urlopen(f"{self.url}?base=EUR&symbols={devise}", timeout=self.timeout) as rep:
                donnees = json.loads(rep.read())
        except OSError as exc:
            raise ServiceTauxIndisponible(str(exc)) from exc
        try:
            return float(donnees["rates"][devise])
        except (KeyError, TypeError, ValueError) as exc:
            raise ServiceTauxIndisponible(f"réponse invalide : {donnees!r}") from exc
