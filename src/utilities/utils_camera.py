import numpy as np
from numba import njit, float32

from src.core import constants
from src.math import mat4


@njit(cache=True)
def set_gizmo_scale(view_matrix: np.ndarray, object_position: np.array) -> float:

    view_position = mat4.mul_vector3(in_mat4=view_matrix, in_vec3=object_position)
    scale = np.abs(view_position[2]) * constants.GIZMO_3D_ANGLE_TANGENT_COEFFICIENT
    return scale


@njit(cache=True)
def screen_gl_position_pixels2viewport_position(position_pixels: tuple, viewport_pixels: tuple) -> tuple:

    """
    Screen's GL origin is the left-lower corner with positive x to the RIGHT and positive y UP. Both axes start from 0
    Viewports origin is at its center with positive x to the RIGHT and positive y UP. Both axes range form -1 to 1

    :param position_pixels: (x, y) <float32>
    :param viewport_pixels: tuple (x, y, width, height) <float32>
    :return: Relative
    """

    if position_pixels[0] < viewport_pixels[0]:
        return None

    if position_pixels[0] > (viewport_pixels[0] + viewport_pixels[2]):
        return None

    if position_pixels[1] < viewport_pixels[1]:
        return None

    if position_pixels[1] > (viewport_pixels[1] + viewport_pixels[3]):
        return None

    x_normalised = (position_pixels[0] - viewport_pixels[0]) / viewport_pixels[2]
    y_normalised = (position_pixels[1] - viewport_pixels[1]) / viewport_pixels[3]

    x_viewport = (x_normalised - 0.5) * 2.0
    y_viewport = (y_normalised - 0.5) * 2.0

    return x_viewport, y_viewport


@njit(cache=True)
def screen_pos2world_ray(viewport_coord_norm: tuple,
                         camera_matrix: np.ndarray,
                         inverse_projection_matrix: np.ndarray):

    """
    Viewport coordinates are +1 to the right, -1 to the left, +1 up and -1 down. Zero at the centre for both axes

    :param viewport_coord_norm: tuple, (x, y) <float, float> Ranges between -1 and 1
    :param camera_matrix: np.ndarray (4, 4) <float32> Do NOT confuse this with the "view_matrix"!
                          This is the transform of the camera in space, simply as you want the camera to be placed
                          in the scene. the view_matrix is the INVERSE of the camera_matrix :)

    :param inverse_projection_matrix: (4, 4) <float32> inverse of the projection matrix

    :return:
    """

    # TODO: [BUG] Orthographic camera doesn't work

    # Create a 4D homogeneous clip space coordinate
    clip_coordinates = np.array([viewport_coord_norm[0], viewport_coord_norm[1], -1.0, 1.0], dtype=np.float32)

    # Inverse the projection matrix to get the view coordinates
    eye_coordinates = np.dot(inverse_projection_matrix, clip_coordinates)
    eye_coordinates = np.array([eye_coordinates[0], eye_coordinates[1], -1.0, 0.0], dtype=np.float32)

    # Inverse the view matrix to get the world coordinates
    world_coordinates = np.dot(camera_matrix, eye_coordinates)

    # Extract the ray's origin from the inverted view matrix
    ray_origin = np.ascontiguousarray(camera_matrix[:, 3][:3])  # When extracting vectors, they need to be continuous!

    # Normalize the world coordinates to get the ray direction
    ray_direction = np.ascontiguousarray(world_coordinates[:3])
    ray_direction /= np.linalg.norm(ray_direction)

    return ray_direction, ray_origin

@njit(cache=True)
def orthographic_projection(scale_x: float, scale_y: float, z_near: float, z_far: float):
    """Returns an orthographic projection matrix."""
    projection = np.zeros((4, 4), dtype=np.float32)
    projection[0, 0] = 1.0 / scale_x
    projection[1, 1] = 1.0 / scale_y
    projection[2, 2] = 2.0 / (z_near - z_far)
    projection[2, 3] = (z_far + z_near) / (z_near - z_far)
    projection[3, 3] = 1.0
    return projection


@njit(cache=True)
def perspective_projection(fov_rad: float, aspect_ratio: float, z_near: float, z_far: float):
    """Returns a perspective projection matrix."""
    ar = aspect_ratio
    t = np.tan(fov_rad / 2.0)

    projection = np.zeros((4, 4), dtype=np.float32)
    projection[0, 0] = 1.0 / (ar * t)
    projection[1, 1] = 1.0 / t
    projection[3, 2] = -1.0

    f, n = z_far, z_near
    if f is None:
        projection[2, 2] = -1.0
        projection[2, 3] = -2.0 * n
    else:
        projection[2, 2] = (f + n) / (n - f)
        projection[2, 3] = (2 * f * n) / (n - f)

    return projection

"""

@njit
def screen_to_world_ray(screen_coords_normalised: tuple,
                        view_matrix: np.ndarray,
                        projection_matrix: np.ndarray,
                        output_ray_origin: np.array,
                        output_ray_direction: np.array):
                        
    # :param output_ray_origin: np.array (3,) <float32> origin of ray matching the camera's view matrix
    #     :param output_ray_direction: np.array (3,) <float32> direction of ray

    # Create a 4D homogeneous clip space coordinate
    clip_coordinates = np.array([screen_coords_normalised[0], screen_coords_normalised[1], -1.0, 1.0])

    # Inverse the projection matrix to get the view coordinates
    inv_projection_matrix = np.linalg.inv(projection_matrix)
    eye_coordinates = np.dot(inv_projection_matrix, clip_coordinates)
    eye_coordinates = np.array([eye_coordinates[0], eye_coordinates[1], -1.0, 0.0])

    # Inverse the view matrix to get the world coordinates
    inv_view_matrix = np.linalg.inv(view_matrix)
    world_coordinates = np.dot(inv_view_matrix, eye_coordinates)

    # Extract the ray's origin from the inverted view matrix
    output_ray_origin = inv_view_matrix[:, 3][:3]

    # Normalize the world coordinates to get the ray direction
    output_ray_direction = world_coordinates[:3]
    output_ray_direction /= np.linalg.norm(output_ray_direction)

"""