from hello import bonjour


def test_bonjour_par_defaut():
    # Arrange
    expected = "Bonjour"

    # Act
    result = bonjour()

    # Assert
    assert result == expected


def test_bonjour_avec_nom():
    # Arrange
    nom = "Alice"
    expected = "Bonjour Alice"

    # Act
    result = bonjour(nom)

    # Assert
    assert result == expected
