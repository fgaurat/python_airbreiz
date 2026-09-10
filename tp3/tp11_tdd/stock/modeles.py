from dataclasses import dataclass


@dataclass
class Produit:
    ref: str
    nom: str
    prix_ht: float
    quantite: int = 0

    def __post_init__(self):
        if not self.ref:
            raise ValueError("Référence obligatoire")
        if self.prix_ht < 0:
            raise ValueError("prix négatif")
        if self.quantite < 0:
            raise ValueError("quantité négative")

    def prix_ttc(self):
        return self.prix_ht * 1.2  # Assuming a 20% VAT rate

