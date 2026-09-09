"""Code métier du TP03 : comptes bancaires et journal d'opérations."""

from pathlib import Path


class SoldeInsuffisant(Exception):
    pass


class Compte:
    def __init__(self, titulaire: str, solde: float = 0.0):
        self.titulaire = titulaire
        self.solde = solde

    def deposer(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("le montant doit être positif")
        self.solde += montant

    def retirer(self, montant: float) -> None:
        if montant > self.solde:
            raise SoldeInsuffisant(f"solde {self.solde} < {montant}")
        self.solde -= montant

    def virer_vers(self, autre: "Compte", montant: float) -> None:
        self.retirer(montant)
        autre.deposer(montant)


class Banque:
    def __init__(self, nom: str = "Banque Test"):
        self.nom = nom
        self._comptes: dict[str, Compte] = {}

    def ouvrir_compte(self, titulaire: str, solde: float = 0.0) -> Compte:
        if titulaire in self._comptes:
            raise ValueError(f"{titulaire} a déjà un compte")
        compte = Compte(titulaire, solde)
        self._comptes[titulaire] = compte
        return compte

    def trouver(self, titulaire: str) -> Compte:
        return self._comptes[titulaire]

    @property
    def nb_comptes(self) -> int:
        return len(self._comptes)


class Journal:
    """Journal d'opérations persisté dans un fichier texte (une ligne par opération)."""

    def __init__(self, chemin: Path):
        self.chemin = Path(chemin)
        self._fichier = self.chemin.open("a", encoding="utf-8")

    def enregistrer(self, message: str) -> None:
        self._fichier.write(message + "\n")
        self._fichier.flush()

    def lire(self) -> list[str]:
        return self.chemin.read_text(encoding="utf-8").splitlines()

    def fermer(self) -> None:
        self._fichier.close()
