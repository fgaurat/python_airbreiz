import sqlite3

from todoapp.todo import Todo


class TodoDAO:

    def __init__(self, db_file):
        self.db_file = db_file
        self._con = sqlite3.connect(db_file)

    def creer_table(self):
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS todos_tbl (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT,
                completed INTEGER
            )
        """)
        self._con.commit()

    def save(self, todo: Todo) -> Todo:
        cur = self._con.execute(
            "INSERT INTO todos_tbl (title, completed) VALUES (?, ?)",
            (todo.title, todo.completed),
        )
        self._con.commit()
        todo.id = cur.lastrowid
        return todo

    def trouver(self, id_: int):
        res = self._con.execute(
            "SELECT id, title, completed FROM todos_tbl WHERE id = ?", (id_,)
        )
        ligne = res.fetchone()
        if ligne is None:
            return None
        return Todo(ligne[0], ligne[1], bool(ligne[2]))

    def find_all(self):
        res = self._con.execute("SELECT id, title, completed FROM todos_tbl")
        for id_, title, completed in res.fetchall():
            yield Todo(id_, title, bool(completed))

    def fermer(self):
        self._con.close()
