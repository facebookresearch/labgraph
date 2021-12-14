#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from PyQt5 import QtCore, QtGui, QtMultimedia, QtMultimediaWidgets, QtWidgets


# Main window
class MainWindow(QtWidgets.QWidget):
    def __init__(
        self, keypress_callbacks: typing.Dict[int, typing.Callable[..., typing.Any]]
    ) -> None:
        super().__init__()
        self.keypress_callbacks = keypress_callbacks

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        callback = self.keypress_callbacks.get(event.key())
        if callback is not None:
            callback()


# Mixins
class QGraphicsItemWithHover(QtWidgets.QGraphicsItem):
    def __init__(self) -> None:
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.hoverEnterCallback = None
        self.hoverLeaveCallback = None
        self.hoverEnterCallAt = 0.0
        self.hoverLeaveCallAt = 0.0

    def setHoverEnterCallback(self, callback: typing.Callable[..., typing.Any]) -> None:
        self.hoverEnterCallback = callback

    def setHoverLeaveCallback(self, callback: typing.Callable[..., typing.Any]) -> None:
        self.hoverLeaveCallback = callback

    def setHoverEnterCallAt(self, call_at: float) -> None:
        self.hoverEnterCallAt = call_at

    def setHoverLeaveCallAt(self, call_at: float) -> None:
        self.hoverLeaveCallAt = call_at

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.hoverEnterCallback is not None:
            self.hoverEnterCallback(self.hoverEnterCallAt)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.hoverLeaveCallback is not None:
            self.hoverLeaveCallback(self.hoverLeaveCallAt)


class QObjectWithMediaContent(QtCore.QObject):
    def getMediaContent(self, filename: str) -> QtMultimedia.QMediaContent:
        return QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filename))


# Implementations
class QGraphicsRectItemWithHover(QtWidgets.QGraphicsRectItem, QGraphicsItemWithHover):
    pass


class QGraphicsVideoItemWithMediaContent(
    QtMultimediaWidgets.QGraphicsVideoItem, QObjectWithMediaContent
):
    pass


class QLabelWithPictureFromFilename(QtWidgets.QLabel):
    def setPictureFromFilename(self, filename: str) -> None:
        picture = QtGui.QPixmap(filename).scaled(self.width(), self.height())
        self.setPixmap(picture)


class QMediaPlayerWithMediaContent(QtMultimedia.QMediaPlayer, QObjectWithMediaContent):
    pass
