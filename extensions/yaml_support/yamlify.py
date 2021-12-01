from .model.lg_unit_model import LabGraphUnitsModel
from ._parser.lg_units_parser import LabGraphUnitsParser
from .loader.python_file_loader import PythonFileLoader
from typing import List
import ntpath
import os


def yamlify(python_file: str, yaml_file: str = "") -> None:
    """
    Takes .py file and parse it to .yaml file

    Args:
        python_file : The .py file path
        yml_file: The name of the YAML file to be created,
                  in case nothing is passed the output file
                  will have the same name as the input file
    """
    # loads python file
    loader = PythonFileLoader()
    code: str = loader.load_from_file(python_file)

    # parses python code
    lg_units_parser = LabGraphUnitsParser()
    lg_units: List[LabGraphUnitsModel] = lg_units_parser.parse(code)

    # stores parsed units into a YAML file
    if not yaml_file:
        yaml_file = f"{ntpath.basename(python_file)}"[:-3]

    # check if the file exists
    file = f'{os.path.abspath(f"yaml_outputs/{yaml_file}")}.yaml'

    if os.path.exists(file):
        os.remove(file)

    # saves all models
    for cls in lg_units:
        cls.save(file)

    return file
