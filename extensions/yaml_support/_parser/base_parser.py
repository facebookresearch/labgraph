from abc import ABCMeta, abstractmethod
from typing import List, Any


class BaseParser(metaclass=ABCMeta):
    """
    An abstraction for parsers
    """

    @abstractmethod
    def parse(self, code:str) -> List[Any]:
        raise NotImplementedError()