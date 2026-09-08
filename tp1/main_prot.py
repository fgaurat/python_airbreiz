from typing import Protocol

class Adder(Protocol):
    def add(self, x, y):
        pass

class IntAdder:
    def add(self, x, y):
        return x + yx

class StrAdder:
    def add(self, x, y):
        return str(x) + str(y)

def add(adder: Adder) -> None:
    print(adder.add(2, 3))

add(IntAdder()) # mypy: Success: no issues found in 1 source file
add(StrAdder()) # mypy: Success: no issues found in 1 source file