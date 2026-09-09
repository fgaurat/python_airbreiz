from todoapp.chargeur import lire_csv
from todoapp.ecrivain import ecrire
from todoapp.filtres import restantes
from todoapp.formateur import en_texte
from todoapp.journal import Journal


def main():
    journal = Journal()
    todos = lire_csv("todos.csv")
    journal.noter(f"{len(todos)} tâches lues")
    a_faire = restantes(todos)
    texte = en_texte(a_faire)
    ecrire("restantes.txt", texte)
    journal.noter(f"{len(a_faire)} tâches exportées vers restantes.txt")


if __name__ == "__main__":
    main()
