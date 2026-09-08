from todo import Todo
import sqlite3
from pprint import pprint

from deco import do_log
class TodoDAO:
    


    def __init__(self,db_file):
       self.db_file = db_file
       self._con = sqlite3.connect(db_file)

    
    def save(self,todo:Todo):
        cur = self._con.cursor()
        cur.execute(f"""
            INSERT INTO todos_tbl (title,completed) 
            VALUES ('{todo.title}',{todo.completed})
                
        """)
        self._con.commit()

    @do_log('meslogs.log')    
    def find_all(self):
        """
        find_all c'est bien
        """
        # all = []
        cur = self._con.cursor()
        res = cur.execute("SELECT id,title,completed FROM todos_tbl")
        todos = res.fetchall()
        for t in todos:
            todo = Todo(*t)#Todo(id=t[0],title=t[1],completed=t[2]) 
            yield todo
        #     all.append(todo)
        # return all

    def __del__(self):
        self._con.close()