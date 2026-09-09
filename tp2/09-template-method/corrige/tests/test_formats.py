import pytest

from todoapp.formats import RapportHtml, RapportMarkdown, RapportTexte
from todoapp.todo import Todo

TODOS = [Todo(1, "a"), Todo(2, "b", completed=True), Todo(3, "c")]


# ------------------------------------------------ les deux tests de l'étape 1, pour tous


@pytest.mark.parametrize("rapport", [RapportTexte(), RapportHtml(), RapportMarkdown()])
def test_pied_compte_les_restantes(rapport):
    assert "2 restante(s) sur 3" in rapport.generer(TODOS)


@pytest.mark.parametrize(
    ("rapport", "attendu"),
    [
        (RapportTexte(), "(aucune tâche)"),
        (RapportHtml(), "aucune tâche"),
        (RapportMarkdown(), "0 restante(s) sur 0"),
    ],
)
def test_liste_vide(rapport, attendu):
    assert attendu in rapport.generer([])


# ------------------------------------------------ les méthodes propres à chaque format


def test_texte_ligne():
    assert RapportTexte().ligne(Todo(1, "a", completed=True)) == "[x] a"


def test_texte_bout_en_bout():
    assert RapportTexte().generer(TODOS, "T") == (
        "== T ==\n\n[ ] a\n[x] b\n[ ] c\n\n2 restante(s) sur 3\n"
    )


def test_html_ligne_terminee():
    assert RapportHtml().ligne(Todo(1, "a", completed=True)) == '<li class="faite">a</li>'


def test_html_echappe_le_titre_et_les_taches():
    assert RapportHtml().entete("<T>") == "<h1>&lt;T&gt;</h1>\n<ul>"
    assert "&lt;urgent&gt;" in RapportHtml().ligne(Todo(1, "<urgent>"))


def test_markdown_ligne():
    assert RapportMarkdown().ligne(Todo(1, "a")) == "- [ ] a"


def test_markdown_pied():
    assert RapportMarkdown().pied(1, 2) == "\n_1 restante(s) sur 2_"
