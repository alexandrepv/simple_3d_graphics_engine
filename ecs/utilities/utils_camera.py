import numpy as np
from numba import njit


def _transform_vector(transform, vector):
    """Apply affine transformation (4-by-4 matrix) to a 3D vector."""
    return (transform @ np.concatenate([vector, np.array([1])]))[:3]


def _transform_direction(transform, vector):
    """Apply affine transformation (4-by-4 matrix) to a 3D directon."""
    return (transform @ np.concatenate([vector, np.array([0])]))[:3]

def normalize(x):
    return x / np.linalg.norm(x)


def look_at(position, target, up):
    """
    Create an affine transformation that locates the camera at `position`, s.t. it looks at `target`.
    :param position: The 3D position of the camera in world coordinates.
    :param target: The 3D target where the camera should look at in world coordinates.
    :param up: The vector that is considered to be up in world coordinates.
    :return: Returns the 4-by-4 affine transform that transforms a point in world space into the camera space, i.e.
      it returns the inverse of the camera's 6D pose matrix. Assumes right-multiplication, i.e. x' = [R|t] * x.
    """

    forward = normalize(position - target)  # forward actually points in the other direction than `target` is.
    right = normalize(np.cross(up, forward))
    camera_up = np.cross(forward, right)

    # We directly create the inverse matrix (i.e. world2cam) because this is typically how look-at is define.
    rot = np.eye(4)
    rot[0, :3] = right
    rot[1, :3] = camera_up
    rot[2, :3] = forward

    trans = np.eye(4)
    trans[:3, 3] = -position

    return rot @ trans


def orthographic_projection(scale_x, scale_y, znear, zfar):
    """Returns an orthographic projection matrix."""
    P = np.zeros((4, 4))
    P[0][0] = 1.0 / scale_x
    P[1][1] = 1.0 / scale_y
    P[2][2] = 2.0 / (znear - zfar)
    P[2][3] = (zfar + znear) / (znear - zfar)
    P[3][3] = 1.0
    return P


def perspective_projection(fov, aspect_ratio, znear, zfar):
    """Returns a perspective projection matrix."""
    ar = aspect_ratio
    t = np.tan(fov / 2.0)

    P = np.zeros((4, 4))
    P[0][0] = 1.0 / (ar * t)
    P[1][1] = 1.0 / t
    P[3][2] = -1.0

    f, n = zfar, znear
    if f is None:
        P[2][2] = -1.0
        P[2][3] = -2.0 * n
    else:
        P[2][2] = (f + n) / (n - f)
        P[2][3] = (2 * f * n) / (n - f)

    return P