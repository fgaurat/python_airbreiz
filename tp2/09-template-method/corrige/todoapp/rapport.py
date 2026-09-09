from abc import ABC, abstractmethod

from todoapp.todo import Todo


class Rapport(ABC):
    """Le déroulé d'un rapport, écrit une seule fois.

    Les sous-classes remplissent les trous (entete, ligne, pied, vide).
    Elles ne décident ni de l'ordre, ni du calcul des restantes.
    """

    def generer(self, todos: list[Todo], titre: str = "Rapport") -> str:
        parties = [self.entete(titre)]
        if not todos:
            parties.append(self.vide())
        parties.extend(self.ligne(todo) for todo in todos)
        restantes = sum(1 for t in todos if not t.completed)
        parties.append(self.pied(restantes, len(todos)))
        return self.assembler(parties)

    @abstractmethod
    def entete(self, titre: str) -> str: ...

    @abstractmethod
    def ligne(self, todo: Todo) -> str: ...

    @abstractmethod
    def pied(self, restantes: int, total: int) -> str: ...

    def vide(self) -> str:
        """Hook optionnel : ce qu'on affiche quand il n'y a aucune tâche."""
        return ""

    def assembler(self, parties: list[str]) -> str:
        return "\n".join(p for p in parties if p) + "\n"
