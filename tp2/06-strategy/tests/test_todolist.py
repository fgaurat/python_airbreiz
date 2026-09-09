import pytest

from todoapp.todolist import TodoList


@pytest.fixture
def liste():
    liste = TodoList()
    liste.ajouter("a")
    liste.ajouter("b")
    return liste



def test_lister_applique_la_strategie_recue(liste):
    # Un tri factice suffit : on vérifie que TodoList délègue, pas qu'elle trie.
    def inverse(todos):
        return todos[::-1]

    assert [t.title for t in liste.lister(inverse)] == ["b", "a"]


def test_lister_sans_argument_rend_l_ordre_d_ajout(liste):
    assert [t.title for t in liste.lister()] == ["a", "b"]


def test_terminer(liste):
    liste.terminer(1)
    assert liste.lister()[0].completed is True


def test_terminer_inconnu(liste):
    with pytest.raises(LookupError):
        liste.terminer(9)


def test_tri_par_titre(liste):
    def par_titre(todos):
        return sorted(todos, key=lambda t: t.title)

    assert [t.title for t in liste.lister(par_titre)] == ["a", "b"]
    