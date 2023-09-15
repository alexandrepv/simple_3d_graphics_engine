import numpy as np

from ecs import constants
from ecs.components.component import Component


class PointLight(Component):

    __slots__ = [
        "position",
        "diffuse",
        "ambient",
        "specular",
        "intensity",
        "attenuation_coeffs",
        "active"
    ]

    _type = constants.COMPONENT_TYPE_SPOT_LIGHT

    def __init__(self, **kwargs):
        self.diffuse = kwargs.get("diffuse", (1.0, 1.0, 1.0))
        self.ambient = kwargs.get("ambient", (1.0, 1.0, 1.0))
        self.specular = kwargs.get("specular", (1.0, 1.0, 1.0))
        self.attenuation_coeffs = kwargs.get("attenuation_coeffs", (1.0, 0.09, 0.032))
        self.intensity = kwargs.get("intensity", 0.8)
        self.active = True
