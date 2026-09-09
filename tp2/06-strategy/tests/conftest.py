import pytest

from todo import Todo


@pytest.fixture
def todos():
    return [
        Todo(1, "relire le rapport", False, priorite=1),
        Todo(2, "Envoyer le compte rendu", True, priorite=0),
        Todo(3, "appeler le client", False, priorite=2),
        Todo(4, "Archiver", False, priorite=1),
    ]
