from dataclasses import dataclass, field
from datetime import date


@dataclass
class Produit:
    reference: str
    nom: str
    prix_ht: float
    quantite: int = 0
    seuil_alerte: int = 5
    date_creation: date = field(default_factory=date.today)

    def __post_init__(self):
        if not self.reference:
            raise ValueError("référence obligatoire")
        if self.prix_ht < 0:
            raise ValueError("prix négatif")
        if self.quantite < 0:
            raise ValueError("quantité négative")

    @property
    def en_rupture(self) -> bool:
        return self.quantite <= self.seuil_alerte

    def prix_ttc(self, taux_tva: float = 0.20) -> float:
        return round(self.prix_ht * (1 + taux_tva), 2)

    def to_dict(self) -> dict:
        return {
            "reference": self.reference,
            "nom": self.nom,
            "prix_ht": self.prix_ht,
            "quantite": self.quantite,
            "seuil_alerte": self.seuil_alerte,
            "date_creation": self.date_creation.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Produit":
        return cls(
            reference=d["reference"],
            nom=d["nom"],
            prix_ht=d["prix_ht"],
            quantite=d.get("quantite", 0),
            seuil_alerte=d.get("seuil_alerte", 5),
            date_creation=date.fromisoformat(d["date_creation"]),
        )
