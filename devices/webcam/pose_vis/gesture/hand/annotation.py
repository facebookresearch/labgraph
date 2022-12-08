#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import numpy as np
import matplotlib.pyplot as plt

from typing import Dict, List, Tuple
from json import JSONEncoder
from matplotlib.pyplot import Axes
from matplotlib.figure import Figure

Vector = np.ndarray(shape=(0, 3), dtype=float)

class NumpyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class Annotation():
    """
    Handles tracking of hand and gesture data
    """
    hands: List[np.ndarray] = []
    gestures: Dict[str, List[np.ndarray]] = {}

    def set_hand_vertices(self, hand_index: int, vertices: Vector) -> None:
        """
        Sets vertex data for a hand index. If the hand does not exist, it is created
        """
        if np.size(self.hands, axis=0) <= hand_index:
            self.hands.append(vertices)
        else:
            self.hands[hand_index] = vertices

    def clear_hand_vertices(self) -> None:
        """
        Clears all hand vertex data
        """
        self.hands.clear()

    def add_gesture_data(self, vertices: Vector, label: str) -> None:
        """
        Adds gesture data to the given label, if the label doesn't exist, it is created
        """
        if label not in self.gestures:
            self.gestures[label] = []
        self.gestures[label].append(vertices)

    def save_gestures(self, file_path: str) -> None:
        """
        Saves gesture data to the given file path. Must be a full path
        """
        with open(file_path, "w") as output:
            output.write(json.dumps(self.gestures, indent=4, cls=NumpyJSONEncoder))

    def load_gestures(self, file_path: str) -> None:
        """
        Loads gesture data from the given file path. Must be a full path
        """
        if os.path.exists(file_path):
            with open(file_path, "r") as _file:
                gestures: Dict = json.load(_file)
                for k, v in gestures.items():
                    self.gestures[k] = []
                    for vertex_list in v:
                        self.gestures[k].append(np.asarray(vertex_list))

    def guess_annotations(self, max_difference_value: float) -> List[Tuple[str, float]]:
        """
        Returns a list of labels and their difference values for each hand based on `max_difference_value`

        If no gesture is found, returns an empty string and the closest difference value
        """
        results: List[Tuple[str, float]] = []
        for hdx in range(len(self.hands)):
            differences: List[Tuple[str, float]] = []
            for label, vertices_list in self.gestures.items():
                for data_index in range(len(vertices_list)):
                    diff = 0.0
                    for indice in range(len(vertices_list[data_index])):
                        for i in range(len(vertices_list[data_index][indice])):
                            diff += abs(self.hands[hdx][indice][i] - vertices_list[data_index][indice][i])
                    differences.append((label, diff))
            differences.sort(key = lambda x: x[1])
            if len(differences) > 0 and differences[0][1] <= max_difference_value:
                results.append(differences[0])
            else:
                results.append(("", -1 if len(differences) == 0 else differences[0][1]))
        return results
    
    def configure_plot(self) -> Tuple[Figure, Axes]:
        """
        Configures a plot for plotting hand data
        """
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        return (fig, ax)

    def plot_hand(self, hand_index: int, ax: Axes, drawing_order: List[List[int]], bounds: Tuple[int, int], hand_scale: float = 1.0, xyz_order: Tuple[int, int, int] = (0, 1, 2), xyz_scale: Tuple[int, int, int] = (1, 1, 1)) -> None:
        """
        Plots hand data

        `drawing_order` must be a list of indice lists, where each indice is connected in order

        `bounds` is the size of the 3D scene

        `hand_scale` scales the raw hand data

        `xyz_order` allows switching which values are used for X, Y, and Z in the plot. `0` is X, `1` is Y, and `2` is Z

        `xyz_scale` scales the flipped X, Y, and Z values
        """
        ax.cla()
        ax.set_xlim3d(bounds[0], bounds[1])
        ax.set_ylim3d(bounds[0], bounds[1])
        ax.set_zlim3d(bounds[0], bounds[1])
        for indices in drawing_order:
            handx = np.empty(shape=0)
            handy = np.empty(shape=0)
            handz = np.empty(shape=0)
            for indice in indices:
                world_pos = self.hands[hand_index][indice] * hand_scale
                handx = np.append(handx, [world_pos[xyz_order[0]] * xyz_scale[0]], axis=0)
                handy = np.append(handy, [world_pos[xyz_order[1]] * xyz_scale[1]], axis=0)
                handz = np.append(handz, [world_pos[xyz_order[2]] * xyz_scale[2]], axis=0)
            ax.plot(handx, handy, handz)