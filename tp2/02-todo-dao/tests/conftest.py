

import pytest
from todo_dao import TodoDAO
from todo import Todo
from pathlib import Path


@pytest.fixture(
    params=[
        # pytest.param('memoire', id="memoire"),
        pytest.param('fichier', id="fichier"),
    ]
)
def dao(request, tmp_path):
    chemin = ":memory:" if request.param == "memoire" else tmp_path / "todos.db"
    # chemin = ":memory:"

    # if request.param == "fichier":
    #     chemin = Path("tp2/01-test-geo/tests/todos.db")
    #     chemin.parent.mkdir(parents=True, exist_ok=True)

    dao = TodoDAO(chemin)

    dao.creer_table()
    yield dao
    dao.fermer()  # teardown : exécuté après le test, même s'il a échoué


@pytest.fixture
def todos():
    return [
        Todo(title="Faire des tests"),
        Todo(title="Faire encore des tests", completed=True),
        Todo(title="Refaire des tests"),
    ]


@pytest.fixture
def dao_rempli(dao, todos):
    for todo in todos:
        dao.good_save(todo)
    return dao
