import pytest
from unittest.mock import MagicMock, patch
from salutation import formule, saluer
from unittest.mock import Mock
from horloges import Horloge


@pytest.mark.parametrize(
    ("heure", "attendue"),
    [
        pytest.param(0, "Bonjour", id="minuit"),
        pytest.param(11, "Bonjour", id="fin_de_matinee"),
        pytest.param(12, "Bon après-midi", id="midi"),
        pytest.param(17, "Bon après-midi", id="fin_d_apres_midi"),
        pytest.param(18, "Bonsoir", id="18h"),
        pytest.param(23, "Bonsoir", id="23h"),
    ],
)
def test_formule(heure, attendue):
    assert formule(heure) == attendue


@pytest.mark.parametrize("heure", [-1, 24])
def test_formule_refuse_une_heure_invalide(heure):
    with pytest.raises(ValueError):
        formule(heure)


class HorlogeFixe:
    def __init__(self, heure):
        self._heure = heure

    def heure(self):
        return self._heure


def test_saluer_utilise_l_horloge_recue():
    assert saluer("Ada", HorlogeFixe(9)) == "Bonjour, Ada !"
    assert saluer("Ada", HorlogeFixe(21)) == "Bonsoir, Ada !"


def test_saluer_utilise_l_horloge_recue_avec_mock():
    horloge = Mock(spec=Horloge)
    horloge.heure.return_value = 9
    assert saluer("Ada", horloge) == "Bonjour, Ada !"
    horloge.heure.return_value = 21
    assert saluer("Ada", horloge) == "Bonsoir, Ada !"
    horloge.heure.assert_called()
