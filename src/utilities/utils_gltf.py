import os
import json
import numpy as np

# Constants
GLTF_MESHES = "meshes"
GLTF_PRIMITIVES = "primitives"
GLTF_NODES = "nodes"
GLTF_ROTATION = "rotation"
GLTF_TRANSLATION = "translation"
GLTF_SCALE = "scale"
GLTF_MATRIX = "matrix"
GLTF_SKIN = "skin"
GLTF_CHILDREN = "children"
GLTF_BUFFERS = "buffers"
GLTF_BYTE_LENGTH = "byteLength"
GLTF_URI = "uri"
GLTF_ACCESSORS = "accessors"
GLTF_BUFFER_VIEWS = "bufferViews"

GLTF_ATTR_POSITION = "POSITION"
GLTF_ATTR_NORMAL = "NORMAL"
GLTF_ATTR_TANGENT = "TANGENT"

GLTF_DATA_TYPE_MAP = {
      5120: np.int8,
      5121: np.uint8,
      5122: np.int16,
      5123: np.uint16,
      5124: np.int32,
      5125: np.uint32,
      5126: np.float32}

GLTF_DATA_SHAPE_MAP = {
    "SCALAR": (1,),
    "VEC2": (2,),
    "VEC3": (3,),
    "VEC4": (4,),
    "MAT2": (2, 2),
    "MAT3": (3, 3),
    "MAT4": (4, 4)}

GLTF_DATA_FORMAT_SIZE_MAP = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16}

GLTF_INTERPOLATION_MAP = {
    "LINEAR": 0,
    "STEP": 1,
    "CUBICSPLINE": 2}


RENDERING_MODES = {
    0: "points",
    1: "lines",
    2: "line_loop",
    3: "line_strip",
    4: "triangles",
    5: "triangle_strip",
    6: "triangle_fan"
}


def load_gltf_parts(gltf_fpath: str, include_dependencies=True) -> tuple:

    filename = os.path.basename(gltf_fpath)
    _, extension = os.path.splitext(filename)

    # Load Header
    gltf_header = None
    with open(gltf_fpath, "r") as file:
        gltf_header = json.load(file)

    # Load binary data
    gltf_dir = os.path.dirname(gltf_fpath)
    bin_fpath = os.path.join(gltf_dir, gltf_header[GLTF_BUFFERS][0][GLTF_URI])
    target_bin_data_size = gltf_header[GLTF_BUFFERS][0][GLTF_BYTE_LENGTH]

    gltf_data = None
    with open(bin_fpath, "rb") as file:
        gltf_data = file.read()

    if target_bin_data_size != len(gltf_data):
        raise Exception(f"[ERROR] Loaded GLTF binary data from {bin_fpath} has {len(gltf_data)} bytes, "
                        f"but was expected to have {target_bin_data_size} bytes")

    # Load dependencies
    gltf_dependencies = {}

    return gltf_header, gltf_data, gltf_dependencies


def load_buffer_view_data(buffer_view: dict, data: bytes) -> bytes:

    # Extract buffer view properties
    byte_offset = buffer_view.get("byteOffset", 0)
    byte_length = buffer_view["byteLength"]
    byte_stride = buffer_view.get("byteStride", 0)  # Optional

    # Calculate the starting and ending byte positions in the binary data
    last_byte = byte_offset + byte_length

    if byte_stride == 0:
        # If byteStride is not specified, read all the data in one go
        loaded_data = data[byte_offset:last_byte]
    else:
        # If byteStride is specified, read data element by element
        num_elements = byte_length // byte_stride
        loaded_data = b''.join(data[byte_offset + i * byte_stride:byte_offset + (i + 1) * byte_stride]
                               for i in range(num_elements))

    return loaded_data


def extract_accessor_arrays(header: dict, data: bytes):

    # Split input data into their respective buffer views to make it easy to be loaded by the accessors
    buffer_views_data = [load_buffer_view_data(buffer_view=buffer_view, data=data)
                         for buffer_view in header[GLTF_BUFFER_VIEWS]]

    accessors_arrays = []

    for accessor in header[GLTF_ACCESSORS]:

        buffer_data = buffer_views_data[accessor["bufferView"]]

        accessor_offset = accessor["byteOffset"]
        data_shape = GLTF_DATA_SHAPE_MAP[accessor["type"]]
        data_type = GLTF_DATA_TYPE_MAP[accessor["componentType"]]
        data_format_size = GLTF_DATA_FORMAT_SIZE_MAP[accessor["type"]]
        num_elements = accessor["count"]

        acessor_data = np.frombuffer(offset=accessor_offset,
                                     count=num_elements * data_format_size,
                                     dtype=data_type,
                                     buffer=buffer_data)

        accessor_array = acessor_data.reshape((-1, *data_shape)) if accessor["type"] != "SCALAR" else acessor_data

        data_min = np.min(accessor_array, axis=0)
        data_max = np.max(accessor_array, axis=0)

        accessors_arrays.append(accessor_array)

    return accessors_arrays


