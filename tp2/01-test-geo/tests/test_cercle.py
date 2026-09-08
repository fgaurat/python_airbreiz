from cercle import Cercle
import pytest
import math


@pytest.mark.parametrize(
    ("rayon, surface_attendue"),
    [
        pytest.param(1, math.pi, id="rayon 1"),
        pytest.param(2, 4*math.pi, id="rayon 2"),
        pytest.param(0.5, math.pi/4, id="rayon 2"),
    ]
)
def test_surface(rayon, surface_attendue):
    ce = Cercle(rayon)
    s = ce.surface
    assert s == surface_attendue


def test_surface_2():
    ce = Cercle(2)
    s = ce.surface
    assert s == pytest.approx(4*math.pi)
