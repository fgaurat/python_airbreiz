"""
Pattern Decorator — façon Head First Design Patterns (Starbuzz Coffee)
"""
from abc import ABC, abstractmethod


# ---------- Composant abstrait ----------
class Boisson(ABC):
    @property
    @abstractmethod
    def prix(self) -> float: ...

    @property
    @abstractmethod
    def title(self) -> str: ...

    def __str__(self):
        return f"{self.title} : {self.prix:.2f} €"


# ---------- Composants concrets ----------
class Sumatra(Boisson):
    @property
    def prix(self): return 3.5

    @property
    def title(self): return "Sumatra"


class Expresso(Boisson):
    @property
    def prix(self): return 2.0

    @property
    def title(self): return "Expresso"


# ---------- Décorateur abstrait : EST une Boisson et A une Boisson ----------
class Topping(Boisson):
    def __init__(self, boisson: Boisson):
        self._boisson = boisson


# ---------- Décorateurs concrets ----------
class Chocolat(Topping):
    @property
    def prix(self): return self._boisson.prix + 1.0

    @property
    def title(self): return f"{self._boisson.title}, Chocolat"


class Chantilly(Topping):
    @property
    def prix(self): return self._boisson.prix + 0.5

    @property
    def title(self): return f"{self._boisson.title}, Chantilly"


def main():
    boisson: Boisson = Expresso()
    print(boisson)                      # Expresso : 2.00 €

    boisson = Chocolat(boisson)
    print(boisson)                      # Expresso, Chocolat : 3.00 €

    boisson = Chantilly(boisson)
    # Expresso, Chocolat, Chantilly : 3.50 €
    print(boisson)
    # Expresso, Chocolat, Chantilly : 3.50 €
    print(boisson.prix)

    # Empilage direct, double chocolat
    # Expresso, Chocolat, Chocolat : 4.00 €
    print(Chocolat(Chocolat(Expresso())))


if __name__ == '__main__':
    main()
