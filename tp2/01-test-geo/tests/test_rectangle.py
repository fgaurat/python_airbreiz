from rectangle import Rectangle
import pytest


def test_surface():
    # Arrange
    r = Rectangle(2, 3)
    # Act
    surface = r.surface
    # Assert
    assert surface == 6


@pytest.mark.parametrize(
    ("longueur, largeur, surface_attendue"),
    [
        pytest.param(2, 3, 6, id="valeurs entières"),
        # pytest.param(2, 4, 0, id="largeur nulle"),
    ]
)
def test_surface_with_params(longueur, largeur, surface_attendue):
    # Arrange
    r = Rectangle(longueur, largeur)
    # Act
    surface = r.surface
    # Assert
    assert surface == surface_attendue


def test_surface_type_int():
    # Arrange
    r = Rectangle(2, 3)
    # Act
    surface = r.surface
    # Assert
    assert isinstance(surface, int)


def test_comparaison_egaux():
    # Arrange
    r1 = Rectangle(2, 3)
    r2 = Rectangle(2, 3)

    # Act
    c = r1 == r2

    # Assert
    assert c
    #     assert Rectangle(2, 3) == Rectangle(2, 3)


def test_comparaison_pas_egaux():
    # Arrange
    r1 = Rectangle(2, 3)
    r2 = Rectangle(2, 4)

    # Act
    c = r1 != r2

    # Assert
    assert c
    #     assert Rectangle(2, 3) != Rectangle(2, 3)


def test_build_from_str_mal_formee():
    with pytest.raises(ValueError):
        r = Rectangle.build_from_str("2,3")


def test_set_longeur_negative():
    r = Rectangle(2, 3)

    with pytest.raises(Exception):
        r.longueur = -2


def test_set_largeur_negative():
    r = Rectangle(2, 3)
    with pytest.raises(Exception):
        r.largeur = -2


def test_construction_negative():
    with pytest.raises(AssertionError):
        r = Rectangle(-2, 3)


def test_compteur():
    Rectangle(1, 1)
    Rectangle(1, 2)
    assert Rectangle.get_cpt() == 2
