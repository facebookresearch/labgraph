from typing import Any, Dict
from .base_serializer import BaseSerializer
import yaml
import os
import ntpath

class YamlSerializer(BaseSerializer):
    """
    Represents a YAML serializer
    """
    @staticmethod
    def serialize(obj:Dict[str,Dict[str,Any]], path:str)-> None:
        """
        Serializes a model and save it a YAML file (.yaml)
        """

        assert isinstance(obj,dict)
        assert isinstance(path, str)


        # name of the output directory
        output_dir = f"yaml_outputs"

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        with open(f"{output_dir}/{ntpath.basename(path)}",'a') as file:
            yaml.dump(obj, file, sort_keys=False)
            file.write('\n')



        