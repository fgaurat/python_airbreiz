"""Code métier du TP01 : une calculatrice volontairement simple."""


def additionner(a, b):
    return a + b


def soustraire(a, b):
    return a - b


def multiplier(a, b):
    return a * b


def diviser(a, b):
    if b == 0:
        raise ZeroDivisionError("division par zéro impossible")
    return a / b


def moyenne(valeurs):
    if not valeurs:
        raise ValueError("impossible de calculer la moyenne d'une liste vide")
    return sum(valeurs) / len(valeurs)


def est_pair(n):
    return n % 2 == 0


def factorielle(n):
    if n < 0:
        raise ValueError("n doit être positif ou nul")
    return 1 if n in (0, 1) else n * factorielle(n - 1)
