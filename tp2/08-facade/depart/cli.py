"""Même export, appelé depuis la ligne de commande : python cli.py todos.csv sortie.txt"""
import sys

from todoapp.chargeur import lire_csv
from todoapp.ecrivain import ecrire
from todoapp.filtres import restantes
from todoapp.formateur import en_texte


def main(source, destination):
    todos = lire_csv(source)
    texte = en_texte(todos)
    restantes(todos)
    ecrire(destination, texte)
    print(f"export terminé : {destination}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
