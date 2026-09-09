"""Le squelette, testé une fois, sans aucun format réel."""
import pytest

from todoapp.rapport import Rapport
from todoapp.todo import Todo


class RapportEspion(Rapport):
    def entete(self, titre):
        return f"E({titre})"

    def ligne(self, todo):
        return f"L({todo.id})"

    def pied(self, restantes, total):
        return f"P({restantes}/{total})"

    def vide(self):
        return "V"


def test_ordre_des_parties():
    todos = [Todo(1, "a"), Todo(2, "b", completed=True), Todo(3, "c")]
    assert RapportEspion().generer(todos, "T") == "E(T)\nL(1)\nL(2)\nL(3)\nP(2/3)\n"


def test_liste_vide_appelle_le_hook_vide():
    assert RapportEspion().generer([]) == "E(Rapport)\nV\nP(0/0)\n"


def test_le_hook_vide_est_optionnel():
    class Minimal(Rapport):
        def entete(self, titre):
            return "E"

        def ligne(self, todo):
            return "L"

        def pied(self, restantes, total):
            return "P"

    assert Minimal().generer([]) == "E\nP\n"


def test_un_format_incomplet_ne_s_instancie_pas():
    class Incomplet(Rapport):
        def entete(self, titre):
            return ""

    with pytest.raises(TypeError):
        Incomplet()
