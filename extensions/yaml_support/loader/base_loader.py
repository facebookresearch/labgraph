from abc import ABCMeta, abstractstaticmethod


class BaseLoader(metaclass=ABCMeta):
    """
    An abstraction for file loaders
    """
    @abstractstaticmethod
    def load_from_file() -> str:
        pass
