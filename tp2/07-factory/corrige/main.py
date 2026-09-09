import sys

from geo.chargeur import charger
from geo.erreurs import DimensionInvalide, FormeInconnue
from geo.fabrique import fabrique_par_defaut


def main():
    fabrique = fabrique_par_defaut()
    try:
        if len(sys.argv) > 1:
            formes = [fabrique.creer(sys.argv[1], *sys.argv[2:])]
        else:
            with open("formes.txt", encoding="utf-8") as f:
                lignes = [ligne.strip() for ligne in f if ligne.strip()]
            formes = charger(lignes, fabrique)
    except (FormeInconnue, DimensionInvalide) as e:
        sys.exit(f"erreur : {e}")
    for forme in formes:
        print(f"{forme!r:30} surface = {forme.surface:.2f}")


if __name__ == "__main__":
    main()
