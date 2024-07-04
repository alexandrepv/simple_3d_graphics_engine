from typing import Any
import moderngl
import numpy as np
from src3 import constants
from glm import vec3, vec4, mat4, length, length2, inverse, translate, scale, dot, normalize
import copy

from src3.gizmos.gizmo import Gizmo
from src3 import math_3d
from src3.shader_loader import ShaderLoader
from src3.mesh_factory_3d import MeshFactory3D


class BezierGizmo(Gizmo):

    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)

        self.active_handle_index = -1
        self.handle_world_matrix = mat4(1.0)

        self.handle_triangles_vbo = None
        self.handle_triangles_vao = None
        self.handle_triangles_highlight_vbo = None
        self.handle_triangles_highlight_vao = None

    def generate_vbos_and_vaos(self):

        center_data = self.generate_center_vertex_data(
            radius=constants.GIZMO_CENTER_RADIUS,
            color=(0.7, 0.7, 0.7, constants.GIZMO_ALPHA))
        self.handle_triangles_vbo = self.ctx.buffer(center_data.tobytes())
        self.handle_triangles_vao = self.ctx.vertex_array(
            self.program_triangles,
            [
                (self.handle_triangles_vbo, '3f 4f', 'aPosition', 'aColor')
                # Assuming each vertex is 8 floats (4 bytes each)
            ]
        )
        center_data = self.generate_center_vertex_data(
            radius=constants.GIZMO_CENTER_RADIUS,
            color=(0.8, 0.8, 0.0, constants.GIZMO_ALPHA))
        self.handle_triangles_highlight_vbo = self.ctx.buffer(center_data.tobytes())
        self.handle_triangles_highlight_vao = self.ctx.vertex_array(
            self.program_triangles,
            [
                (self.handle_triangles_highlight_vbo, '3f 4f', 'aPosition', 'aColor')
            ]
        )

    def generate_center_vertex_data(self, radius: float, color: tuple) -> np.ndarray:

        # TODO: same function as the one transform gizmo. Move this to a common base class

        mesh_factory = MeshFactory3D()
        shape_list = [
            {"name": "icosphere",
             "radius": radius,
             "color": color,
             "subdivisions": 3},
        ]
        mesh_data = mesh_factory.generate_mesh(shape_list=shape_list)
        vertices_and_colors = np.concatenate([mesh_data["vertices"], mesh_data["colors"]], axis=1)

        return vertices_and_colors

    def render(self,
               view_matrix: mat4,
               projection_matrix: mat4,
               model_matrix: mat4):

        # Update lines VBOs



        pass

    def handle_event_mouse_move(self,
                                event_data: tuple,
                                ray_origin: vec3,
                                ray_direction: vec3,
                                model_matrix: mat4,
                                component: Any) -> mat4:

        if component is None:
            return None

        # Calculate perpendicular distances between handles and ray
        handles_dist2 = [math_3d.distance2_ray_point(ray_origin=ray_origin,
                                                     ray_direction=ray_direction,
                                                     point=vec3(point)) for point in component.control_points]


        #if handles_dist2 < (self.gizmo_scale * constants.GIZMO_CENTER_RADIUS) ** 2:
        #    pass



        return None

    def handle_event_mouse_drag(self,
                                event_data: tuple,
                                ray_origin: vec3,
                                ray_direction: vec3,
                                model_matrix: mat4,
                                component: Any) -> mat4:
        if component is None:
            return None

        return None