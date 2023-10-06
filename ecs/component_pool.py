import logging
import os
import numpy as np
from bs4 import BeautifulSoup

from ecs import constants
from ecs.components.component import Component
from ecs.components.transform_3d import Transform3D
from ecs.components.collider import Collider
from ecs.components.mesh import Mesh
from ecs.components.material import Material
from ecs.components.camera import Camera
from ecs.components.input_control import InputControl
from ecs.components.text_2d import Text2D
from ecs.components.point_light import PointLight
from ecs.components.directional_light import DirectionalLight

from ecs.utilities import utils_string


class Entity:

    def __init__(self, name=""):
        self.name = name
        self.parent_entity = None
        self.children_entities = []

    @property
    def is_subentity(self):
        return self.parent_entity is not None


class ComponentPool:

    COMPONENT_CLASS_MAP = {
        constants.COMPONENT_TYPE_TRANSFORM_3D: Transform3D,
        constants.COMPONENT_TYPE_MESH: Mesh,
        constants.COMPONENT_TYPE_CAMERA: Camera,
        constants.COMPONENT_TYPE_MATERIAL: Material,
        constants.COMPONENT_TYPE_INPUT_CONTROL: InputControl,
        constants.COMPONENT_TYPE_TEXT_2D: Text2D,
        constants.COMPONENT_TYPE_POINT_LIGHT: PointLight,
        constants.COMPONENT_TYPE_DIRECTIONAL_LIGHT: DirectionalLight,
        constants.COMPONENT_TYPE_COLLIDER: Collider,
    }

    def __init__(self, logger: logging.Logger):

        self.logger = logger

        # TODO: We start from 2 to make it easy to discern the background [0, 1]
        self.entity_uid_counter = constants.COMPONENT_POOL_STARTING_ID_COUNTER

        # For holding states!
        self.entities = {}

        # Components
        self.transform_3d_components = {}
        self.transform_2d_components = {}
        self.camera_components = {}
        self.mesh_components = {}
        self.material_components = {}
        self.input_control_components = {}
        self.text_2d_components = {}
        self.directional_light_components = {}
        self.spot_light_components = {}
        self.point_light_components = {}
        self.collider_components = {}

        self.component_storage_map = {
            constants.COMPONENT_TYPE_TRANSFORM_3D: self.transform_3d_components,
            constants.COMPONENT_TYPE_TRANSFORM_2D: self.transform_2d_components,
            constants.COMPONENT_TYPE_MESH: self.mesh_components,
            constants.COMPONENT_TYPE_CAMERA: self.camera_components,
            constants.COMPONENT_TYPE_MATERIAL: self.material_components,
            constants.COMPONENT_TYPE_INPUT_CONTROL: self.input_control_components,
            constants.COMPONENT_TYPE_TEXT_2D: self.text_2d_components,
            constants.COMPONENT_TYPE_DIRECTIONAL_LIGHT: self.directional_light_components,
            constants.COMPONENT_TYPE_SPOT_LIGHT: self.spot_light_components,
            constants.COMPONENT_TYPE_POINT_LIGHT: self.point_light_components,
            constants.COMPONENT_TYPE_COLLIDER: self.collider_components,
        }

        # This variable is a temporary solution to keep track of all entities added during the xml scene loading
        self.entity_uids_to_be_initiliased = []

    def create_entity(self, name="") -> int:
        uid = self.entity_uid_counter
        self.entities[uid] = Entity(name=name)
        self.entity_uid_counter += 1
        return uid

    def add_component(self, entity_uid: int, component_type: int, **kwargs):
        component_pool = self.component_storage_map.get(component_type, None)

        # Safety
        if component_pool is None:
            raise TypeError(f"[ERROR] Component type '{component_type}' not supported")
        if entity_uid in component_pool:
            raise TypeError(f"[ERROR] Component type '{component_type}' already exists in component pool")

        component_pool[entity_uid] = ComponentPool.COMPONENT_CLASS_MAP[component_type](**kwargs)
        return component_pool[entity_uid]

    def remove_component(self, entity_uid: int, component_type: str):

        if self.entities[entity_uid].is_sub_entity:
            raise Exception("[ERROR] Tried to remove sub-component directly")
        component_pool = self.component_storage_map.get(component_type, None)

        # Safety
        if component_pool is None:
            return

        component_pool[entity_uid].release()
        component_pool.pop(entity_uid)

    def get_component(self, entity_uid: int, component_type: str) -> Component:

        entity = self.entities.get(entity_uid, None)
        if entity is None:
            raise TypeError(f"[ERROR] Entity ID '{entity}' not present")

        component_pool = self.component_storage_map.get(component_type, None)

        component = component_pool.get(entity_uid, None)
        if component is not None:
            return component

        if entity.is_sub_entity():
            return self.get_component(entity_uid=entity_uid.parent_entity)

        raise TypeError(f"[ERROR] Component type '{component_type}' not supported")

    def get_all_components(self, entity_uid: int) -> list:
        return [storage[entity_uid] for _, storage in self.component_storage_map.items() if entity_uid in storage]

    def get_entities_using_component(self, component_type: int) -> list:
        return list(self.component_storage_map[component_type].keys())

    # ================================================================================
    #                           Scene Loading Functions
    # ================================================================================

    def load_scene(self, scene_xml_fpath: str):

        # Check if path is absolute
        fpath = None
        if os.path.isfile(scene_xml_fpath):
            fpath = scene_xml_fpath

        if fpath is None:
            # Assume it is a relative path from the working directory/root directory
            clean_scene_xml_fpath = scene_xml_fpath.replace("\\", os.sep).replace("/", os.sep)
            fpath = os.path.join(constants.ROOT_DIR, clean_scene_xml_fpath)

        # Load UI window blueprint
        with open(fpath) as file:
            root_soup = BeautifulSoup(file.read(), features="lxml")

            # Find window root node - there should be only one
            ui_soup = root_soup.find("scene")
            if ui_soup is None:
                raise ValueError(f"[ERROR] Could not find root 'scene' element")

            for entity_soup in root_soup.find_all("entity"):

                entity_name = entity_soup.attrs.get("name", "unamed_entity")
                entity_uid = self.create_entity(name=entity_name)

                self.entity_uids_to_be_initiliased.append(entity_uid)
                self._add_entity_components(entity_uid=entity_uid, entity_soup=entity_soup)

    def _add_entity_components(self, entity_uid: int, entity_soup: BeautifulSoup) -> None:
        """
        This function uses the Beautifulsoup element provided to add all the components
        assigned to the entity UID.
        :param entity_uid: int,
        :param entity_soup:
        :return: None
        """

        for component_soup in entity_soup.find_all():

            # Transform 3D
            if component_soup.name == constants.COMPONENT_NAME_TRANSFORM_3D:
                position_str = component_soup.attrs.get("position", "0 0 0")

                rotation_in_degrees = True if "rotation_deg" in component_soup.attrs else False
                rotation_str = component_soup.attrs.get("rotation_deg" if rotation_in_degrees else "rotation", "0 0 0")

                position = utils_string.string2float_tuple(position_str)
                rotation = utils_string.string2float_tuple(rotation_str)

                if rotation_in_degrees:
                    deg2rad = np.pi / 180.0
                    rotation = (rotation[0] * deg2rad, rotation[1] * deg2rad, rotation[2] * deg2rad)

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_TRANSFORM_3D,
                    position=position,
                    rotation=rotation)
                continue

            # Transform 2D
            if component_soup.name == constants.COMPONENT_NAME_TRANSFORM_2D:
                continue

            # Mesh
            if component_soup.name == constants.COMPONENT_NAME_MESH:
                shape = component_soup.attrs.get("shape", None)
                if shape is None:
                    raise Exception("You need to specify the shape of the mesh you want to create.")

                # Shape: OBJ
                if shape == constants.MESH_SHAPE_FROM_OBJ:
                    fpath = component_soup.attrs.get("fpath", None)
                    if shape is None:
                        raise Exception("You need to specify the location of the .obj file")

                    self.add_component(
                        entity_uid=entity_uid,
                        component_type=constants.COMPONENT_TYPE_MESH,
                        shape=shape,
                        fpath=fpath)

                # Shape: BOX
                if shape == constants.MESH_SHAPE_BOX:
                    self.add_component(
                        entity_uid=entity_uid,
                        component_type=constants.COMPONENT_TYPE_MESH,
                        shape=shape,
                        width=float(component_soup.attrs.get("width", "1.0")),
                        height=float(component_soup.attrs.get("height", "1.0")),
                        depth=float(component_soup.attrs.get("depth", "1.0")))

                # Shape: ICOSPHERE
                if shape == constants.MESH_SHAPE_ICOSPHERE:
                    self.add_component(
                        entity_uid=entity_uid,
                        component_type=constants.COMPONENT_TYPE_MESH,
                        shape=shape,
                        radius=float(component_soup.attrs.get("radius", "0.2")),
                        subdivisions=int(component_soup.attrs.get("subdivisions", "3")))

                # Shape: CYLINDER
                if shape == constants.MESH_SHAPE_CYLINDER:

                    point_a = utils_string.string2int_tuple(component_soup.attrs.get("point_a", "0 0 0"))
                    point_b = utils_string.string2int_tuple(component_soup.attrs.get("point_b", "0 1 0"))
                    radius = component_soup.attrs.get("radius", 0.5)
                    sections = component_soup.attrs.get("sections", 32)

                    self.add_component(
                        entity_uid=entity_uid,
                        component_type=constants.COMPONENT_TYPE_MESH,
                        shape=shape,
                        point_a=point_a,
                        point_b=point_b,
                        radius=radius,
                        sections=sections)
                continue

            # Camera
            if component_soup.name == constants.COMPONENT_NAME_CAMERA:
                viewport_ratio_str = component_soup.attrs.get("viewport_ratio", "0.0 0.0 1.0 1.0")
                perspective_str = component_soup.attrs.get("perspective", "true")

                viewport_ratio = utils_string.string2int_tuple(viewport_ratio_str)
                perspective = utils_string.str2bool(perspective_str)

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_CAMERA,
                    viewport_ratio=viewport_ratio,
                    perspective=perspective)
                continue

            # Material
            if component_soup.name == constants.COMPONENT_NAME_MATERIAL:

                diffuse_str = component_soup.attrs.get("diffuse", ".75 .75 .75")
                specular_str = component_soup.attrs.get("ambient", "1.0 1.0 1.0")

                diffuse = constants.MATERIAL_COLORS.get(diffuse_str, utils_string.string2float_tuple(diffuse_str))
                specular = constants.MATERIAL_COLORS.get(specular_str, utils_string.string2float_tuple(specular_str))

                shininess_factor = float(component_soup.attrs.get("shininess_factor", "32.0"))
                metallic_factor = float(component_soup.attrs.get("metallic_factor", "1.0"))
                roughness_factor = float(component_soup.attrs.get("roughness_factor", "0.0"))

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_MATERIAL,
                    diffuse=diffuse,
                    specular=specular,
                    shininess_factor=shininess_factor,
                    metallic_factor=metallic_factor,
                    roughness_factor=roughness_factor)
                continue

            # Input Control
            if component_soup.name == constants.COMPONENT_NAME_INPUT_CONTROL:
                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_INPUT_CONTROL)
                continue

            # Text 2D
            if component_soup.name == constants.COMPONENT_NAME_TEXT_2D:
                font_name = component_soup.attrs.get("font_name", None)
                if font_name is None:
                    raise Exception("You need to specify the font")

                text_component = self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_TEXT_2D,
                    font_name=font_name)

                # Add text, if present
                text = entity_soup.text.strip()
                if len(text) > 0:
                    text_component.set_text(text=text)
                continue

            # Directional Light
            if component_soup.name == constants.COMPONENT_NAME_DIRECTIONAL_LIGHT:
                diffuse_str = component_soup.attrs.get("diffuse", "1.0 1.0 1.0")
                specular_str = component_soup.attrs.get("ambient", "1.0 1.0 1.0")

                diffuse = tuple(utils_string.string2float_tuple(diffuse_str))
                specular = tuple(utils_string.string2float_tuple(specular_str))

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_DIRECTIONAL_LIGHT,
                    diffuse=diffuse,
                    specular=specular)
                continue

            # Point Light
            if component_soup.name == constants.COMPONENT_NAME_POINT_LIGHT:
                position_str = component_soup.attrs.get("position", "22.0 16.0 50.0")
                color_str = component_soup.attrs.get("color", "1.0 1.0 1.0")

                position = utils_string.string2float_tuple(position_str)
                color = utils_string.string2float_tuple(color_str)

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_POINT_LIGHT,
                    position=position,
                    color=color)
                continue

            # Collider
            if component_soup.name == constants.COMPONENT_NAME_COLLIDER:
                shape_str = component_soup.attrs.get("shape", "sphere")
                radius_str = component_soup.attrs.get("radius", "0.5")

                radius = float(radius_str)

                self.add_component(
                    entity_uid=entity_uid,
                    component_type=constants.COMPONENT_TYPE_COLLIDER,
                    shape=shape_str,
                    radius=radius)
                continue

            # If you got here, it means the component you selected is not supported :(
            entity_name = entity_soup.attrs.get("name", "")
            if len(entity_name) > 0:
                entity_name = f" ({entity_name})"
                self.logger.error(f"Component {component_soup.name}, declared in entity uid "
                                  f"{entity_uid}{entity_name}, is not supported.")


