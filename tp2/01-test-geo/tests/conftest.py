from rectangle import Rectangle
import pytest


@pytest.fixture(autouse=True)
def reset_cpt():

    # setup
    Rectangle._cpt = 0

    yield

    # teardown
    Rectangle._cpt = 0
