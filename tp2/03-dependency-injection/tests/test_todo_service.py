from todo_service import TodoService
from todo import Todo
import pytest


class FauxDAO:
    """Un DAO en mémoire, juste assez pour le service."""

    def __init__(self, todos=()):
        self._todos = list(todos)

    def creer_table(self):
        print("Création de la table")

    def save(self, todo):
        todo.id = len(self._todos) + 1
        self._todos.append(todo)
        return todo

    def find_all(self):
        return list(self._todos)


def test_restantes_exclut_les_terminees():
    dao = FauxDAO([Todo(1, "a"), Todo(2, "b", completed=True), Todo(3, "c")])

    service = TodoService(dao)
    # Comment mettre un todo terminé et un todo non terminé dans le service,
    # sans passer par le fichier todos.db ?

    #
    assert service.resume() == "2 tâches restantes"


def test_ajouter_passe_par_la_source():
    dao = FauxDAO()
    service = TodoService(dao)
    todo = service.ajouter("Relire")
    assert todo.id == 1
    assert dao.find_all() == [Todo(1, "Relire")]


@pytest.mark.parametrize(
    ("todos", "attendu"),
    [
        pytest.param([], "aucune tâche restante", id="zero"),
        pytest.param([Todo(1, "a")], "1 tâche restante", id="un"),
        pytest.param([Todo(1, "a"), Todo(2, "b")],
                     "2 tâches restantes", id="deux"),
        pytest.param([Todo(1, "a", completed=True)],
                     "aucune tâche restante", id="terminee"),
    ],
)
def test_resume(todos, attendu):
    assert TodoService(FauxDAO(todos)).resume() == attendu
