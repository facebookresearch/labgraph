#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import dataclasses
import importlib
import pickle
from typing import Dict, Optional

import click

from .local_runner import LocalRunner
from .process_manager import ProcessManagerState
from .runner import BootstrapInfo, RunnerOptions
from .util import get_module_class


@click.command()
@click.option(
    "--module",
    type=str,
    help="The fully-qualified classname of the module to run",
    required=True,
)
@click.option(
    "--process-name",
    type=str,
    help="The name of the process in the ProcessManager state",
    required=True,
)
@click.option(
    "--stream-namespace",
    type=str,
    help="The namespace of the streams in the managed process",
)
@click.option(
    f"--{ProcessManagerState.SUBPROCESS_ARG}",
    type=str,
    help="The path to the ProcessManager state file",
)
@click.option(
    "--streams-file-path", type=str, help="The path to the stream file for the module"
)
@click.option(
    "--options-file-path", type=str, help="The path to the options file for the module"
)
@click.option(
    "--config-file-path", type=str, help="The path to the config file for the module"
)
@click.option(
    "--state-file-path", type=str, help="The path to the state file for the module"
)
def main(
    module: str,
    process_name: str,
    stream_namespace: Optional[str] = None,
    process_manager_state_file: Optional[str] = None,
    streams_file_path: Optional[str] = None,
    options_file_path: Optional[str] = None,
    config_file_path: Optional[str] = None,
    state_file_path: Optional[str] = None,
) -> None:
    assert (process_name is None) == (process_manager_state_file is None), (
        "Expected both or neither of --process-name and "
        f"--{ProcessManagerState.SUBPROCESS_ARG}"
    )

    # Get the Python class for the LabGraph module
    module_cls = get_module_class(*module.rsplit(".", 1))

    # Restore the config and state for the module
    config, state = None, None
    if config_file_path is not None:
        with open(config_file_path, "rb") as config_file:
            cls_path, config_dict = pickle.load(config_file)
        config = _load_cls(cls_path)(**config_dict)
        assert isinstance(config, module_cls.__config_type__)
    if state_file_path is not None:
        with open(state_file_path, "rb") as state_file:
            cls_path, state_dict = pickle.load(state_file)
        state = _load_cls(cls_path)(**state_dict)
        assert isinstance(state, module_cls.__state_type__)

    # Construct an instance of the module
    module_instance = module_cls(config=config, state=state)

    # Restore or create runner options
    if options_file_path is not None:
        with open(options_file_path, "rb") as options_file:
            options = pickle.load(options_file)
        assert isinstance(options, RunnerOptions)
    else:
        options = RunnerOptions()

    # Add bootstrap info to runner options
    if process_manager_state_file is not None:
        stream_ids_by_topic_path: Dict[str, str] = {}
        if streams_file_path is not None:
            with open(streams_file_path, "rb") as streams_file:
                stream_ids_by_topic_path = pickle.load(streams_file)
                assert isinstance(stream_ids_by_topic_path, dict)
        options = dataclasses.replace(
            options,
            bootstrap_info=BootstrapInfo(
                process_name=process_name,
                process_manager_state=ProcessManagerState.load(
                    process_manager_state_file
                ),
                stream_ids_by_topic_path=stream_ids_by_topic_path,
                stream_namespace=stream_namespace,
            ),
        )
    runner = LocalRunner(module=module_instance, options=options)
    runner.run()


def _load_cls(cls_path: str) -> type:
    module_path, cls_name = cls_path.rsplit(".", 1)
    cls = getattr(importlib.import_module(module_path), cls_name)
    assert isinstance(cls, type)
    return cls


if __name__ == "__main__":
    main()
