import glfw
import moderngl
from PIL import Image
import numpy as np
import struct

from ecs import constants
from ecs.systems.system import System
from ecs.systems.render_system.shader_program_library import ShaderProgramLibrary
from ecs.systems.render_system.font_library import FontLibrary
from ecs.component_pool import ComponentPool
from ecs.geometry_3d import ready_to_render
from ecs.math import mat4


class RenderSystem(System):

    _type = "render_system"

    __slots__ = [
        "ctx",
        "buffer_size",
        "shader_program_library",
        "font_library",
        "framebuffers",
        "textures_offscreen_rendering",
        "textures_font",
        "vbo_groups",
        "quads",
        "fullscreen_selected_texture",
        "picker_buffer",
        "picker_program",
        "picker_output",
        "picker_vao",
        "outline_program",
        "outline_texture",
        "outline_framebuffer",
        "selected_entity_id",
        "shadow_map_program",
        "shadow_map_depth_texture",
        "shadow_map_framebuffer",
        "_sample_entity_location"
    ]

    def __init__(self, **kwargs):
        super().__init__(logger=kwargs["logger"])

        self.ctx = kwargs["context"]
        self.buffer_size = kwargs["buffer_size"]
        self.shader_program_library = ShaderProgramLibrary(context=self.ctx, logger=kwargs["logger"])
        self.font_library = FontLibrary(logger=kwargs["logger"])

        # Internal components (different from normal components)
        self.framebuffers = {}
        self.textures_offscreen_rendering = {}
        self.textures_font = {}
        self.vbo_groups = {}
        self.quads = {}

        self.fullscreen_selected_texture = 0  # Color is selected by default

        # Fragment Picking - altogether for now
        self.picker_buffer = None
        self.picker_program = None
        self.picker_output = None
        self.picker_vao = None

        # Outline drawing
        self.outline_program = None
        self.outline_texture = None
        self.outline_framebuffer = None

        self.selected_entity_id = -1

        # Shadow Mapping
        self.shadow_map_program = None
        self.shadow_map_depth_texture = None
        self.shadow_map_framebuffer = None

        # Flags
        self._sample_entity_location = None

    # =========================================================================
    #                         System Core functions
    # =========================================================================

    def initialise(self, **kwargs):

        # Fragment picking
        self.picker_program = self.shader_program_library["fragment_picking"]
        self.picker_buffer = self.ctx.buffer(reserve=3 * 4)  # 3 ints
        self.picker_vao = self.ctx.vertex_array(self.picker_program, [])

        # Offscreen rendering
        self.textures_offscreen_rendering["color"] = self.ctx.texture(size=self.buffer_size, components=4)
        self.textures_offscreen_rendering["normal"] = self.ctx.texture(size=self.buffer_size, components=4, dtype='f4')
        self.textures_offscreen_rendering["viewpos"] = self.ctx.texture(size=self.buffer_size, components=4, dtype='f4')
        self.textures_offscreen_rendering["entity_info"] = self.ctx.texture(size=self.buffer_size, components=4, dtype='f4')
        self.textures_offscreen_rendering["entity_info"].filter = (moderngl.NEAREST, moderngl.NEAREST)  # No interpolation!
        self.textures_offscreen_rendering["depth"] = self.ctx.depth_texture(size=self.buffer_size)
        self.framebuffers["offscreen"] = self.ctx.framebuffer(
            color_attachments=[
                self.textures_offscreen_rendering["color"],
                self.textures_offscreen_rendering["normal"],
                self.textures_offscreen_rendering["viewpos"],
                self.textures_offscreen_rendering["entity_info"]
            ],
            depth_attachment=self.textures_offscreen_rendering["depth"],
        )

        # Fonts
        for font_name, font in self.font_library.fonts.items():
            self.textures_font[font_name] = self.ctx.texture(size=font.texture_data.shape,
                                                             data=font.texture_data.astype('f4').tobytes(),
                                                             components=1,
                                                             dtype='f4')

        # Selection Pass
        self.textures_offscreen_rendering["selection"] = self.ctx.texture(size=self.buffer_size,
                                                                          components=4,
                                                                          dtype='f4')
        self.textures_offscreen_rendering["selection"].filter = (moderngl.NEAREST, moderngl.NEAREST)  # No interpolation!
        self.textures_offscreen_rendering["selection_depth"] = self.ctx.depth_texture(size=self.buffer_size)
        self.framebuffers["selection_fbo"] = self.ctx.framebuffer(
            color_attachments=[
                self.textures_offscreen_rendering["selection"],
            ],
            depth_attachment=self.textures_offscreen_rendering["selection_depth"],
        )

        # Shadow mapping
        self.shadow_map_program = self.shader_program_library["shadow_mapping"]
        self.shadow_map_depth_texture = self.ctx.depth_texture(size=self.buffer_size)
        self.shadow_map_framebuffer = self.ctx.framebuffer(depth_attachment=self.shadow_map_depth_texture)

        # Setup fullscreen quad textures
        self.quads["fullscreen"] = ready_to_render.quad_2d(context=self.ctx,
                                                           program=self.shader_program_library["screen_quad"])

        return True

    def update(self, elapsed_time: float, component_pool: ComponentPool, context: moderngl.Context, event=None):

        # Initialise object on the GPU if they haven't been already

        # TODO: Move initialisation to only when objects are created
        for entity_uid, renderable in component_pool.renderable_components.items():

            mesh = component_pool.mesh_components[entity_uid]
            mesh.initialise_on_gpu(ctx=self.ctx)
            renderable.initialise_on_gpu(ctx=self.ctx,
                                         program_name_list=constants.SHADER_PASSES_LIST,
                                         shader_library=self.shader_program_library,
                                         vbo_tuple_list=mesh.get_vbo_declaration_list(),
                                         ibo_faces=mesh.ibo_faces)

        camera_entity_uids = list(component_pool.camera_components.keys())

        # DEBUG -HACK TODO: MOVE THIS TO THE TRANSFORM SYSTEM!!!
        for _, transform in component_pool.transform_3d_components.items():
            transform.update()

        # Every Render pass operates on the OFFSCREEN buffers only
        for camera_uid in camera_entity_uids:

            self.forward_pass(component_pool=component_pool,
                              camera_uid=camera_uid)
            self.selected_entity_pass(component_pool=component_pool,
                                      camera_uid=camera_uid,
                                      selected_entity_uid=self.selected_entity_id)
            self.shadow_mapping_pass(component_pool=component_pool)
            self.text_2d_pass(component_pool=component_pool)

        # Final pass renders everything to a full screen quad from the offscreen textures
        self.render_to_screen()

    def on_event(self, event_type: int, event_data: tuple):

        if event_type == constants.EVENT_WINDOW_RESIZE:
            # TODO: Safe release all offscreen framebuffers and create new ones
            pass

        if (event_type == constants.EVENT_MOUSE_BUTTON_PRESS and
                event_data[constants.EVENT_INDEX_MOUSE_BUTTON_BUTTON] == glfw.MOUSE_BUTTON_LEFT):

            # TODO: Move this to its own function!
            # Pass the coordinate of the pixel you want to sample to the fragment picking shader
            self.picker_program['texel_pos'].value = event_data[constants.EVENT_INDEX_MOUSE_BUTTON_X:]  # (x, y)
            self.textures_offscreen_rendering["entity_info"].use(location=0)

            self.picker_vao.transform(
                self.picker_buffer,
                mode=moderngl.POINTS,
                vertices=1,
                first=0,
                instances=1)
            self.selected_entity_id, instance_id, _ = struct.unpack("3i", self.picker_buffer.read())

        # FULLSCREEN VIEW MODES
        if event_type == constants.EVENT_KEYBOARD_PRESS:
            key_value = event_data[constants.EVENT_INDEX_KEYBOARD_KEY]
            if glfw.KEY_F1 <= key_value <= glfw.KEY_F11:
                self.fullscreen_selected_texture = key_value - glfw.KEY_F1

    def shutdown(self):

        # Release textures
        for texture_name, texture_obj in self.textures_offscreen_rendering.items():
            texture_obj.release()

        # Release Framebuffers
        for frabuffer_name, framebuffer_obj in self.framebuffers.items():
            framebuffer_obj.release()

        for quad_name, quad in self.quads.items():
            if quad["vbo_vertices"] is not None:
                quad["vbo_vertices"].release()

            if quad["vbo_uvs"] is not None:
                quad["vbo_uvs"].release()

            if quad["vao"] is not None:
                quad["vao"].release()

        self.shader_program_library.shutdown()
        self.font_library.shutdown()

    # =========================================================================
    #                         Render functions
    # =========================================================================

    def forward_pass(self, component_pool: ComponentPool, camera_uid: int):

        # IMPORTANT: You MUST have called scene.make_renderable once before getting here!
        self.framebuffers["offscreen"].use()

        camera_component = component_pool.camera_components[camera_uid]
        camera_transform = component_pool.transform_3d_components[camera_uid]

        # Clear context (you need to use the use() first to bind it!)
        self.ctx.clear(
            red=1,
            green=1,
            blue=1,
            alpha=1.0,
            depth=1.0,
            viewport=camera_component.viewport)

        # Prepare context flags for rendering
        self.ctx.enable_only(moderngl.DEPTH_TEST | moderngl.BLEND | moderngl.CULL_FACE)  # Removing has no effect? Why?
        self.ctx.cull_face = "back"
        self.ctx.blend_func = (
            moderngl.SRC_ALPHA,
            moderngl.ONE_MINUS_SRC_ALPHA,
            moderngl.ONE,
            moderngl.ONE)

        program = self.shader_program_library[constants.SHADER_PROGRAM_FORWARD_PASS]
        program["view_matrix"].write(camera_transform.local_matrix.T.astype('f4').tobytes())

        #directional_light_components = list(component_pool.directional_light_components.keys())

        camera_transform.update()
        camera_component.upload_uniforms(program=program)

        for uid, renderable_component in component_pool.renderable_components.items():

            if not renderable_component.visible:
                continue

            # Set entity ID
            program[constants.SHADER_UNIFORM_ENTITY_ID] = uid
            renderable_transform = component_pool.transform_3d_components[uid]

            material = component_pool.material_components.get(uid, None)

            # Upload uniforms
            program["entity_id"].value = uid
            program["model_matrix"].write(renderable_transform.local_matrix.T.tobytes())

            if material is not None:
                program["material_diffuse_color"].write = np.array((*material.diffuse, material.alpha), dtype=np.float32).tobytes()
                #program["material_ambient_factor"] = material.ambient
                #program["material_specular_factor"] = material.specular

            # Render the vao at the end
            renderable_component.vaos[constants.SHADER_PROGRAM_FORWARD_PASS].render(moderngl.TRIANGLES)

            # Stage: Draw transparent objects back to front

    def selected_entity_pass(self, component_pool: ComponentPool, camera_uid: int, selected_entity_uid: int):

        # IMPORTANT: It uses the current bound framebuffer!

        self.framebuffers["selection_fbo"].use()
        camera_component = component_pool.camera_components[camera_uid]
        self.ctx.clear(depth=1.0, viewport=camera_component.viewport)

        # TODO: Numbers between 0 and 1 are background colors, so we assume they are NULL selection
        if selected_entity_uid is None or selected_entity_uid <= 1:
            return

        program = self.shader_program_library[constants.SHADER_PROGRAM_SELECTED_ENTITY_PASS]
        camera_transform = component_pool.transform_3d_components[camera_uid]
        renderable_transform = component_pool.transform_3d_components[selected_entity_uid]
        camera_transform.update()

        # Upload uniforms
        camera_component.upload_uniforms(program=program)
        program["view_matrix"].write(camera_transform.local_matrix.T.tobytes())
        program["model_matrix"].write(renderable_transform.local_matrix.T.tobytes())

        # Render
        renderable_component = component_pool.renderable_components[selected_entity_uid]
        renderable_component.vaos[constants.SHADER_PROGRAM_SELECTED_ENTITY_PASS].render(moderngl.TRIANGLES)

    def text_2d_pass(self, component_pool: ComponentPool):

        if len(component_pool.text_2d_components) == 0:
            return

        self.framebuffers["offscreen"].use()
        self.ctx.disable(moderngl.DEPTH_TEST)

        # Upload uniforms TODO: Move this to render system
        projection_matrix = mat4.orthographic_projection(
            left=0,
            right=self.buffer_size[0],
            bottom=self.buffer_size[1],
            top=0,
            near=-1,
            far=1)

        # Upload uniforms
        program = self.shader_program_library[constants.SHADER_PROGRAM_TEXT_2D]
        program["projection_matrix"].write(projection_matrix.T.tobytes())

        # Update VBOs and render text
        for _, text_2d in component_pool.text_2d_components.items():

            # State Updates
            text_2d.initialise_on_gpu(ctx=self.ctx, shader_library=self.shader_program_library)
            text_2d.update_buffer(font_library=self.font_library)

            # Rendering
            self.textures_font[text_2d.font_name].use(location=0)
            text_2d.vao.render(moderngl.POINTS)

    def shadow_mapping_pass(self, component_pool: ComponentPool):

        self.shadow_map_framebuffer.clear()
        self.shadow_map_framebuffer.use()

        program = self.shader_program_library[constants.SHADER_PROGRAM_SHADOW_MAPPING_PASS]

        #directional_lights_uids = self.

        for uid, renderable_component in component_pool.renderable_components.items():

            if not renderable_component.visible:
                continue

            renderable_transform = component_pool.transform_3d_components[uid]
            program["model_matrix"].write(renderable_transform.local_matrix.T.astype('f4').tobytes())

    def render_to_screen(self) -> None:

        """
        Renders selected offscreen texture to window. By default, it is the color texture, but you can
        change it using F1-F12 keys.
        :return: None
        """

        self.ctx.screen.use()
        self.ctx.screen.clear(red=1, green=1, blue=1)  # TODO: Check if this line is necessary
        self.ctx.disable(moderngl.DEPTH_TEST)

        self.textures_offscreen_rendering["color"].use(location=0)
        self.textures_offscreen_rendering["normal"].use(location=1)
        self.textures_offscreen_rendering["viewpos"].use(location=2)
        self.textures_offscreen_rendering["entity_info"].use(location=3)
        self.textures_offscreen_rendering["selection"].use(location=4)

        quad_vao = self.quads["fullscreen"]['vao']
        quad_vao.program["selected_texture"] = self.fullscreen_selected_texture
        quad_vao.render(moderngl.TRIANGLES)

    # =========================================================================
    #                         Other Functions
    # =========================================================================

    # Release framebuffers if they already exist.
    def safe_release(self, buffer: moderngl.Buffer):
        if buffer is not None:
            buffer.release()

    def load_texture_from_file(self, texture_fpath: str, texture_id: str, datatype="f4"):
        if texture_id in self.textures_offscreen_rendering:
            raise KeyError(f"[ERROR] Texture ID '{texture_id}' already exists")

        image = Image.open(texture_fpath)
        image_data = np.array(image)
        self.textures_offscreen_rendering[texture_id] = self.ctx.texture(size=image.size,
                                                                         components=image_data.shape[-1],
                                                                         data=image_data.tobytes())
