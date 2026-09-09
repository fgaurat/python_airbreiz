import sys

from geo.carre import Carre
from geo.cercle import Cercle
from geo.chargeur import charger
from geo.rectangle import Rectangle


def depuis_argv(args):
    """python main.py cercle 2  ->  une forme construite depuis la ligne de commande."""
    type_, *valeurs = args
    if type_ == "rectangle":
        return Rectangle(float(valeurs[0]), float(valeurs[1]))
    elif type_ == "carre":
        return Carre(float(valeurs[0]))
    elif type_ == "cercle":
        return Cercle(float(valeurs[0]))
    print(f"forme inconnue : {type_}")
    sys.exit(1)


def main():
    if len(sys.argv) > 1:
        forme = depuis_argv(sys.argv[1:])
        print(f"{forme!r:30} surface = {forme.surface:.2f}")
        return
    with open("formes.txt", encoding="utf-8") as f:
        lignes = [ligne.strip() for ligne in f if ligne.strip()]
    formes = charger(lignes)
    print(f"{len(lignes)} lignes, {len(formes)} formes")
    for forme in formes:
        print(f"{forme!r:30} surface = {forme.surface:.2f}")


if __name__ == "__main__":
    main()
