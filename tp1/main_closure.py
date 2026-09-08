
import os
import sys
import logging
from pprint import pprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def make_incrementor(n):

    def the_function(v):
        return n+v

    return the_function

def main():
    do_inc = make_incrementor(10)
    r = do_inc(5)
    print(r) # 15

if __name__=='__main__':
    main()
