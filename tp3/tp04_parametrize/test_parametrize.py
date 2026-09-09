"""TP04 - Paramétrage : un test, plusieurs jeux de données.

@pytest.mark.parametrize génère UN test par jeu de valeurs. Chaque cas est
indépendant : il apparaît séparément dans le rapport, peut être sélectionné
avec -k, et un échec n'empêche pas les autres cas de s'exécuter.
"""

import pytest

from tp04_parametrize.validation import (
    celsius_vers_fahrenheit,
    classer_age,
    est_palindrome,
    est_premier,
    fizzbuzz,
    valider_email,
)

# ---------------------------------------------------------------------------
# 1. Forme de base : un paramètre
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("texte", ["kayak", "Radar", "A man, a plan, a canal: Panama", ""])
def test_palindromes(texte):
    assert est_palindrome(texte)


@pytest.mark.parametrize("texte", ["python", "pytest"])
def test_non_palindromes(texte):
    assert not est_palindrome(texte)


# ---------------------------------------------------------------------------
# 2. Plusieurs paramètres : "a, b" + liste de tuples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n, attendu",
    [
        (1, "1"),
        (3, "Fizz"),
        (5, "Buzz"),
        (15, "FizzBuzz"),
        (30, "FizzBuzz"),
        (7, "7"),
    ],
)
def test_fizzbuzz(n, attendu):
    assert fizzbuzz(n) == attendu


# ---------------------------------------------------------------------------
# 3. ids : rendre les cas lisibles dans le rapport (-v)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email, valide",
    [
        ("alice@example.com", True),
        ("bob.martin+news@mail.fr", True),
        ("sans-arobase.com", False),
        ("@vide.com", False),
        ("alice@", False),
    ],
    ids=["simple", "avec_plus_et_point", "sans_arobase", "sans_local", "sans_domaine"],
)
def test_valider_email(email, valide):
    assert valider_email(email) is valide


# ids peut être une fonction : appelée pour chaque valeur de paramètre
def _id_temperature(valeur):
    if isinstance(valeur, (int, float)):
        return f"{valeur}deg"
    return None  # None -> id par défaut


@pytest.mark.parametrize(
    "celsius, fahrenheit",
    [(0, 32), (100, 212), (-40, -40), (37, 98.6)],
    ids=_id_temperature,
)
def test_conversion(celsius, fahrenheit):
    assert celsius_vers_fahrenheit(celsius) == pytest.approx(fahrenheit)


# ---------------------------------------------------------------------------
# 4. pytest.param : id et marqueurs sur un cas précis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "age, categorie",
    [
        pytest.param(0, "mineur", id="nouveau-ne"),
        pytest.param(17, "mineur", id="limite-mineur"),
        pytest.param(18, "adulte", id="limite-adulte"),
        pytest.param(64, "adulte"),
        pytest.param(65, "senior"),
        pytest.param(150, "invalide", marks=pytest.mark.xfail(reason="âge non plausible : règle métier à définir")),
        pytest.param(-1, "erreur", marks=pytest.mark.skip(reason="cas d'erreur testé ailleurs")),
    ],
)
def test_classer_age(age, categorie):
    assert classer_age(age) == categorie


def test_classer_age_negatif():
    with pytest.raises(ValueError):
        classer_age(-1)


# ---------------------------------------------------------------------------
# 5. Empilement : produit cartésien des paramètres
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("x", [0, 1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_produit_cartesien(x, y):
    # 3 x 2 = 6 tests : test_produit_cartesien[10-0], [10-1], ...
    assert x + y == y + x



# ---------------------------------------------------------------------------
# 6. Paramétrer une classe entière
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 6, 9])
class TestMultiplesDeTrois:
    
    def test_fizz(self, n):
        assert fizzbuzz(n).startswith("Fizz")

    def test_divisible(self, n):
        assert n % 3 == 0


# ---------------------------------------------------------------------------
# 7. Fixtures paramétrées (définies dans conftest.py)
# ---------------------------------------------------------------------------


def test_moteur_bdd(moteur_bdd):
    # Exécuté 3 fois : [sqlite], [postgres], [mysql]
    assert moteur_bdd["connecte"]
    assert moteur_bdd["moteur"] in {"sqlite", "postgres", "mysql"}


def test_nombre_et_libelle(nombre_et_libelle):
    nombre, libelle = nombre_et_libelle
    assert isinstance(nombre, int) and isinstance(libelle, str)


# ---------------------------------------------------------------------------
# 8. Paramétrage indirect : la valeur passe par une fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def utilisateur(request):
    """Reçoit request.param (l'âge) et construit un objet plus riche."""
    age = request.param
    return {"nom": f"user{age}", "age": age, "categorie": classer_age(age)}


@pytest.mark.parametrize("utilisateur", [10, 30, 70], indirect=True)
def test_indirect(utilisateur):
    assert utilisateur["categorie"] == classer_age(utilisateur["age"])


# ---------------------------------------------------------------------------
# 9. Paramètre généré par pytest_generate_tests (conftest.py)
# ---------------------------------------------------------------------------


def test_nombres_premiers(nombre_premier):
    assert est_premier(nombre_premier)


@pytest.mark.parametrize("n", [0, 1, 4, 9, 15])
def test_non_premiers(n):
    assert not est_premier(n)
