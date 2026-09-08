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
        # Paramètres liés (?) : sqlite se charge de l'échappement, quelle que
        # soit la valeur du titre. Jamais de f-string dans une requête.
        cur = self._con.execute(
            "INSERT INTO todos_tbl (title, completed) VALUES (?, ?)",
            (todo.title, todo.completed),
        )
        self._con.commit()
        todo.id = cur.lastrowid
        return todo

    def find_all(self):
        res = self._con.execute("SELECT id, title, completed FROM todos_tbl")
        for id_, title, completed in res.fetchall():
            # sqlite n'a pas de booléen : la colonne revient en 0/1.
            # Décision : la conversion est faite ici, Todo reste un simple dataclass.
            yield Todo(id_, title, bool(completed))

    def fermer(self):
        self._con.close()
