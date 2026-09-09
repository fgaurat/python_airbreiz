from todoapp import rapport_html, rapport_texte
from todoapp.todo import Todo

todos = [
    Todo(1, "Relire le rapport"),
    Todo(2, "Envoyer le compte rendu", completed=True),
    Todo(3, "Appeler le client <urgent>"),
]

if __name__ == "__main__":
    print(rapport_texte.generer(todos))
    print(rapport_html.generer(todos))
