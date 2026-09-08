
import os
import sys
import logging
from pprint import pprint
from todo_dao import TodoDAO
from todo import Todo
from rectangle import Rectangle
from cercle import Cercle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def main():
    r = Rectangle(2,3)
    r1 = Rectangle(2,3)
    r2 = Rectangle.build_from_str("2;3")


    if r==r1:
        print("ok")
    else:
        print("ko")



    print(Rectangle.get_cpt())
    print(r1.get_cpt())
    print(r2)


    # print(r)
    # print(r.longueur)
    # r.longueur = -12
    # print(r.longueur)

    # print(r.__dir__())
    # r.longeur = 34
    # r.toto=33


    # print(r.toto)
    # print(r.__dict__())




    l1 = [1,2,3,4]
    l2 = l1[:2] #copy() # copy.copy()

    l = [1,2,3,4]

    # l2 = map(lambda i:i*2,l)
    # l2 = [i*2 for i in l]

    ce = Cercle(2)

    print(ce.surface)

def main_1():


    dao = TodoDAO("tp1/todos.db")

    t1 = Todo(title="Sample Todo 1", completed=False)
    t2 = Todo(title="Sample Todo 2", completed=True)

    # dao.save(t1)
    # dao.save(t2)


    all =dao.find_all()
    print(dao.find_all.__doc__)
    print(dao.find_all.__name__)

    for todo in all:
        print(todo)




if __name__=='__main__':
    main()
