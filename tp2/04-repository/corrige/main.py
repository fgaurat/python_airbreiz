import os

from todoapp.repository_sqlite import SqliteTodoRepository
from todoapp.repository_memoire import TodoRepositoryMemoire
from todoapp.todo_service import TodoService


def main():
    if os.path.exists("todos.db"):
        os.remove("todos.db")
    repo1 = SqliteTodoRepository("todos.db")
    repo2 = TodoRepositoryMemoire()
    service = TodoService(repo2)

    todo = service.ajouter("Relire le rapport")
    print("après ajout   :", service.resume())
    service.terminer(todo.id)
    print("après terminer:", service.resume())
    print("en base       :", repo2.lister())
    repo2.fermer()


if __name__ == "__main__":
    main()
