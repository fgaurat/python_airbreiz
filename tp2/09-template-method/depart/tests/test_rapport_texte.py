from todoapp.rapport_texte import generer
from todoapp.todo import Todo


def test_pied_compte_les_restantes():
    todos = [Todo(1, "a"), Todo(2, "b", completed=True), Todo(3, "c")]
    assert generer(todos).endswith("2 restante(s) sur 3\n")


def test_liste_vide():
    assert "(aucune tâche)" in generer([])
