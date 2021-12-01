from .base_loader import BaseLoader
from .errors.errors import PythonFileLoaderError
import os

class PythonFileLoader(BaseLoader):
    """
    Represents a python (.py) file loader    
    """
    
    @staticmethod
    def load_from_file(path:str) -> str:

        """
        Returns the content of a python (.py) file as a string

        Args:
            path: The path of the python (.py) file to be load
        """

        
        if not os.path.exists(path):
            raise PythonFileLoaderError(f"{path} file not found")

        if (not os.path.isfile(path)) or (not path.endswith('.py')):
            raise PythonFileLoaderError(f"{path} should be a .py file")


        with open(path, mode =  'r', encoding='utf8') as file:
            content = file.read()
            assert isinstance(content,str)
            return content
