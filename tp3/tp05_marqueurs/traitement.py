"""Code métier du TP05."""

import time


def calcul_lourd(n: int) -> int:
    """Simule un calcul long."""
    time.sleep(0.2)
    return sum(i * i for i in range(n))


def telecharger(url: str) -> bytes:
    """Simule un accès réseau (en vrai : urllib / requests)."""
    raise ConnectionError(f"réseau indisponible pour {url}")


def charger_donnees(fichier: str) -> list[str]:
    """Simule le chargement d'un fichier de données."""
    return [f"{fichier}:ligne{i}" for i in range(3)]


def fonction_buggee(x: int) -> int:
    """Bug connu : renvoie x au lieu de x * 2 pour les négatifs."""
    return x * 2 if x >= 0 else x
