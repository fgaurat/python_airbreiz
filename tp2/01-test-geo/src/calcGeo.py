from abc import ABCMeta,ABC,abstractmethod


class CalcGeo(metaclass=ABCMeta):

    # @property
    # def surface(self)->float | None:
    #     raise NotImplementedError('Hoooo et la surface ??? ')


    @property
    @abstractmethod
    def surface(self)->float | None:
        pass
