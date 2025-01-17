import numpy as np

from src.core.component import Component


class Collider(Component):

    """
    Colliders are components that will allow collision tobe detected between
    """

    _type = "collider"

    __slots__ = [
        "shape",
        "collision_layer",
        "radius"
    ]

    def __init__(self, parameters, system_owned=False):
        super().__init__(parameters=parameters, system_owned=system_owned)

        self.shape = Component.dict2string(input_dict=parameters, key="shape", default_value="sphere")

        # All shapes parameters
        self.radius = Component.dict2float(input_dict=parameters, key="roughness_factor", default_value=0.5)

        self.collision_layer = 0

    def ray_intersection(self, ray_origin: np.array, ray_direction: np.array) -> float:

        pass
