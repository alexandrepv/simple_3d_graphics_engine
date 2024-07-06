from src3.components.mesh_component import MeshComponent
from src3.components.transform_component import TransformComponent
from src3.components.material_component import MaterialComponent
from src3.components.bezier_segment_component import BezierSegmentComponent
from src3.components.point_cloud_component import PointCloudComponent


class Entity:

    def __init__(self, archetype: str, component_list: list, label=None):
        self.label = label if isinstance(label, str) else "generic"
        self.archetype = archetype

        # Components
        self.component_transform = None
        self.component_material = None
        self.component_mesh = None
        self.component_point_cloud = None
        self.component_bezier_segment = None

        # Assign components
        for component in component_list:
            if isinstance(component, TransformComponent):
                self.component_transform = component
            elif isinstance(component, MaterialComponent):
                self.component_material = component
            elif isinstance(component, MeshComponent):
                self.component_mesh = component
            elif isinstance(component, PointCloudComponent):
                self.component_point_cloud = component
            elif isinstance(component, BezierSegmentComponent):
                self.component_bezier_segment = component

    def render(self):
        pass

    def update(self, elapsed_time: float):
        pass

    def release(self):

        # Go over every component (that starts with "comp_") and release it if not None
        for attr_name in dir(self):
            if not attr_name.startswith("comp_"):
                continue

            component = getattr(self, attr_name)
            if component is not None and hasattr(component, 'release'):
                component.release()
