from html import escape

from todoapp.rapport import Rapport
from todoapp.todo import Todo


class RapportTexte(Rapport):
    def entete(self, titre):
        return f"== {titre} ==\n"

    def ligne(self, todo: Todo):
        return f"[{'x' if todo.completed else ' '}] {todo.title}"

    def pied(self, restantes, total):
        return f"\n{restantes} restante(s) sur {total}"

    def vide(self):
        return "(aucune tâche)"


class RapportHtml(Rapport):
    def entete(self, titre):
        return f"<h1>{escape(titre)}</h1>\n<ul>"

    def ligne(self, todo: Todo):
        classe = "faite" if todo.completed else "a-faire"
        return f'<li class="{classe}">{escape(todo.title)}</li>'

    def pied(self, restantes, total):
        return f"</ul>\n<p>{restantes} restante(s) sur {total}</p>"

    def vide(self):
        return "<li><em>aucune tâche</em></li>"


class RapportMarkdown(Rapport):
    def entete(self, titre):
        return f"# {titre}\n"

    def ligne(self, todo: Todo):
        return f"- [{'x' if todo.completed else ' '}] {todo.title}"

    def pied(self, restantes, total):
        return f"\n_{restantes} restante(s) sur {total}_"
