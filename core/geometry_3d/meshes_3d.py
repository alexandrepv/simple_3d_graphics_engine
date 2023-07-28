import numpy as np
import trimesh
from functools import lru_cache
from core.utilities import utils
from core.math import so3


# Constants
_CYLINDER_SECTORS = 8

@lru_cache
def create_sphere(radius=1.0, rings=16, sectors=32):
    """
    Create a sphere centered at the origin. This is a port of moderngl-window's geometry.sphere() function, but it
    returns the vertices and faces explicitly instead of directly storing them in a VAO.
    :param radius: Radius of the sphere.
    :param rings: Longitudinal resolution.
    :param sectors: Latitudinal resolution.
    :return: vertices and faces of the sphere.
    """
    R = 1.0 / (rings - 1)
    S = 1.0 / (sectors - 1)

    vertices = np.zeros((rings * sectors, 3))
    v, n = 0, 0
    for r in range(rings):
        for s in range(sectors):
            y = np.sin(-np.pi / 2 + np.pi * r * R)
            x = np.cos(2 * np.pi * s * S) * np.sin(np.pi * r * R)
            z = np.sin(2 * np.pi * s * S) * np.sin(np.pi * r * R)

            vertices[v] = np.array([x, y, z]) * radius

            v += 1
            n += 1

    faces = np.zeros([rings * sectors * 2, 3], dtype=np.int32)
    i = 0
    for r in range(rings - 1):
        for s in range(sectors - 1):
            faces[i] = np.array([r * sectors + s, (r + 1) * sectors + (s + 1), r * sectors + (s + 1)])
            faces[i + 1] = np.array([r * sectors + s, (r + 1) * sectors + s, (r + 1) * sectors + (s + 1)])
            i += 2

    return vertices, faces

@lru_cache
def create_disk(n_disks=1, radius=1.0, sectors=None, plane="xz"):
    """
    Create `n_disks` many disks centered at the origin with the given radius1.
    :param n_disks: How many disks to create.
    :param radius: Radius of the disks.
    :param sectors: How many lines to use to approximate the disk. Increasing this will lead to more vertex data.
    :param plane: In which plane to create the disk.
    :return: Vertices as a np array of shape (N, V, 3), and face data as a np array of shape (F, 3).
    """
    assert plane in ["xz", "xy", "yz"]
    sectors = sectors or _CYLINDER_SECTORS
    angle = 2 * np.pi / sectors

    c1 = "xyz".index(plane[0])
    c2 = "xyz".index(plane[1])
    c3 = "xyz".index("xyz".replace(plane[0], "").replace(plane[1], ""))

    # Vertex Data.
    vertices = np.zeros((n_disks, sectors + 1, 3))
    x = radius * np.cos(np.arange(sectors) * angle)
    y = radius * np.sin(np.arange(sectors) * angle)
    vertices[:, 1:, c1] = x
    vertices[:, 1:, c2] = y

    # Faces.
    faces = np.zeros((sectors, 3), dtype=np.int32)
    idxs = np.array(range(1, sectors + 1), dtype=np.int32)
    faces[:, 2] = idxs
    faces[:-1, 1] = idxs[1:]
    faces[-1, 1] = 1

    return {"vertices": vertices, "faces": faces}