def load_meshes(header: dict, accessor_arrays: list) -> list:

    gltf_meshes = header[GLTF_MESHES]
    meshes = []
    for mesh in gltf_meshes:

        primitives = mesh[GLTF_PRIMITIVES]
        primitives_final = []

        total_num_vertices = 0

        all_indices = []
        all_positions = []
        all_normals = []
        all_tangents = []

        # Group all relevant indices, positions, normals and tangent arrays for this mesh
        for primitive_index, primitive in enumerate(primitives):

            indices = accessor_arrays[primitive["indices"]]
            all_indices.append(indices + total_num_vertices)

            if GLTF_ATTR_POSITION in primitive["attributes"]:
                positions = accessor_arrays[primitive["attributes"][GLTF_ATTR_POSITION]]
                all_positions.append(positions)
                total_num_vertices += positions.shape[0]

            if GLTF_ATTR_NORMAL in primitive["attributes"]:
                normals = accessor_arrays[primitive["attributes"][GLTF_ATTR_NORMAL]]
                all_normals.append(normals)

            if GLTF_ATTR_TANGENT in primitive["attributes"]:
                tangents = accessor_arrays[primitive["attributes"][GLTF_ATTR_TANGENT]]
                all_tangents.append(tangents)

        # Now combine them into one single mesh
        meshes.append(
            {
                "indices": np.concatenate(all_indices) if len(all_indices) > 0 else None,
                "positions": np.concatenate(all_positions, axis=0) if len(all_positions) > 0 else None,
                "normals": np.concatenate(all_normals, axis=0) if len(all_normals) > 0 else None,
                "tangents": np.concatenate(all_tangents, axis=0) if len(all_tangents) > 0 else None
            }
        )

    return meshes


def load_nodes(header: dict, accessor_arrays: list,  scene_index=None) -> dict:

    # First, select which scene to take the meshes from
    if scene_index is None:
        scene_index = header["scene"] if "scene" in header else 0

    gltf_nodes = header[GLTF_NODES]
    num_nodes = len(gltf_nodes)

    node_parent_index = np.empty((num_nodes, ), dtype=np.int32)
    node_matrix = np.empty((num_nodes, 4, 4), dtype=np.float32)
    node_translation = np.empty((num_nodes, 3), dtype=np.float32)
    node_rotation_quat = np.empty((num_nodes, 4), dtype=np.float32)
    node_scale = np.empty((num_nodes, 3), dtype=np.float32)

    for current_index, node in enumerate(gltf_nodes):

        for child_index in node.get("children", []):
            node_parent_index[child_index] = current_index

        node_matrix[current_index, :, :] = np.eye(4, dtype=np.float32)
        if "matrix" in node:
            # GLTF matrices are COLUMN-MAJOR, hence the transpose at the end
            node_matrix[current_index, :, :] = np.reshape(np.array(node["matrix"]), (4, 4)).T

        if "translation" in node:
            node_translation[current_index, :] = np.array(node["translation"])

        if "rotation" in node:
            node_rotation_quat[current_index, :] = np.array(node["rotation"])

        if "scale" in node:
            node_scale[current_index, :] = np.array(node["scale"])

    return {"parent_index": node_parent_index,
            "matrix": node_matrix,
            "translation": node_translation,
            "rotation_quat": node_rotation_quat,
            "scale": node_scale}

def load_animations(header: dict, accessor_arrays: list) -> list:

    pass


# TODO: Remove this function and use the RESOURCE MANAGER INSTEAD
def debug_load_gltf_meshes(gltf_fpath: str) -> list:
    header, data, _ = load_gltf_parts(gltf_fpath=gltf_fpath)
    accessor_arrays = extract_accessor_arrays(header=header, data=data)
    return load_meshes(header=header, accessor_arrays=accessor_arrays)
