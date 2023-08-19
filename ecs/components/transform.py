import numpy as np
from core.math import mat4

from ecs.components.component import Component


class Transform(Component):

    _type = "transform"

    __slots__ = [
        "world_matrix",
        "local_matrix",
        "position",
        "rotation",
        "scale"
    ]

    def __init__(self, **kwargs):
        self.world_matrix = np.eye(4, dtype=np.float32)
        self.local_matrix = np.eye(4, dtype=np.float32)

        self.position = np.array(kwargs.get("position", (0, 0, 0)), dtype=np.float32)
        self.rotation = np.array(kwargs.get("rotation", (0, 0, 0)), dtype=np.float32)
        self.scale = kwargs.get("scale", 1.0)

    def update(self):

        # TODO: Add the _dirty_flag check to avoid unecessary updates
        self.local_matrix = mat4.compute_transform(position=self.position,
                                                   rotation_rad=self.rotation,
                                                   scale=self.scale)