from typed_ast import ast3
from .base_parser import BaseParser
from extensions.yaml_support.yaml_support.model.lg_unit_model import (LabGraphUnitsModel)
from extensions.yaml_support.yaml_support.enums.lg_units_enum import LabGraphBuiltinUnits

from typed_ast.ast3 import (
    AsyncFunctionDef,
    NodeVisitor,
    ClassDef,
    Module,
    FunctionDef,
    Assign,
    AnnAssign,
)
from typing import TypeVar, Generic, List, Dict


T = TypeVar("T")


class LabGraphUnitsParser(BaseParser, NodeVisitor, Generic[T]):
    """
    Parses the LabGraph classes
    """
    def __init__(self, element_type: T = LabGraphBuiltinUnits):
        super().__init__()
        self.__classes: List[element_type] = []

    def parse(self, code: str) -> List[T]:
        ast = ast3.parse(code)
        self.visit(ast)
        return self.__classes

    def visit_Module(self, node) -> None:
        assert isinstance(node, Module)
        for child in node.body:
            self.visit(child)

    def visit_ClassDef(self, node) -> None:
        assert isinstance(node, ClassDef)

        # finds the type of the base class
        if len(node.bases):
            base_type: str = self.__construct_type(node.bases[0], '')
            base_type = base_type.split('.')[-1]

        # checks if the class is a LabGraph builtin unit.
        if (
            node.bases and
            base_type in set(unit.value for unit in LabGraphBuiltinUnits)
        ):
            class_model = LabGraphUnitsModel(node.name, base_type)
            for child in node.body:
                # case of members defined using annotation
                if isinstance(child, AnnAssign):
                    # member name & type
                    name: str = child.target.id
                    type: str = ''

                    if(hasattr(child.annotation, 'id')):
                        type = child.annotation.id

                    elif(hasattr(child.annotation, 'value')):
                        type = self.__construct_type(child.annotation, type)

                    class_model.members[name] = type

                # case of a class member defined using assign operator
                elif isinstance(child, Assign):
                    target_id = child.targets[0].id
                    class_model.members[target_id] = child.value.args[0].id

                # case of a method
                elif isinstance(child, (FunctionDef, AsyncFunctionDef)):
                    # argument type
                    arguments_info = list()
                    for arg in child.args.args:
                        if arg.arg == "self":
                            continue

                        argument_info = {}
                        argument_info['name'] = arg.arg

                        if arg.annotation is not None:
                            type: str = self.__construct_type(
                                arg.annotation,
                                ''
                            )
                            argument_info['type'] = type

                        arguments_info.append(argument_info)

                    # return type & data
                    return_info = {}
                    type: str = ''

                    # checks for connections
                    # this is specific for Groups & Graphs
                    if child.name == "connections":
                        connections: List[str] = []
                        # construct a list of connections
                        for _child in child.body:
                            if hasattr(_child, 'value'):
                                for elts in _child.value.elts:
                                    for elt in elts.elts:
                                        type = self.__construct_type(elt, '')
                                        connections.append(type)

                        # transform the list of connections to a dict
                        # each connection is represented as key-value
                        connections_dict: Dict[str, str] = {}
                        _iter = iter(connections)
                        for value in _iter:
                            key = value.split('.')[1]
                            value = next(_iter).split('.')[1]

                            if value != 'OUTPUT':
                                connections_dict[key] = value
                            else:
                                connections_dict[key] = node.name

                        return_info['connections_dict'] = connections_dict

                    # checks for publisher & subscriber decorators
                    publishers: List[str] = []
                    subscribers: List[str] = []
                    for decorator in child.decorator_list:
                        if hasattr(decorator, 'func'):
                            decorator_type: str = self.__construct_type(
                                                            decorator.func,
                                                            ''
                                                        )
                            decorator_type = decorator_type.split('.')[-1]

                            if decorator_type in 'publisher':
                                arg_type: str = self.__construct_type(
                                                            decorator.args[0],
                                                            ''
                                                        )
                                publishers.append(arg_type)

                            elif decorator_type in 'subscriber':
                                arg_type: str = self.__construct_type(
                                                            decorator.args[0],
                                                            ''
                                                        )
                                subscribers.append(arg_type)

                    if(hasattr(child.returns, 'value')):
                        type = self.__construct_type(child.returns, type)
                        return_info['type'] = type

                    class_model.methods[child.name] = {
                        "args": arguments_info,
                        "return": return_info,
                        "publishers": publishers,
                        "subscribers": subscribers
                    }

            assert isinstance(class_model, LabGraphUnitsModel)
            self.__classes.append(class_model)
            self.generic_visit(node)

    def __construct_type(self, value, type):
        """
        Recursive method that helps to construct a string
        that represents a complex datatype of a class member or a method

        Args:
            type : The final string we are trying to construct recursivaly
            value : An object that contains data about
                    the type of the class member/method
        """
        if hasattr(value, 'attr'):
            type = f"{self.__construct_type(value.value,type)}.{value.attr}"

        elif hasattr(value, 'elts'):
            type = f"{self.__construct_type(value.elts[0], type)}{f'.{type}' if type else ''}"

        elif hasattr(value, 'id'):
            return value.id

        elif isinstance(value, str):
            return value

        elif hasattr(value, 'slice'):
            type = f"{self.__construct_type(value.value, type)}.{self.__construct_type(value.slice, type)}{f'.{type}' if type else ''}"

        elif hasattr(value, 'value'):
            type = f"{self.__construct_type(value.value,type)}{f'.{type}' if type else ''}"

        return type
