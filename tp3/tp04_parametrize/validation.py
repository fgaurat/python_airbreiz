"""Code métier du TP04 : petites fonctions de validation / transformation."""

import re

_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def valider_email(email: str) -> bool:
    return bool(_EMAIL.match(email))


def est_palindrome(texte: str) -> bool:
    nettoye = "".join(c.lower() for c in texte if c.isalnum())
    return nettoye == nettoye[::-1]


def fizzbuzz(n: int) -> str:
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)


def celsius_vers_fahrenheit(c: float) -> float:
    return c * 9 / 5 + 32


def classer_age(age: int) -> str:
    if age < 0:
        raise ValueError("âge négatif")
    if age < 18:
        return "mineur"
    if age < 65:
        return "adulte"
    return "senior"


def est_premier(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, int(n**0.5) + 1))
