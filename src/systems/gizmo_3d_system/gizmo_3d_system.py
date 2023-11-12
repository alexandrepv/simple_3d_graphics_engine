import logging
import moderngl
import numpy as np

from src.core import constants
from src.core.event_publisher import EventPublisher
from src.core.action_publisher import ActionPublisher
from src.core.component_pool import ComponentPool
from src.math import ray_intersection, mat4
from src.utilities import utils_camera
from src.systems.system import System
from src.systems.gizmo_3d_system.gizmo_blueprint import GIZMO_3D_RIG_BLUEPRINT


class Gizmo3DSystem(System):

    name = "gizmo_3d_system"

    __slots__ = [
        "entity_ray_intersection_list",
        "window_size",
        "selected_entity_uid",
        "selected_entity_init_distance_to_cam",
        "gizmo_selection_enabled",
        "gizmo_axis_on_hover_index",
        "gizmo_mouse_hovering",
        "gizmo_in_use",
        "selected_entity_original_transform_component",
        "camera2gizmo_map",
        "mouse_screen_position",
        "axes_distances",
        "gizmo_transformed_axes",
        "hover_axis_index",
        "event_handlers"
    ]

    def __init__(self, logger: logging.Logger,
                 component_pool: ComponentPool,
                 event_publisher: EventPublisher,
                 action_publisher: ActionPublisher,
                 parameters: dict,
                 **kwargs):

        super().__init__(logger=logger,
                         component_pool=component_pool,
                         event_publisher=event_publisher,
                         action_publisher=action_publisher,
                         parameters=parameters)

        self.window_size = None
        self.entity_ray_intersection_list = []
        self.gizmo_axis_on_hover_index = None
        self.camera2gizmo_map = {}
        self.mouse_screen_position = (-1, -1)  # in Pixels
        self.axes_distances = np.array([-1, -1, -1], dtype=np.float32)
        self.gizmo_transformed_axes = np.eye(3, dtype=np.float32)

        # In-Use variables
        self.selected_entity_original_transform_component = None

        # State flags
        self.gizmo_selection_enabled = True
        self.gizmo_in_use = False

        # State variables
        self.selected_entity_uid = None
        self.selected_entity_init_distance_to_cam = None

        self.event_handlers = {
            constants.EVENT_WINDOW_FRAMEBUFFER_SIZE: self.handle_event_window_framebuffer_size,
            constants.EVENT_ENTITY_SELECTED: self.handle_event_entity_selected,
            constants.EVENT_ENTITY_DESELECTED: self.handle_event_entity_deselected,
            constants.EVENT_MOUSE_LEAVE_UI: self.handle_event_mouse_leave_ui,
            constants.EVENT_MOUSE_ENTER_UI: self.handle_event_mouse_enter_ui,
            constants.EVENT_MOUSE_MOVE: self.handle_event_mouse_move,
            constants.EVENT_MOUSE_BUTTON_PRESS: self.handle_event_mouse_button_press,
            constants.EVENT_MOUSE_BUTTON_RELEASE: self.handle_event_mouse_button_release,
        }

    def initialise(self) -> bool:
        """
        Initialises the Gizmo3D system using the parameters given

        :return: bool, TRUE if all steps of initialisation succeeded
        """

        # Stage 1) For every camera, create a gizmo entity and associate their ids
        pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_id, camera_component in pool.items():
            if camera_entity_id in self.camera2gizmo_map:
                continue

            # Create new gizmo entity for this camera
            gizmo_entity_uid = self.component_pool.add_entity(entity_blueprint=GIZMO_3D_RIG_BLUEPRINT,
                                                              system_owned=True)
            self.camera2gizmo_map[camera_entity_id] = gizmo_entity_uid

            # And make sure only this camera can render it
            gizmo_meshes = self.component_pool.get_all_sub_entity_components(
                parent_entity_uid=gizmo_entity_uid,
                component_type=constants.COMPONENT_TYPE_MESH)
            for mesh in gizmo_meshes:
                mesh.exclusive_to_camera_uid = camera_entity_id

        # Stage 2) For every gizmo3D, find out which meshes correspond to their respective axes
        pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        for gizmo_3d_entity_uid, gizmo_3d_component in pool.items():

            children_uids = self.component_pool.get_children_uids(entity_uid=gizmo_3d_entity_uid)

            for index, axis_name in enumerate(constants.GIZMO_3D_AXES_NAME_ORDER):

                for child_uid in children_uids:

                    entity_name = self.component_pool.get_entity(child_uid).name

                    if entity_name == axis_name:
                        gizmo_3d_component.axes_entities_uids[index] = child_uid
                        continue

        # Step 3) Hide all gizmos before we begin
        self.set_all_gizmo_3d_visibility(visible=False)

        return True

    def on_event(self, event_type: int, event_data: tuple):

        handler = self.event_handlers.get(event_type, None)
        if handler is not None:
            handler(event_data=event_data)

    # ========================================================================
    #                             Event Handling
    # ========================================================================

    def handle_event_window_framebuffer_size(self, event_data: tuple):
        self.window_size = event_data

    def handle_event_entity_selected(self, event_data: tuple):
        self.selected_entity_uid = event_data[0]
        self.set_all_gizmo_3d_visibility(visible=True)
        self.set_gizmo_to_selected_entity()

    def handle_event_entity_deselected(self, event_data: tuple):
        self.selected_entity_uid = None
        self.set_all_gizmo_3d_visibility(visible=False)

    def handle_event_mouse_enter_ui(self, event_data: tuple):
        self.gizmo_selection_enabled = False

    def handle_event_mouse_leave_ui(self, event_data: tuple):
        self.gizmo_selection_enabled = True

    def handle_event_mouse_move(self, event_data: tuple):
        self.mouse_screen_position = event_data
        self.process_mouse_movement(screen_gl_pixels=(event_data[0], event_data[1]))

    def handle_event_mouse_button_press(self, event_data: tuple):
        if event_data[constants.EVENT_INDEX_MOUSE_BUTTON_BUTTON] != constants.MOUSE_LEFT:
            return

        if self.gizmo_axis_on_hover_index is None:
            return

        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_GIZMO_3D_ACTIVATED,
                                     event_data=(None,),
                                     sender=self)

        transform = self.component_pool.get_component(entity_uid=self.selected_entity_uid,
                                                      component_type=constants.COMPONENT_TYPE_TRANSFORM_3D)

        self.gizmo_in_use = True
        self.selected_entity_original_transform_component = transform
        self.process_mouse_movement(screen_gl_pixels=event_data[2:])

    def handle_event_mouse_button_release(self, event_data: tuple):
        if event_data[constants.EVENT_INDEX_MOUSE_BUTTON_BUTTON] != constants.MOUSE_LEFT:
            return

        if not self.gizmo_in_use:
            return

        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_GIZMO_3D_DEACTIVATED,
                                     event_data=(None,),
                                     sender=self)

        self.gizmo_in_use = False

    # ========================================================================
    #                            Core functions
    # ========================================================================

    def update(self, elapsed_time: float, context: moderngl.Context) -> bool:

        if self.selected_entity_uid is None:
            return True

        # Get component pools for easy access
        transform_3d_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM_3D)

        selected_transform_component = transform_3d_pool[self.selected_entity_uid]
        selected_world_position = np.ascontiguousarray(selected_transform_component.world_matrix[:3, 3])

        camera_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_id, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_id]
            gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]
            camera_matrix = transform_3d_pool[camera_entity_id].world_matrix
            view_matrix = np.eye(4, dtype=np.float32)
            mat4.fast_inverse(in_mat4=camera_matrix, out_mat4=view_matrix)
            gizmo_scale = utils_camera.set_gizmo_scale(view_matrix=view_matrix, object_position=selected_world_position)
            viewport_height = camera_component.viewport_pixels[3]
            gizmo_scale *= constants.GIZMO_3D_VIEWPORT_SCALE_COEFFICIENT / viewport_height

            # Update gizmo's transform parameters for visual feedback
            gizmo_transform_component.position = selected_transform_component.position
            gizmo_transform_component.rotation = selected_transform_component.rotation
            gizmo_transform_component.scale = gizmo_scale
            gizmo_transform_component.input_values_updated = True

        return True

    def process_mouse_movement(self, screen_gl_pixels: tuple):

        """
        Checks whether the mouse is covering any of the axes and if so, highlight and select it.
        :param screen_gl_pixels:
        :return:
        """

        if self.selected_entity_uid is None:
            return

        # Find which viewport the mouse is
        camera_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        active_camera_component = None
        active_camera_id = None
        for camera_entity_id, camera_component in camera_pool.items():
            if camera_component.is_inside_viewport(screen_gl_position=screen_gl_pixels):
                active_camera_component = camera_component
                active_camera_id = camera_entity_id
                continue

        if active_camera_component is None:
            return

        gizmo_3d_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        material_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_MATERIAL)
        transform_3d_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM_3D)

        gizmo_3d_entity_uid = self.camera2gizmo_map[active_camera_id]

        gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]
        mat4.mul_vectors3(in_mat4=gizmo_transform_component.world_matrix,
                          in_vec3_array=constants.GIZMO_3D_AXES,
                          out_vec3_array=self.gizmo_transformed_axes)

        camera_matrix = transform_3d_pool[active_camera_id].world_matrix
        projection_matrix = active_camera_component.get_projection_matrix()

        viewport_position = utils_camera.screen_gl_position_pixels2viewport_position(
            position_pixels=self.mouse_screen_position,
            viewport_pixels=active_camera_component.viewport_pixels)

        if viewport_position is None:
            return

        ray_direction, ray_origin = utils_camera.screen_pos2world_ray(
            viewport_coord_norm=viewport_position,
            camera_matrix=camera_matrix,
            projection_matrix=projection_matrix)

        if self.process_gizmo_in_use(ray_origin=ray_origin, ray_direction=ray_direction):
            return

        # TODO: [CLEANUP] Clean this silly code. Change the intersection function to accommodate for this
        points_a = np.array([gizmo_transform_component.position,
                             gizmo_transform_component.position,
                             gizmo_transform_component.position], dtype=np.float32)

        ray_intersection.intersect_ray_capsules(
            ray_origin=ray_origin,
            ray_direction=ray_direction,
            points_a=points_a,
            points_b=self.gizmo_transformed_axes,
            radius=np.float32(0.1 * gizmo_transform_component.scale),
            output_distances=self.axes_distances)

        # TODO: [CLEANUP] Remove direct access and use get_component instead. Think about performance later

        # De-highlight all axes
        gizmo_component = gizmo_3d_pool[gizmo_3d_entity_uid]
        for axis_entity_uid in gizmo_component.axes_entities_uids:
            material_pool[axis_entity_uid].state_highlighted = False

        # And Re-highlight only the current axis being hovered, if any
        valid_indices = np.where(self.axes_distances > -1.0)[0]
        if valid_indices.size == 0:
            self.gizmo_axis_on_hover_index = None
            self.event_publisher.publish(event_type=constants.EVENT_MOUSE_NOT_HOVERING_GIZMO_3D,
                                         event_data=(-1,),
                                         sender=self)
            return

        selected_axis_index = valid_indices[self.axes_distances[valid_indices].argmin()]
        axis_entity_uid = gizmo_component.axes_entities_uids[selected_axis_index]
        axis_material = material_pool[axis_entity_uid]
        axis_material.state_highlighted = True
        self.gizmo_axis_on_hover_index = int(selected_axis_index)

        # Notify all systems that mouse is currently hovering one of the gizmo axes
        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_HOVERING_GIZMO_3D,
                                     event_data=(self.gizmo_axis_on_hover_index,),
                                     sender=self)

    def process_gizmo_in_use(self, ray_origin: np.array, ray_direction: np.array) -> bool:
        if not self.gizmo_in_use:
            return False

        # TODO: CONTINUE FROM HERE !!!!!!!

        return True

    def set_gizmo_to_selected_entity(self):

        transform_3d_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM_3D)
        selected_transform_component = transform_3d_pool[self.selected_entity_uid]

        camera_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_id, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_id]
            gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]
            gizmo_transform_component.position = selected_transform_component.position
            gizmo_transform_component.rotation = selected_transform_component.rotation
            gizmo_transform_component.input_values_updated = True

    def set_all_gizmo_3d_visibility(self, visible=True):

        camera_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        gizmo_3d_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        mesh_pool = self.component_pool.get_pool(component_type=constants.COMPONENT_TYPE_MESH)

        for camera_entity_id, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_id]
            gizmo_3d_component = gizmo_3d_pool[gizmo_3d_entity_uid]

            for mesh_entity_uid in gizmo_3d_component.axes_entities_uids:
                mesh_pool[mesh_entity_uid].visible = visible

    def perform_ray_axis_collision(self, camera_entity_uid: int) -> tuple:

        camera_component = self.component_pool.camera_components[camera_entity_uid]
        transform_component = self.component_pool.transform_3d_components[camera_entity_uid]

        view_matrix = self.component_pool.transform_3d_components[camera_entity_uid].world_matrix
        projection_matrix = camera_component.get_projection_matrix()

        viewport_coord_norm = camera_component.get_viewport_coordinates(screen_coord_pixels=self.mouse_screen_position)
        if viewport_coord_norm is None:
            return None, None

        return utils_camera.screen_pos2world_ray(
            viewport_coord_norm=viewport_coord_norm,
            camera_matrix=view_matrix,
            projection_matrix=projection_matrix)


