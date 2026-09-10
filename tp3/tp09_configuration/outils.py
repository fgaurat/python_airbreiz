"""Fonctions avec des doctests : exécutables via `pytest --doctest-modules`."""


def slugifier(texte: str) -> str:
    """Transforme un titre en identifiant URL.

    >>> slugifier("Formation Pytest 2024")
    'formation-pytest-2024'
    >>> slugifier("  espaces   multiples ")
    'espaces-multiples'
    >>> slugifier("")
    ''
    """
    mots = texte.lower().split()
    return "-".join(mots)


def tranche(valeurs: list[int], taille: int) -> list[list[int]]:
    """Découpe une liste en morceaux de `taille`.

    >>> tranche([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    >>> tranche([], 3)
    []
    >>> tranche([1], 0)
    Traceback (most recent call last):
        ...
    ValueError: taille doit être > 0
    """
    if taille <= 0:
        raise ValueError("taille doit être > 0")
    return [valeurs[i : i + taille] for i in range(0, len(valeurs), taille)]
