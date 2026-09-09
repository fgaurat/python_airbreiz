from todoapp.formats import RapportHtml, RapportMarkdown, RapportTexte
from todoapp.todo import Todo

todos = [
    Todo(1, "Relire le rapport"),
    Todo(2, "Envoyer le compte rendu", completed=True),
    Todo(3, "Appeler le client <urgent>"),
]

if __name__ == "__main__":
    for rapport in (RapportTexte(), RapportHtml(), RapportMarkdown()):
        print(rapport.generer(todos))
