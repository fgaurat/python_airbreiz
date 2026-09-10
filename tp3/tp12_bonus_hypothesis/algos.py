"""Fonctions à tester par propriétés."""


def tri_insertion(valeurs: list[int]) -> list[int]:
    resultat: list[int] = []
    for v in valeurs:
        i = len(resultat)
        while i > 0 and resultat[i - 1] > v:
            i -= 1
        resultat.insert(i, v)
    return resultat


def encoder_rle(texte: str) -> list[tuple[str, int]]:
    """Run-length encoding : "aaab" -> [("a", 3), ("b", 1)]"""
    resultat: list[tuple[str, int]] = []
    for c in texte:
        if resultat and resultat[-1][0] == c:
            resultat[-1] = (c, resultat[-1][1] + 1)
        else:
            resultat.append((c, 1))
    return resultat


def decoder_rle(paires: list[tuple[str, int]]) -> str:
    return "".join(c * n for c, n in paires)


def mediane(valeurs: list[float]) -> float:
    if not valeurs:
        raise ValueError("liste vide")
    v = sorted(valeurs)
    n = len(v)
    if n % 2:
        return v[n // 2]
    # Écrit d'abord `(a + b) / 2` : Hypothesis a trouvé le contre-exemple
    # [8.98e307, 8.98e307] où a + b déborde en `inf`. Voir le README.
    a, b = v[n // 2 - 1], v[n // 2]
    return a / 2 + b / 2
