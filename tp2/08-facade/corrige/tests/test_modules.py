"""Les modules derrière la façade gardent leurs tests unitaires."""
from todoapp.chargeur import lire_csv
from todoapp.filtres import restantes
from todoapp.formateur import en_texte
from todoapp.todo import Todo


def test_lire_csv(source):
    assert lire_csv(source)[1] == Todo(2, "Envoyer le compte rendu", True)


def test_restantes():
    todos = [Todo(1, "a"), Todo(2, "b", True)]
    assert restantes(todos) == [Todo(1, "a")]


def test_en_texte():
    assert en_texte([Todo(1, "a"), Todo(2, "b", True)]) == "[ ] a\n[x] b\n"


def test_en_texte_vide():
    assert en_texte([]) == "\n"
