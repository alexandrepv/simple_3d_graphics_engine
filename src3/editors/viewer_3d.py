import imgui
import moderngl
import struct
import copy
from glm import vec3

from src3 import constants
from src3.editors.editor import Editor
from src3.components.component_factory import ComponentFactory
from src3.entities.entity_factory import EntityFactory
from src3.gizmos.transform_gizmo import TransformGizmo
from src3.camera_3d import Camera3D  # Import the Camera class
from src3 import math_3d


class Viewer3D(Editor):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.window_size = (900, 600)
        self.fbo_size = (640, 480)
        self.program = self.shader_loader.get_program(shader_filename="basic.glsl")
        self.camera = Camera3D(fbo_size=self.fbo_size, position=vec3(0, 1, 5))

        self.component_factory = ComponentFactory(ctx=self.ctx, shader_loader=self.shader_loader)
        self.entity_factory = EntityFactory(ctx=self.ctx, shader_loader=self.shader_loader)

        # Fragment picking
        self.picker_program = self.shader_loader.get_program("fragment_picking.glsl")
        self.picker_buffer = self.ctx.buffer(reserve=3 * 4)  # 3 ints
        self.picker_vao = self.ctx.vertex_array(self.picker_program, [])
        self.picker_output = None
        self.image_mouse_x = 0
        self.image_mouse_y = 0
        self.image_mouse_y_opengl = copy.copy(self.fbo_size[1])
        self.texture_entity_info = self.ctx.texture(size=self.fbo_size, components=4, dtype='f4')
        self.texture_entity_info.filter = (moderngl.NEAREST, moderngl.NEAREST)  # No interpolation!
        self.selected_entity_id = -1

        self.fbo = self.ctx.framebuffer(
            color_attachments=[
                self.ctx.texture(self.fbo_size, 3),  # Main RGB color output that will be rendered to screen
                self.texture_entity_info
            ],
            depth_attachment=self.ctx.depth_texture(self.fbo_size),
        )

        self.imgui_renderer.register_texture(self.fbo.color_attachments[0])

        self.gizmo_3d = TransformGizmo(ctx=self.ctx, shader_loader=self.shader_loader, output_fbo=self.fbo)

        self.entities = {}

        # System-only entities
        self.renderable_entity_grid = None

    def setup(self) -> bool:

        self.entities[23] = self.entity_factory.create_renderable_3d_axis(axis_radius=0.05)
        return True

    def update(self, time: float, elapsed_time: float):
        self.camera.process_keyboard(elapsed_time)
        self.render_scene()
        self.render_gizmo()
        self.render_ui()

    def shutdown(self):
        for _, entity in self.entities.items():
            entity.release()

    def render_scene(self):

        # Setup mvp cameras
        self.program["m_proj"].write(self.camera.projection_matrix)
        self.program['m_view'].write(self.camera.view_matrix)

        # Setup lights
        self.program["light.position"].value = (10.0, 10.0, -10.0)
        self.program['light.position'].value = vec3(1.0, 1.0, 1.0)
        self.program['light.Ia'].value = vec3(0.2, 0.2, 0.2)
        self.program['light.Id'].value = vec3(0.5, 0.5, 0.5)
        self.program['light.Is'].value = vec3(1.0, 1.0, 1.0)
        self.program['camPos'].value = (0.0, 0.0, 3.0)

        self.fbo.use()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.fbo.clear()

        # Render renderable entities
        for entity_id, entity in self.entities.items():
            self.program["entity_id"].value = entity_id
            self.program['m_model'].write(entity.component_transform.world_matrix)
            entity.component_mesh.render(shader_program_name="basic.glsl")

    def render_gizmo(self):

        if self.selected_entity_id < 1:
            return

        self.gizmo_3d.render(
            view_matrix=self.camera.view_matrix,
            projection_matrix=self.camera.projection_matrix,
            entity_matrix=self.entities[self.selected_entity_id].component_transform.world_matrix,
            ray_origin=vec3(0, 0, 0),
            ray_direction=vec3(1, 0, 0))

    def render_ui(self):
        imgui.begin("Viewer 3D", True)
        imgui.set_window_size(self.window_size[0], self.window_size[1])

        # Left Column - Menus
        with imgui.begin_group():
            imgui.push_style_var(imgui.STYLE_FRAME_BORDERSIZE, 1.0)
            imgui.text("Entities")
            with imgui.begin_list_box("", 200, 100) as list_box:
                if list_box.opened:
                    imgui.selectable("Selected", True)
                    imgui.selectable("Not Selected", False)
            imgui.pop_style_var(1)

            imgui.text(f"Selected entity: {self.selected_entity_id}")

        imgui.same_line(spacing=20)

        # Right Column - 3D Scene
        with imgui.begin_group():
            texture_id = self.fbo.color_attachments[0].glo

            # Get the position where the image will be drawn
            image_pos = imgui.get_cursor_screen_pos()

            # NOTE: I'm using the uv0 and uv1 arguments to FLIP the image back vertically, as it is flipped by default
            imgui.image(texture_id, *self.fbo.size, uv0=(0, 1), uv1=(1, 0))

            # Check if the mouse is over the image and print the position
            if imgui.is_item_hovered():
                mouse_x, mouse_y = imgui.get_mouse_pos()

                # Calculate the mouse position relative to the image
                self.image_mouse_x = mouse_x - image_pos[0]
                self.image_mouse_y = mouse_y - image_pos[1]

                # Generate a 3D ray from the camera position
                ray_origin, ray_direction = self.camera.screen_to_world(self.image_mouse_x, self.image_mouse_y)

                collision = math_3d.intersect_ray_sphere_boolean(
                    ray_origin=ray_origin,
                    ray_direction=ray_direction,
                    sphere_origin=vec3(0, 0, 0),
                    sphere_radius=1.0)

                # DEBUG
                #print(f"Ray Origin: {ray_origin}, Ray Direction: {ray_direction}")
                #print(f"Collision: {collision}")

        imgui.end()

    def process_input(self, elapsed_time):
        io = imgui.get_io()

        if self.camera.right_mouse_button_down:
            self.camera.process_keyboard(elapsed_time)

    def get_entity_id(self, mouse_x, mouse_y) -> int:

        # The mouse positions are on the framebuffer being rendered, not the screen coordinates
        self.picker_program['texel_pos'].value = (int(mouse_x), int(mouse_y))  # (x, y)
        self.texture_entity_info.use(location=0)

        self.picker_vao.transform(
            self.picker_buffer,
            mode=moderngl.POINTS,
            vertices=1,
            first=0,
            instances=1)

        entity_id, instance_id, _ = struct.unpack("3i", self.picker_buffer.read())
        return entity_id

    def handle_event_mouse_button_press(self, event_data: tuple):
        button, x, y = event_data

        if button == constants.MOUSE_RIGHT:
            self.camera.right_mouse_button_down = True

        if button == constants.MOUSE_LEFT:
            # The framebuffer image is flipped on the y-axis, so we flip the coordinates as well
            image_mouse_y_opengl = self.fbo_size[1] - self.image_mouse_y
            entity_id = self.get_entity_id(mouse_x=self.image_mouse_x,
                                           mouse_y=image_mouse_y_opengl)
            self.selected_entity_id = -1 if entity_id < 0 else entity_id

    def handle_event_mouse_button_release(self, event_data: tuple):
        button, x, y = event_data
        if button == constants.MOUSE_RIGHT:
            self.camera.right_mouse_button_down = False

    def handle_event_keyboard_press(self, event_data: tuple):
        key, modifiers = event_data
        self.camera.handle_key_press(key)

    def handle_event_keyboard_release(self, event_data: tuple):
        key, modifiers = event_data
        self.camera.handle_key_release(key)

    def handle_event_mouse_double_click(self, event_data: tuple):
        print("Double click!")

    def handle_event_mouse_move(self, event_data: tuple):
        x, y, dx, dy = event_data

    def handle_event_mouse_drag(self, event_data: tuple):
        x, y, dx, dy = event_data
        if self.camera.right_mouse_button_down:
            self.camera.process_mouse_movement(dx=dx, dy=dy)
