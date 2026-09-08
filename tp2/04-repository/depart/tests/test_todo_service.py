import pytest

from todoapp.erreurs import TodoIntrouvable
from todoapp.todo import Todo
from todoapp.todo_service import TodoService


class FauxDAO:
    def __init__(self, todos=()):
        self._todos = {t.id: t for t in todos}

    def save(self, todo):
        if not todo.id:
            todo.id = max(self._todos, default=0) + 1
        self._todos[todo.id] = todo
        return todo

    def trouver(self, id_):
        return self._todos.get(id_)

    def find_all(self):
        return list(self._todos.values())


def test_terminer_retire_la_tache_des_restantes():
    service = TodoService(FauxDAO([Todo(1, "a"), Todo(2, "b")]))
    service.terminer(1)
    assert [t.title for t in service.restantes()] == ["b"]


def test_terminer_une_tache_inconnue():
    with pytest.raises(TodoIntrouvable):
        TodoService(FauxDAO()).terminer(42)


def test_resume_apres_terminer():
    service = TodoService(FauxDAO([Todo(1, "a")]))
    service.terminer(1)
    assert service.resume() == "aucune tâche restante"
