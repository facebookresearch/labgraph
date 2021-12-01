from abc import ABCMeta, abstractstaticmethod
from typing import Dict, Any


class BaseSerializer(metaclass=ABCMeta):
    """
    An abstraction for serializers.
    """
    @abstractstaticmethod
    def serialize(obj: Dict[str, Dict[str, Any]], path: str) -> None:
        """
        Serializes a dict and save it into a file
        Args:
            model : The model object to be serialized
            path  : The path of the file where the model should be stored.
        """
        pass
