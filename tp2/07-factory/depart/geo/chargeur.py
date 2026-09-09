from geo.carre import Carre
from geo.cercle import Cercle
from geo.rectangle import Rectangle


def charger(lignes):
    """Construit les formes décrites par des lignes "type;valeur;valeur"."""
    formes = []
    for ligne in lignes:
        type_, *valeurs = [p.strip() for p in ligne.split(";")]
        if type_ == "rectangle":
            formes.append(Rectangle(float(valeurs[0]), float(valeurs[1])))
        elif type_ == "carre":
            formes.append(Carre(float(valeurs[0])))
        elif type_ == "cercle":
            formes.append(Cercle(float(valeurs[0])))
    return formes
