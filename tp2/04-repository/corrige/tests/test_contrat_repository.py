"""Test de contrat : chaque test tourne sur chaque implémentation.

Si une implémentation diverge du contrat, c'est ici que ça casse,
pas en production.
"""
import pytest

from todoapp.erreurs import TodoIntrouvable
from todoapp.repository_memoire import TodoRepositoryMemoire
from todoapp.repository_sqlite import SqliteTodoRepository
from todoapp.todo import Todo


@pytest.fixture(params=["memoire", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memoire":
        yield TodoRepositoryMemoire()
    else:
        repo = SqliteTodoRepository(tmp_path / "todos.db")
        yield repo
        repo.fermer()


def test_ajouter_attribue_des_ids_croissants(repo):
    a = repo.ajouter(Todo(title="a"))
    b = repo.ajouter(Todo(title="b"))
    assert (a.id, b.id) == (1, 2)


def test_obtenir_un_todo_ajoute(repo):
    repo.ajouter(Todo(title="a"))
    assert repo.obtenir(1) == Todo(1, "a", False)


def test_obtenir_un_inconnu_renvoie_none(repo):
    assert repo.obtenir(42) is None


def test_enregistrer_modifie_sans_dupliquer(repo):
    # Le test qui était rouge sur le DAO : c'est le bug de main.py.
    todo = repo.ajouter(Todo(title="a"))
    todo.completed = True
    repo.enregistrer(todo)
    assert repo.lister() == [Todo(1, "a", True)]


def test_enregistrer_un_inconnu_est_une_erreur(repo):
    with pytest.raises(TodoIntrouvable):
        repo.enregistrer(Todo(42, "fantôme"))


def test_lister_rend_l_ordre_d_ajout(repo):
    for titre in ("c", "a", "b"):
        repo.ajouter(Todo(title=titre))
    assert [t.title for t in repo.lister()] == ["c", "a", "b"]


def test_lister_vide(repo):
    assert repo.lister() == []
