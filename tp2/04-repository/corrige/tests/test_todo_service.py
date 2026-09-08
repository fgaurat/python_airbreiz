import pytest

from todoapp.erreurs import TodoIntrouvable
from todoapp.repository_memoire import TodoRepositoryMemoire
from todoapp.todo import Todo
from todoapp.todo_service import TodoService


@pytest.fixture
def service():
    return TodoService(TodoRepositoryMemoire([Todo(title="a"), Todo(title="b")]))


def test_terminer_retire_la_tache_des_restantes(service):
    service.terminer(1)
    assert [t.title for t in service.restantes()] == ["b"]


def test_terminer_ne_duplique_pas(service):
    service.terminer(1)
    assert len(service._repo.lister()) == 2


def test_terminer_une_tache_inconnue(service):
    with pytest.raises(TodoIntrouvable):
        service.terminer(42)


def test_resume_apres_terminer(service):
    service.terminer(1)
    service.terminer(2)
    assert service.resume() == "aucune tâche restante"
