from geo.rectangle import Rectangle


class Carre(Rectangle):

    def __init__(self, cote: float = 0):
        super().__init__(cote, cote)

    @property
    def cote(self):
        # Plus d'attribut __cote dupliqué : la longueur est la source de vérité.
        return self.longueur

    @cote.setter
    def cote(self, cote):
        self.longueur = cote
        self.largeur = cote

    def __str__(self) -> str:
        return f"{__class__.__name__} cote={self.cote}"
