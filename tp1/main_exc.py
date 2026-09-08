
import os
import sys
import logging
from pprint import pprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main1():


    a = 50
    found = False
    for i in range(10):
        print(i)
        if i == a:
            found = True
            break
            
    if found:
        print("ok")
    else:
        print("ko")


    for i in range(10):
        print(i)
        if i == a:
            found = True
            break
    else:
        print("ok")



def div(a,b):
    return a/b

def call_div(a,b):
    r = 0
    try:
        print("OPEN LOG FILE")
        r = div(a,b)
    except ZeroDivisionError as e:
        print("Erreur dans call_div")
        raise e
    finally:
        print("CLOSE LOG FILE")

    return r

def main():
    try:

        a = 2
        b = 0
        c = call_div(a,b)
        print(c)
    except ZeroDivisionError as e: 
        print(e)
    except TypeError as e: 
        print(e)
    except Exception as e: 
        print("Exception",e)

    print("La suite du code")


if __name__=='__main__':
    main()
