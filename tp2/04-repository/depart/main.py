import os

from todoapp.todo_dao import TodoDAO
from todoapp.todo_service import TodoService


def main():
    if os.path.exists("todos.db"):
        os.remove("todos.db")
    dao = TodoDAO("todos.db")
    dao.creer_table()
    service = TodoService(dao)

    todo = service.ajouter("Relire le rapport")
    print("après ajout   :", service.resume())
    service.terminer(todo.id)
    print("après terminer:", service.resume())
    print("en base       :", list(dao.find_all()))
    dao.fermer()


if __name__ == "__main__":
    main()
