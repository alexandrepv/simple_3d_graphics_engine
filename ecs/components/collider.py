import numpy as np
import moderngl

from ecs import constants
from ecs.components.component import Component
from ecs.math import intersection_3d


class Collider(Component):

    """
    Colliders are components that will allow collision tobe detected between
    """

    _type = "collision_body"

    __slots__ = [
        "shape",
        "layer",
        "radius"
    ]

    def __init__(self, parameters: dict):
        super().__init__(parameters=parameters)

        self.shape = Component.dict2string(input_dict=parameters, key="shape", default_value="sphere")

        # All shapes parameters
        self.radius = Component.dict2float(input_dict=parameters, key="roughness_factor", default_value=0.5)

        self.layer = 0

    def ray_intersection_boolean(self, ray_origin: np.array, ray_direction: np.array) -> bool:

        pass




