#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
import os
import pathlib
from extensions.yaml_support.labgraph_yaml_parser.loader.python_file_loader import PythonFileLoader
from extensions.yaml_support.labgraph_yaml_parser.loader.errors.errors import PythonFileLoaderError
from extensions.yaml_support.labgraph_yaml_parser._parser.lg_units_parser import LabGraphUnitsParser


class TestLabgraphYamlAPI(unittest.TestCase):

    def setUp(self) -> None:
        tests_code_dir: str = "tests_code"
        tests_dir: str = pathlib.Path(__file__).parent.absolute()
        self.tests_dir: str = os.path.join(tests_dir, tests_code_dir)

    def test_loader_load_from_file_success(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_py_code.py")
        loader = PythonFileLoader()
        loaded_code = '\n'.join(
            loader.load_from_file(local_dir).split('\n')[3:]
        )
        expected_code = """class MyClass:\n    pass\n"""
        self.assertMultiLineEqual(expected_code, loaded_code)

    def test_loader_load_from_file_not_exist_throw_exception(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_py_code_.py")
        loader = PythonFileLoader()
        with self.assertRaises(PythonFileLoaderError):
            loader.load_from_file(local_dir)

    def test_loader_load_from_file_file_type_wrong_throw_exception(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_py_code_.py1")
        loader = PythonFileLoader()
        with self.assertRaises(PythonFileLoaderError):
            loader.load_from_file(local_dir)

    def test_parser_parse_message_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_message.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyMessage"
        expected_base_name = "Message"
        expected_members_count = 2
        expected_methods_count = 0

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))

    def test_parser_parse_config_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_config.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyConfig"
        expected_base_name = "Config"
        expected_members_count = 3
        expected_methods_count = 0

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))

    def test_parser_parse_state_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_state.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyState"
        expected_base_name = "State"
        expected_members_count = 1
        expected_methods_count = 0

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))

    def test_parser_parse_node_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_node.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyNode"
        expected_base_name = "Node"
        expected_members_count = 2
        expected_methods_count = 1

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))

    def test_parser_parse_group_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_group.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyGroup"
        expected_base_name = "Group"
        expected_members_count = 4
        expected_methods_count = 2

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))

    def test_parser_parse_graph_unit(self) -> None:
        local_dir = os.path.join(self.tests_dir, "test_lg_unit_graph.py")
        loader = PythonFileLoader()
        code = loader.load_from_file(local_dir)
        lg_units_parser = LabGraphUnitsParser()
        lg_units = lg_units_parser.parse(code)

        expected_units_count = 1
        expected_unit_name = "MyGraph"
        expected_base_name = "Graph"
        expected_members_count = 2
        expected_methods_count = 3

        self.assertEqual(expected_units_count, len(lg_units))
        self.assertEqual(expected_unit_name, lg_units[0].name)
        self.assertEqual(expected_base_name, lg_units[0].base)
        self.assertEqual(expected_members_count, len(lg_units[0].members))
        self.assertEqual(expected_methods_count, len(lg_units[0].methods))


if __name__ == "__main__":
    unittest.main()