def create_cylinder_from_to(v1, v2, radius1=1.0, radius2=1.0, sectors=None):
    """
    Create cylinders from points v1 to v2.
    :param v1: A np array of shape (N, 3).
    :param v2: A np array of shape (N, 3).
    :param radius1: The radius at the bottom of the cylinder.
    :param radius2: The radius at the top of the cylinder.
    :param sectors: how many lines to use to approximate the bottom disk.
    :return: Vertices and normals as a np array of shape (N, V, 3) and face data in shape (F, 3), i.e. only one
      face array is created for all cylinders.
    """
    sectors = sectors or _CYLINDER_SECTORS
    n_cylinders = v1.shape[0]

    # Create bottom lid.
    bottom = create_disk(n_disks=n_cylinders, radius=radius1, sectors=sectors)

    # We must also change the winding of the bottom triangles because we have backface culling enabled and
    # otherwise we wouldn't see the bottom lid even if the normals are correct.
    fs_bottom = bottom["faces"]
    fs_bottom[:, 1], fs_bottom[:, 2] = fs_bottom[:, 2], fs_bottom[:, 1].copy()

    # Create top lid.
    top = create_disk(n_disks=n_cylinders, radius=radius2, sectors=sectors)
    p2 = np.zeros((n_cylinders, 3))
    p2[:, 1] = np.linalg.norm(v2 - v1, axis=-1)
    top["vertices"] = top["vertices"] + p2[:, np.newaxis]

    # Shift indices of top faces by how many vertices the bottom lid has.
    n_vertices = bottom["vertices"].shape[1]
    fs_top = top["faces"] + n_vertices

    # Create the faces that make up the coat between bottom and top lid.
    idxs_bot = np.array(range(1, sectors + 1), dtype=np.int32)
    idxs_top = idxs_bot + n_vertices
    fs_coat1 = np.zeros((sectors, 3), dtype=np.int32)
    fs_coat1[:, 0] = idxs_top
    fs_coat1[:-1, 1] = idxs_top[1:]
    fs_coat1[-1, 1] = idxs_top[0]
    fs_coat1[:, 2] = idxs_bot

    fs_coat2 = np.zeros((sectors, 3), dtype=np.int32)
    fs_coat2[:, 0] = fs_coat1[:, 1]
    fs_coat2[:-1, 1] = idxs_bot[1:]
    fs_coat2[-1, 1] = idxs_bot[0]
    fs_coat2[:, 2] = idxs_bot

    # Concatenate everything to create a single mesh.
    vs = np.concatenate([bottom["vertices"], top["vertices"]], axis=1)
    fs = np.concatenate([fs_bottom, fs_top, fs_coat1, fs_coat2], axis=0)

    # Compute smooth normals.
    vertex_faces = trimesh.Trimesh(vs[0], fs, process=False).vertex_faces
    ns, _ = utils.compute_vertex_and_face_normals(vs[0:1], fs, vertex_faces, normalize=True)
    ns = np.repeat(ns, n_cylinders, axis=0)

    # Rotate cylinders to align the the given data.
    vs, ns = rotate_cylinder_to(v2 - v1, vs, ns)

    # Translate cylinders to the given positions
    vs += v1[:, np.newaxis]

    return {"vertices": vs, "normals": ns, "faces": fs}


def create_cone_from_to(v1, v2, radius=1.0, sectors=None):
    """
    Create a cone from points v1 to v2.
    :param v1: A np array of shape (N, 3).
    :param v2: A np array of shape (N, 3).
    :param radius: The radius for the disk of the cone.
    :param sectors: how many lines to use to approximate the bottom disk.
    :return: Vertices and normals as a np array of shape (N, V, 3) and face data in shape (F, 3), i.e. only one
      face array is created for all cones.
    """
    sectors = sectors or _CYLINDER_SECTORS
    n_cylinders = v1.shape[0]

    # Create bottom lid.
    bottom = create_disk(n_cylinders, radius, sectors)

    # We must also change the winding of the bottom triangles because we have backface culling enabled and
    # otherwise we wouldn't see the bottom lid even if the normals are correct.
    fs_bottom = bottom["faces"]
    fs_bottom[:, 1], fs_bottom[:, 2] = fs_bottom[:, 2], fs_bottom[:, 1].copy()

    # Add the top position as a new vertex.
    p2 = np.zeros((n_cylinders, 3))
    p2[:, 1] = np.linalg.norm(v2 - v1, axis=-1)
    vs = np.concatenate([bottom["vertices"], p2[:, np.newaxis]], axis=1)
    n_vertices = vs.shape[1]
    idx_top = n_vertices - 1

    # Create the faces from the bottom lid to the top point.
    idxs_bot = np.array(range(1, sectors + 1), dtype=np.int32)
    fs_coat = np.zeros((sectors, 3), dtype=np.int32)
    fs_coat[:, 0] = idx_top
    fs_coat[:-1, 1] = idxs_bot[1:]
    fs_coat[-1, 1] = idxs_bot[0]
    fs_coat[:, 2] = idxs_bot

    # Concatenate everything to create a single mesh.
    fs = np.concatenate([fs_bottom, fs_coat], axis=0)

    # Compute smooth normals.
    vertex_faces = trimesh.Trimesh(vs[0], fs, process=False).vertex_faces
    ns, _ = utils.compute_vertex_and_face_normals(vs[0:1], fs, vertex_faces, normalize=True)
    ns = np.repeat(ns, n_cylinders, axis=0)

    # Rotate cones to align the the given data.
    vs, ns = rotate_cylinder_to(v2 - v1, vs, ns)

    # Translate cones to the given positions
    vs += v1[:, np.newaxis]

    return {"vertices": vs, "normals": ns, "faces": fs}


