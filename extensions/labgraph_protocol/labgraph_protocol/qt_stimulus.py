#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import operator
import typing
from collections.abc import Iterable
from dataclasses import dataclass, field

from labgraph_protocol import qt_widgets
from labgraph_protocol.stimulus import Stimulus
from PyQt5 import QtMultimedia, QtMultimediaWidgets, QtWidgets


CALLBACKS_T = typing.List[typing.Tuple[str, typing.Any]]
KNOWN_MEMBERS = ["widget", "player"]


@dataclass
class Deferred:
    """
    Special case used for specifying stimulus attributes in callbacks.
    If args are provided, named function is called with these args and applied.
    """

    name: typing.Union[str, typing.Callable[..., typing.Any]]
    args: typing.Any = None
    unpack: bool = False


@dataclass
class QtStimulus(Stimulus):
    qt_type: str
    callbacks: CALLBACKS_T = field(default_factory=list, compare=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.widget = None
        self.player = None
        self.parent = None

    def _get_widget_type(self) -> QtWidgets.QWidget:
        widget_type = getattr(qt_widgets, self.qt_type, None)
        if widget_type is None:
            widget_type = getattr(QtMultimediaWidgets, self.qt_type, None)
        if widget_type is None:
            widget_type = getattr(QtMultimedia, self.qt_type, None)
        if widget_type is None:
            widget_type = getattr(QtWidgets, self.qt_type)
        return widget_type

    def _get_resolved_func(self, funcname: str) -> typing.Callable[..., typing.Any]:
        if funcname.split(".", 1)[0] not in KNOWN_MEMBERS:
            if self.widget is not None:
                funcname = f"widget.{funcname}"
            elif self.player is not None:
                funcname = f"player.{funcname}"
        return operator.attrgetter(funcname)(self)

    def _get_resolved_arg(self, arg: typing.Any) -> typing.Any:
        if isinstance(arg, Deferred):
            if isinstance(arg.name, str):
                attr = operator.attrgetter(arg.name)(self)
            else:
                attr = arg.name
            if callable(attr) and arg.args is not None:
                return self._call_func(attr, arg.args)
            else:
                return attr
        elif isinstance(arg, str) or not isinstance(arg, Iterable):
            return arg
        elif isinstance(arg, dict):
            return {name: self._get_resolved_arg(value) for name, value in arg.items()}
        else:
            return [self._get_resolved_arg(value) for value in arg]

    def _call_func(
        self, func: typing.Callable[..., typing.Any], args: typing.Any
    ) -> typing.Any:
        if isinstance(args, str) or not isinstance(args, Iterable):
            args = (args,)
        if isinstance(args, dict):
            resolved_args = {}
            for name, arg in args.items():
                resolved_args[name] = self._get_resolved_arg(arg)
            return func(**resolved_args)
        else:
            resolved_args = []
            for arg in args:
                resolved_arg = self._get_resolved_arg(arg)
                if isinstance(arg, Deferred) and arg.unpack:
                    resolved_args.extend(resolved_arg)
                else:
                    resolved_args.append(resolved_arg)
            return func(*resolved_args)

    def setup(self, view: QtWidgets.QGraphicsView) -> None:
        widget_type = self._get_widget_type()
        if issubclass(widget_type, QtWidgets.QGraphicsItem):
            self.widget = widget_type()
            view.scene().addItem(self.widget)
            if issubclass(widget_type, QtMultimediaWidgets.QGraphicsVideoItem):
                self.player = QtMultimedia.QMediaPlayer(parent=view)
                self.player.setVideoOutput(self.widget)
        elif issubclass(widget_type, QtMultimedia.QMediaPlayer):
            self.player = widget_type(parent=view)
        else:
            self.widget = widget_type(parent=view)
        self.parent = view
        for funcname, args in self.callbacks:
            func = self._get_resolved_func(funcname)
            self._call_func(func, args)

    def enable(self) -> None:
        if self.widget is not None:
            self.widget.show()
        if self.player is not None:
            self.player.play()

    def disable(self) -> None:
        if self.widget is not None:
            self.widget.hide()
        if self.player is not None:
            self.player.pause()

    def teardown(self, event: typing.Any = None) -> None:
        self.player = None
        self.widget = None
        self.parent = None
