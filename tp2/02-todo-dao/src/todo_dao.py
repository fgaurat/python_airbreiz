from todo import Todo
import sqlite3
from pprint import pprint


class TodoDAO:

    def __init__(self, db_file):
        self.db_file = db_file
        self._con = sqlite3.connect(db_file)

    def good_save(self, todo: Todo):
        cur = self._con.cursor()

        sql = f"""
            INSERT INTO todos_tbl (title,completed) 
            VALUES (?,?)
                
        """
        cur.execute(sql, (todo.title, todo.completed))

        self._con.commit()

    def bad_save(self, todo: Todo):
        cur = self._con.cursor()
        cur.execute(f"""
            INSERT INTO todos_tbl (title,completed) 
            VALUES ({todo.title},{todo.completed})
                
        """)
        self._con.commit()

    def creer_table(self):
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS todos_tbl (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT,
                completed INTEGER
            )
        """)
        self._con.commit()

    def find_all(self):
        """
        find_all c'est bien
        """
        # all = []
        cur = self._con.cursor()
        res = cur.execute("SELECT id,title,completed FROM todos_tbl")
        todos = res.fetchall()
        for t in todos:
            todo = Todo(*t)  # Todo(id=t[0],title=t[1],completed=t[2])
            yield todo
        #     all.append(todo)
        # return all

    def fermer(self):
        self._con.close()
