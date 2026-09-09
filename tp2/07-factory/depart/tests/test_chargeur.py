from geo.cercle import Cercle
from geo.chargeur import charger
from geo.rectangle import Rectangle


def test_charger_un_rectangle():
    assert charger(["rectangle;2;3"]) == [Rectangle(2, 3)]


def test_charger_un_cercle():
    (cercle,) = charger(["cercle;2"])
    assert isinstance(cercle, Cercle)
    assert cercle.rayon == 2
