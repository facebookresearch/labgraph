from abc import ABCMeta, abstractmethod
from typing import TypeVar, List

T = TypeVar("T")

class BaseParser(metaclass=ABCMeta):
    """
    An abstraction for parsers
    """

    @abstractmethod
    def parse(self, code:str) -> List[T]:
        pass