def rotate_cylinder_to(target: np.ndarray, vs: np.ndarray, ns: np.ndarray):
    """
    Rotate vertices and normals such that the main axis of the cylinder aligns with `target`.
    :param target: A np array of shape (N, 3) specifying the target direction for each cylinder given in `vs`.
    :param vs: A np array of shape (N, V, 3), i.e. the vertex data for each cylinder.
    :param ns: A np array of shape (N, V, 3), i.e. the normal data for each cylinder.
    :return: The rotated vertices and normals.
    """
    n_cylinders = vs.shape[0]
    s = np.array([[0.0, 1.0, 0.0]]).repeat(n_cylinders, axis=0)
    v = target / (np.linalg.norm(target, axis=1, keepdims=True) + 1e-16)
    a = np.cross(s, v, axis=1)
    dot = np.sum(s * v, axis=1)
    theta = np.arccos(dot)
    is_col = np.linalg.norm(a, axis=1) < 10e-6
    a[is_col] = np.array([1.0, 0.0, 0.0])
    theta[is_col] = 0.0
    theta[np.logical_and(dot < 0.0, is_col)] = np.pi
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    rot = so3.aa2rot_numpy(a * theta[..., np.newaxis])
    vs = np.matmul(rot[:, np.newaxis], vs[..., np.newaxis]).squeeze(-1)
    ns = np.matmul(rot[:, np.newaxis], ns[..., np.newaxis]).squeeze(-1)
    return vs, ns


def create_chessboard(side_length: float, num_tiles: int):

    vertices = []
    faces = []
    face_colors = []
    color_1_indices = []  # Store indices into face_colors containing color 1.
    color_2_indices = []  # Store indices into face_colors containing color 2.
    tile_size = side_length / num_tiles
    dim1 = "xyz".index(self.plane[0])
    dim2 = "xyz".index(self.plane[1])
    up = "xyz".index("xyz".replace(self.plane[0], "").replace(self.plane[1], ""))

    for row in range(num_tiles):
        for col in range(num_tiles):
            v0 = np.zeros([3])
            v0[dim1] = row * tile_size
            v0[dim2] = col * tile_size

            v1 = np.zeros([3])
            v1[dim1] = (row + 1) * tile_size
            v1[dim2] = col * tile_size

            v2 = np.zeros([3])
            v2[dim1] = (row + 1) * tile_size
            v2[dim2] = (col + 1) * tile_size

            v3 = np.zeros([3])
            v3[dim1] = row * tile_size
            v3[dim2] = (col + 1) * tile_size

            vertices.extend([v0, v1, v2, v3])

            # Need counter-clock-wise ordering
            faces.append([len(vertices) - 4, len(vertices) - 1, len(vertices) - 3])
            faces.append([len(vertices) - 3, len(vertices) - 1, len(vertices) - 2])

            if row % 2 == 0 and col % 2 == 0:
                col = self.c1
                fc_idxs = color_1_indices
            elif row % 2 == 0 and col % 2 != 0:
                col = self.c2
                fc_idxs = color_2_indices
            elif row % 2 != 0 and col % 2 != 0:
                col = self.c1
                fc_idxs = color_1_indices
            else:
                col = self.c2
                fc_idxs = color_2_indices
            face_colors.append(col)
            face_colors.append(col)
            fc_idxs.extend([len(face_colors) - 2, len(face_colors) - 1])

    vertices = np.stack(vertices)
    vertices = vertices - np.mean(vertices, axis=0, keepdims=True)
    vertices[:, up] = self.height
    faces = np.stack(faces)
    face_colors = np.stack(face_colors)

    return vertices, faces, face_colors, color_1_indices, color_2_indices