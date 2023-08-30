import numpy as np
from ecs.math import mat4
from ecs.math import mat3
from ecs import constants

from ecs.components.component import Component


class Transform2D(Component):

    _type = "transform"

    __slots__ = [
        "world_matrix",
        "local_matrix",
        "position",
        "rotation",
        "look_at_target",
        "scale"
    ]

    def __init__(self, **kwargs):

        self.world_matrix = np.eye(3, dtype=np.float32)
        self.local_matrix = np.eye(3, dtype=np.float32)

        self.position = np.array(kwargs.get("position", (0, 0)), dtype=np.float32)
        self.rotation = 0

        if self.look_at_target is not None:
            self.look_at_target = np.array(self.look_at_target, dtype=np.float32)

        self.scale = kwargs.get("scale", 1.0)

    def update(self):

        self.local_matrix = mat3.compute_transform(position=self.position,
                                                   rotation_rad=self.rotation,
                                                   scale=self.scale)