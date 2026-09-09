from geo.calc_geo import CalcGeo
from geo.fabrique import FabriqueFormes


def charger(lignes, fabrique: FabriqueFormes) -> list[CalcGeo]:
    """Construit les formes décrites par des lignes "type;valeur;valeur"."""
    formes = []
    for ligne in lignes:
        nom, *valeurs = [p.strip() for p in ligne.split(";")]
        formes.append(fabrique.creer(nom, *valeurs))
    return formes
