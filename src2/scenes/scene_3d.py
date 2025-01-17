from src2.core.scene import Scene

from src2.entities.entity import Entity


from src2.core.render_layer import RenderLayer
from src2.core.viewport_container import ViewportContainer
from src2.core.viewport import Viewport
from src2.entities.camera import Camera
from src2.entities.point_light import PointLight
from src2.core.entity_group import EntityGroup
from src2.components.transform import Transform


class Scene3D(Scene):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.viewport_container_main = ViewportContainer(rect_pixels=(0, 0, *self.initial_window_size))
        self.viewport_container_shadow = ViewportContainer(rect_pixels=(0, 0, 2048, 2048))

        self.render_stage_order = [
            "forward",
            "selection",
            "overlay",
            "screen"
        ]

        self.entity_groups = {
            "default": EntityGroup(),
            "point_lights": EntityGroup(),
            "directional_lights": EntityGroup(),
            "gizmos": EntityGroup()
        }

        self.generate_render_stages()
        self.generate_render_layers()
        self.generate_gizmos()
        self.generate_lights()

    def generate_render_stages(self):

        self.render_stages["forward"] = RenderStageForward(
            ctx=self.ctx,
            ubos=self.ubos,
            initial_window_size=self.initial_window_size,
            shader_library=self.shader_library)

        self.render_stages["selection"] = RenderStageSelection(
            ctx=self.ctx,
            ubos=self.ubos,
            initial_window_size=self.initial_window_size,
            shader_library=self.shader_library)

        self.render_stages["overlay"] = RenderStageOverlay(
            ctx=self.ctx,
            ubos=self.ubos,
            initial_window_size=self.initial_window_size,
            shader_library=self.shader_library)

        screen_input_textures = {
            "forward/color": self.render_stages["forward"].textures["color"],
            "forward/normal": self.render_stages["forward"].textures["normal"],
            "forward/viewpos": self.render_stages["forward"].textures["viewpos"],
            "forward/entity_info": self.render_stages["forward"] .textures["entity_info"],
            "selection/color": self.render_stages["selection"].textures["color"],
            "overlay/color": self.render_stages["overlay"].textures["color"],
            "forward/depth": self.render_stages["forward"].textures["depth"]}

        self.render_stages["screen"] = RenderStageScreen(
            ctx=self.ctx,
            ubos=self.ubos,
            initial_window_size=self.initial_window_size,
            shader_library=self.shader_library,
            input_textures=screen_input_textures)

    def generate_render_layers(self):

        # Forward Stage Layers
        viewport = Viewport(rect_ratio=(0.0, 0.0, 1.0, 1.0))
        viewport.camera = Camera()
        viewport.camera.components["transform"] = Transform(params={"position": (0.0, 0.0, -5.0)})
        self.viewport_container_main.add_viewport(name="full_screen", viewport=viewport)
        self.render_stages["forward"].render_layers.append(RenderLayer(viewport=viewport))

    def generate_gizmos(self):
        pass

    def generate_lights(self):

        # Point lights
        point_light_group = EntityGroup()
        new_point_light = PointLight(params={"ubo_index": 0})
        new_point_light.components["transform"] = Transform(params={"position": (5, 5, 5)})
        point_light_group.entities["light_1"] = new_point_light
        self.entity_groups["point_lights"] = point_light_group

        # Directional Lights

    def attach_entity(self, entity_id: str, entity: Entity):
        self.entity_groups["default"].entities[entity_id] = entity

    def detach_entity(self, entity_id: str):
        self.entity_groups["default"].entities.pop(entity_id, None)

    def render(self):
        for render_stage_name in self.render_stage_order:
            self.render_stages[render_stage_name].render()
