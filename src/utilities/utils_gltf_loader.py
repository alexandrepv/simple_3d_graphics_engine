import os
import json
import numpy as np

from pygltflib import GLTF2

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

class GLTFLoader:

    def __init__(self):
        self.gltf = None
        self.gltf_header = None
        self.gltf_data = None
        self.gltf_dependencies = None
        self.__file_loaded = False

    def load(self, gltf_fpath: str):

        # Get library to parse it first
        self.gltf = GLTF2().load(gltf_fpath)

        # Then, read it in my own way
        filename = os.path.basename(gltf_fpath)
        _, extension = os.path.splitext(filename)

        # Load Header
        with open(gltf_fpath, "r") as file:
            self.gltf_header = json.load(file)

        # Load binary data
        gltf_dir = os.path.dirname(gltf_fpath)
        bin_fpath = os.path.join(gltf_dir, self.gltf_header[GLTF_BUFFERS][0][GLTF_URI])
        target_bin_data_size = self.gltf_header[GLTF_BUFFERS][0][GLTF_BYTE_LENGTH]

        with open(bin_fpath, "rb") as file:
            self.gltf_data = file.read()

        if target_bin_data_size != len(self.gltf_data):
            raise Exception(f"[ERROR] Loaded GLTF binary data from {bin_fpath} has {len(self.gltf_data)} bytes, "
                            f"but was expected to have {target_bin_data_size} bytes")

        # Load dependencies
        # TODO: Load any textures that are listed in the gltf_hedear

        self.__file_loaded = True

    def read_binary_data(self, buffer_view_index):

        if not self.__file_loaded:
            return None

        buffer_view = self.gltf.bufferViews[buffer_view_index]
        return self.gltf_data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength]

    def get_animation(self):

        if not self.__file_loaded:
            return None

        for animation in self.gltf.animations:
            print(f"Animation: {animation.name}")
            for channel in animation.channels:

                sampler = animation.samplers[channel.sampler]
                input_accessor = self.gltf.accessors[sampler.input]
                output_accessor = self.gltf.accessors[sampler.output]

                # Load keyframe data
                input_binary_data = self.read_binary_data(input_accessor.bufferView)
                output_binary_data = self.read_binary_data(output_accessor.bufferView)

                input_data = np.frombuffer(input_binary_data,
                                           dtype=GLTF_DATA_TYPE_MAP[input_accessor.componentType])
                output_data = np.frombuffer(output_binary_data,
                                            dtype=GLTF_DATA_TYPE_MAP[output_accessor.componentType])

            print(f"Keyframe Times: {input_data}")
            print(f"Keyframe Values: {output_data}")

        g = 0

# Usage
loader = GLTFLoader()
loader.load(r"D:\git_repositories\alexandrepv\simple_3d_graphics_engine\resources\meshes\BrainStem.gltf")
loader.get_animation()