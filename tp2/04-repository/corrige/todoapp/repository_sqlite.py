import sqlite3
from typing import Optional

from todoapp.erreurs import TodoIntrouvable
from todoapp.todo import Todo


class SqliteTodoRepository:
    """Implémentation sqlite : l'ancien TodoDAO, aligné sur le contrat."""

    def __init__(self, db_file):
        self._con = sqlite3.connect(db_file)
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS todos_tbl (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT,
                completed INTEGER
            )
        """)
        self._con.commit()

    def ajouter(self, todo: Todo) -> Todo:
        cur = self._con.execute(
            "INSERT INTO todos_tbl (title, completed) VALUES (?, ?)",
            (todo.title, todo.completed),
        )
        self._con.commit()
        todo.id = cur.lastrowid
        return todo

    def obtenir(self, id_: int) -> Optional[Todo]:
        ligne = self._con.execute(
            "SELECT id, title, completed FROM todos_tbl WHERE id = ?", (id_,)
        ).fetchone()
        return None if ligne is None else Todo(ligne[0], ligne[1], bool(ligne[2]))

    def enregistrer(self, todo: Todo) -> None:
        cur = self._con.execute(
            "UPDATE todos_tbl SET title = ?, completed = ? WHERE id = ?",
            (todo.title, todo.completed, todo.id),
        )
        self._con.commit()
        if cur.rowcount == 0:
            raise TodoIntrouvable(f"aucune tâche n°{todo.id}")

    def lister(self) -> list[Todo]:
        lignes = self._con.execute(
            "SELECT id, title, completed FROM todos_tbl ORDER BY id"
        ).fetchall()
        return [Todo(i, t, bool(c)) for i, t, c in lignes]

    def fermer(self):
        self._con.close()
