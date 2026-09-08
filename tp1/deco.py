

from functools import wraps
def do_log(log_file):

    def decorator(func):

        @wraps(func)
        def wrap(*args,**kwargs):
            print(args,kwargs)
            print(log_file,"wrap de doLog",func)
            print("avant")
            r = func(*args,**kwargs)
            print("après")

            yield from  r

        return wrap
    return decorator
