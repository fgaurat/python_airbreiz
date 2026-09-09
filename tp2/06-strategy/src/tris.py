"""Stratégies de tri : chaque tri est un callable list[Todo] -> list[Todo].

Ajouter un tri = ajouter une fonction ici. TodoList n'est pas touchée.
"""
from todoapp.todo import Todo


def par_ajout(todos: list[Todo]) -> list[Todo]:
    return list(todos)


def par_titre(todos: list[Todo]) -> list[Todo]:
    return sorted(todos, key=lambda t: t.title.lower())


def par_priorite(todos: list[Todo]) -> list[Todo]:
    return sorted(todos, key=lambda t: t.priorite, reverse=True)


def par_priorite_puis_titre(todos: list[Todo]) -> list[Todo]:
    return sorted(todos, key=lambda t: (-t.priorite, t.title.lower()))


def restantes_d_abord(todos: list[Todo]) -> list[Todo]:
    return sorted(todos, key=lambda t: t.completed)


class RestantesAuMoins:
    """Stratégie avec état : restantes d'abord, en ignorant les priorités < seuil."""

    def __init__(self, seuil: int):
        self.seuil = seuil

    def __call__(self, todos: list[Todo]) -> list[Todo]:
        retenues = [t for t in todos if t.priorite >= self.seuil]
        return sorted(retenues, key=lambda t: t.completed)
