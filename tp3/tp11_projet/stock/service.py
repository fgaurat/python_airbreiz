import logging

from tp11_projet.stock.depot import Depot, ProduitInconnu
from tp11_projet.stock.modeles import Produit
from tp11_projet.stock.tarification import ClientTaux, ServiceTauxIndisponible

logger = logging.getLogger("stock")


class StockInsuffisant(Exception):
    pass


class ServiceStock:
    def __init__(self, depot: Depot, client_taux: ClientTaux | None = None):
        self.depot = depot
        self.client_taux = client_taux or ClientTaux()

    def ajouter_produit(self, reference: str, nom: str, prix_ht: float, quantite: int = 0) -> Produit:
        try:
            self.depot.charger(reference)
        except ProduitInconnu:
            pass
        else:
            raise ValueError(f"le produit {reference} existe déjà")
        produit = Produit(reference, nom, prix_ht, quantite)
        self.depot.sauvegarder(produit)
        logger.info("produit %s ajouté (%d unités)", reference, quantite)
        return produit

    def entrer_stock(self, reference: str, quantite: int) -> Produit:
        if quantite <= 0:
            raise ValueError("quantité positive attendue")
        produit = self.depot.charger(reference)
        produit.quantite += quantite
        self.depot.sauvegarder(produit)
        return produit

    def sortir_stock(self, reference: str, quantite: int) -> Produit:
        if quantite <= 0:
            raise ValueError("quantité positive attendue")
        produit = self.depot.charger(reference)
        if produit.quantite < quantite:
            raise StockInsuffisant(f"{reference}: {produit.quantite} disponible(s), {quantite} demandé(s)")
        produit.quantite -= quantite
        self.depot.sauvegarder(produit)
        if produit.en_rupture:
            logger.warning("produit %s sous le seuil d'alerte (%d)", reference, produit.quantite)
        return produit

    def produits_en_rupture(self) -> list[Produit]:
        return [p for p in self.depot.tous() if p.en_rupture]

    def valeur_stock(self, devise: str = "EUR") -> float:
        """Valeur HT du stock, convertie dans la devise demandée."""
        total_eur = sum(p.prix_ht * p.quantite for p in self.depot.tous())
        try:
            taux = self.client_taux.taux(devise)
        except ServiceTauxIndisponible:
            logger.error("taux %s indisponible, valeur renvoyée en EUR", devise)
            taux = 1.0
        return round(total_eur * taux, 2)
