from abc import ABC, abstractmethod


class CalcGeo(ABC):

    @property
    @abstractmethod
    def surface(self) -> float:
        ...
