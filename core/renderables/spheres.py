
import moderngl
import numpy as np
from moderngl_window.opengl.vao import VAO

from core.utilities import utils
from core.utilities.utils_decorators import hooked
from core.node import Node
from core.material import Material
from core.geometry_3d import shapes_3d


class Spheres(Node):
    """Render some simple spheres."""

    def __init__(
        self,
        positions,
        radius=0.01,
        color=(0.0, 0.0, 1.0, 1.0),
        rings=16,
        sectors=32,
        icon="\u008d",
        cast_shadow=False,
        **kwargs,
    ):
        """
        Initializer.
        :param positions: A numpy array of shape (F, N, 3) or (N, 3) containing N sphere positions for F time steps.
        :param radius: Radius of the spheres.
        :param color: Color of the spheres.
        :param rings: Longitudinal resolution.
        :param sectors: Latitudinal resolution.
        """
        if len(positions.shape) == 2:
            positions = positions[np.newaxis]
        assert len(positions.shape) == 3

        # Define a default material in case there is None.
        if isinstance(color, tuple) or len(color.shape) == 1:
            kwargs["material"] = kwargs.get("material", Material(color=color, ambient=0.2))
            self.sphere_colors = kwargs["material"].color
        else:
            assert color.shape[1] == 4 and positions.shape[1] == color.shape[0]
            self.sphere_colors = color

        super().__init__(icon=icon, **kwargs)

        self._sphere_positions = positions
        self.radius = radius

        self.vertices, self.faces = shapes_3d.create_sphere(radius=1.0, rings=rings, sectors=sectors)
        self.n_vertices = self.vertices.shape[0]
        self.n_spheres = self.sphere_positions.shape[1]

        self.draw_edges = False
        self._need_upload = True

        # Render passes.
        self.outline = True
        self.fragmap = True
        self.depth_prepass = True
        self.cast_shadow = cast_shadow

    @property
    def bounds(self):
        bounds = self.get_bounds(self.sphere_positions)
        bounds[:, 0] -= self.radius
        bounds[:, 1] += self.radius
        return bounds

    @property
    def current_bounds(self):
        bounds = self.get_bounds(self.current_sphere_positions)
        bounds[:, 0] -= self.radius
        bounds[:, 1] += self.radius
        return bounds

    @property
    def vertex_colors(self):
        if len(self._sphere_colors.shape) == 1:
            return np.full((self.n_spheres * self.n_vertices, 4), self._sphere_colors)
        else:
            return np.tile(self._sphere_colors, (self.n_vertices, 1))

    def color_one(self, index, color):
        new_colors = np.tile(np.array(self.material.color), (self.n_spheres, 1))
        new_colors[index] = color
        self.sphere_colors = new_colors

    @Node.color.setter
    def color(self, color):
        self.material.color = color
        self.sphere_colors = color
        self.redraw()

    @property
    def sphere_colors(self):
        if len(self._sphere_colors.shape) == 1:
            t = np.tile(np.array(self._sphere_colors), (self.n_spheres, 1))
            return t
        else:
            return self._sphere_colors

    @sphere_colors.setter
    def sphere_colors(self, color):
        if isinstance(color, tuple):
            color = np.array(color)
        self._sphere_colors = color
        self.redraw()

    @property
    def current_sphere_positions(self):
        idx = self.current_frame_id if self.sphere_positions.shape[0] > 1 else 0
        return self.sphere_positions[idx]

    @current_sphere_positions.setter
    def current_sphere_positions(self, positions):
        assert len(positions.shape) == 2
        idx = self.current_frame_id if self.sphere_positions.shape[0] > 1 else 0
        self.sphere_positions[idx] = positions
        self.redraw()

    @property
    def sphere_positions(self):
        return self._sphere_positions

    @sphere_positions.setter
    def sphere_positions(self, pos):
        if len(pos.shape) == 2:
            pos = pos[np.newaxis]
        self._sphere_positions = pos
        self.n_frames = len(self._sphere_positions)
        self.redraw()

    def on_frame_update(self):
        self.redraw()

    def redraw(self, **kwargs):
        self._need_upload = True

    @Node.once
    def make_renderable(self, ctx: moderngl.Context):
        self.prog = get_sphere_instanced_program()

        vs_path = "sphere_instanced_positions.vs.glsl"
        self.outline_program = get_outline_program(vs_path)
        self.depth_only_program = get_depth_only_program(vs_path)
        self.fragmap_program = get_fragmap_program(vs_path)

        self.vbo_vertices = ctx.buffer(self.vertices.astype("f4").tobytes())
        self.vbo_indices = ctx.buffer(self.faces.astype("i4").tobytes())

        self.vbo_instance_position = ctx.buffer(reserve=self.n_spheres * 12)
        self.vbo_instance_color = ctx.buffer(reserve=self.n_spheres * 16)

        self.vao = VAO()
        self.vao.buffer(self.vbo_vertices, "3f4", "in_position")
        self.vao.buffer(self.vbo_instance_position, "3f4/i", "instance_position")
        self.vao.buffer(self.vbo_instance_color, "4f4/i", "instance_color")
        self.vao.index_buffer(self.vbo_indices)

    def _upload_buffers(self):
        if not self.is_renderable or not self._need_upload:
            return
        self._need_upload = False
        self.vbo_instance_position.write(self.current_sphere_positions.astype("f4").tobytes())
        if len(self._sphere_colors.shape) > 1:
            self.vbo_instance_color.write(self._sphere_colors.astype("f4").tobytes())

    def render(self, camera, **kwargs):
        self._upload_buffers()

        prog = self.prog
        prog["radius"] = self.radius
        if len(self._sphere_colors.shape) == 1:
            prog["use_uniform_color"] = True
            prog["uniform_color"] = tuple(self._sphere_colors)
        else:
            prog["use_uniform_color"] = False
        prog["draw_edges"].value = 1.0 if self.draw_edges else 0.0
        prog["win_size"].value = kwargs["window_size"]
        prog["clip_control"].value = (0, 0, 0)

        self.set_camera_matrices(prog, camera, **kwargs)
        set_lights_in_program(
            prog,
            kwargs["lights"],
            kwargs["shadows_enabled"],
            kwargs["ambient_strength"],
        )
        utils.set_material_properties(prog, self.material)
        self.receive_shadow(prog, **kwargs)
        self.vao.render(prog, moderngl.TRIANGLES, instances=self.n_spheres)

    def render_positions(self, prog):
        if self.is_renderable:
            self._upload_buffers()
            prog["radius"] = self.radius
            self.vao.render(prog, moderngl.TRIANGLES, instances=self.n_spheres)

    def gui(self, imgui):
        _, self.radius = imgui.drag_float("Radius", self.radius, 0.01, min_value=0.001, max_value=10.0, format="%.3f")
        super().gui(imgui)

    @hooked
    def release(self):
        if self.is_renderable:
            self.vao.release()