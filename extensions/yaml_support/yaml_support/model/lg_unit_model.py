#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from .base_model import BaseModel
from ..serializer.yaml_serializer import YamlSerializer
from ..enums.lg_units_enum import LabGraphBuiltinUnits
from typing import Dict, Union


MethodsType = Dict[str, Union[dict, list, str]]


class LabGraphUnitsModel(BaseModel):
    """
    Stores data related to a labgraph class
    """
    def __init__(self, name: str, base: str) -> None:
        """
        Args:
            name : The name of the class
            base : A LabGraph built-in unit
        """
        self.__name: str = name
        self.__base: str = base
        self.__members: Dict[str, str] = {}
        self.__methods: MethodsType = {}

    @property
    def name(self) -> str:
        return self.__name

    @property
    def base(self) -> str:
        return self.__base

    @property
    def members(self) -> Dict[str, str]:
        return self.__members

    @property
    def methods(self) -> MethodsType:
        return self.__methods

    def save(self, path: str) -> None:
        if self.base in (
            LabGraphBuiltinUnits.MESSAGE,
            LabGraphBuiltinUnits.CONFIG,
            LabGraphBuiltinUnits.STATE
        ):
            self.__save_message(path)

        elif self.base in (
            LabGraphBuiltinUnits.NODE,
            LabGraphBuiltinUnits.GROUP,
            LabGraphBuiltinUnits.GRAPH
        ):
            self.__save_module(path)

    def __save_message(self, file) -> None:
        YamlSerializer.serialize({
            f"{self.name}":
            {
                "type": self.base,
                "fields": self.members
            }
        }, file)

    def __save_module(self, file) -> None:

        obj = {
            f"{self.name}": {
                "type": self.base
            }
        }

        if "state" in self.members:
            obj[self.name]["state"] = self.members["state"]

        if "config" in self.members:
            obj[self.name]["config"] = self.members["config"]

        # inputs and outputs
        inputs = set()
        outputs = set()

        for method in self.methods:
            for subscriber in self.methods[method]["subscribers"]:
                inputs.add(self.members[subscriber])

            for publisher in self.methods[method]["publishers"]:
                outputs.add(self.members[publisher])

        obj[self.name]["inputs"] = list(inputs)
        obj[self.name]["outputs"] = list(outputs)

        if self.base in (
            LabGraphBuiltinUnits.GROUP,
            LabGraphBuiltinUnits.GRAPH
        ):
            if "OUTPUT" in self.members:
                obj[self.name]["outputs"] = [self.members["OUTPUT"]]

            if "connections" in self.methods:
                connections: Dict[str, str] = {
                    self.members[k]:
                    (self.members[v] if v != self.name else v)
                    for k, v in
                    self.methods["connections"]["return"]
                                ["connections_dict"].items()
                }

                obj[self.name]["connections"] = connections

        YamlSerializer.serialize(obj, file)
