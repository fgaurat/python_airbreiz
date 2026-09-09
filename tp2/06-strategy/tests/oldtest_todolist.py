from todoapp.todolist import TodoList


def test_tri_par_titre():
    liste = TodoList()
    liste.ajouter("relire le rapport", priorite=1)
    liste.ajouter("Envoyer le compte rendu")
    liste.ajouter("appeler le client", priorite=2)
    titres = [t.title for t in liste.lister("titre")]
    assert titres == ["appeler le client", "Envoyer le compte rendu", "relire le rapport"]


def test_tri_par_priorite():
    liste = TodoList()
    liste.ajouter("relire le rapport", priorite=1)
    liste.ajouter("Envoyer le compte rendu")
    liste.ajouter("appeler le client", priorite=2)
    titres = [t.title for t in liste.lister("priorite")]
    assert titres == ["appeler le client", "relire le rapport", "Envoyer le compte rendu"]
