import logging
import moderngl
import numpy as np

from src.core import constants
from src.core.event_publisher import EventPublisher
from src.core.action_publisher import ActionPublisher
from src.core.scene import Scene
from src.math import ray_intersection, mat4
from src.utilities import utils_camera
from src.systems.system import System
from src.systems.gizmo_3d_system.gizmo_blueprint import GIZMO_3D_RIG_BLUEPRINT


class Gizmo3DSystem(System):

    name = "gizmo_3d_system"

    __slots__ = [
        "entity_ray_intersection_list",
        "selected_entity_uid",
        "selected_entity_init_distance_to_cam",
        "local_axis_offset_point",
        "original_active_world_matrix",
        "original_active_local_matrix",
        "original_active_local_position",
        "original_active_local_rotation",
        "original_active_local_scale",
        "camera2gizmo_map",
        "mouse_screen_position",
        "local_camera_plane_offset_xy",
        "gizmo_mode_global",
        "gizmo_selection_enabled",
        "gizmo_transformed_axes",
        "gizmo_world_matrix",
        "hover_axis_index",
        "gizmo_state",
        "event_handlers",
        "state_handlers",
        "focused_camera_uid",
        "focused_gizmo_axis_index",
        "focused_gizmo_plane",
        "gizmo_mode",
        "gizmo_orientation"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.entity_ray_intersection_list = []
        self.camera2gizmo_map = {}
        self.gizmo_transformed_axes = np.eye(3, dtype=np.float32)

        # Mouse states
        self.mouse_screen_position = (-1, -1)  # in Pixels

        # Gizmo Active Use variables
        self.local_camera_plane_offset_xy = np.array([0, 0, 0], dtype=np.float32)
        self.local_axis_offset_point = np.array([0, 0, 0], dtype=np.float32)
        self.original_active_local_position = None
        self.original_active_local_rotation = None
        self.original_active_local_scale = None
        self.original_active_local_matrix = None
        self.original_active_world_matrix = None

        # State variables
        self.gizmo_mode = constants.GIZMO_3D_MODE_TRANSLATION
        self.gizmo_orientation = constants.GIZMO_3D_ORIENTATION_GLOBAL
        self.gizmo_selection_enabled = True
        self.gizmo_world_matrix = np.eye(4, dtype=np.float32)
        self.focused_gizmo_axis_index = -1
        self.focused_gizmo_plane = -1
        self.focused_camera_uid = None
        self.gizmo_state = constants.GIZMO_3D_STATE_NOT_HOVERING
        self.selected_entity_uid = None
        self.selected_entity_init_distance_to_cam = None

        # Register event-handling callbacks
        self.event_handlers[constants.EVENT_ENTITY_SELECTED] = self.handle_event_entity_selected
        self.event_handlers[constants.EVENT_ENTITY_DESELECTED] = self.handle_event_entity_deselected
        self.event_handlers[constants.EVENT_MOUSE_ENTER_UI] = self.handle_event_mouse_enter_ui
        self.event_handlers[constants.EVENT_MOUSE_LEAVE_UI] = self.handle_event_mouse_leave_ui
        self.event_handlers[constants.EVENT_MOUSE_MOVE] = self.handle_event_mouse_move
        self.event_handlers[constants.EVENT_MOUSE_BUTTON_PRESS] = self.handle_event_mouse_button_press
        self.event_handlers[constants.EVENT_MOUSE_BUTTON_RELEASE] = self.handle_event_mouse_button_release
        self.event_handlers[constants.EVENT_GIZMO_3D_SYSTEM_PARAMETER_UPDATED] = self.handle_event_parameter_updated

        # Internal state handling
        self.state_handlers = {
            constants.GIZMO_3D_STATE_NOT_HOVERING: self.handle_state_not_hovering,
            constants.GIZMO_3D_STATE_HOVERING_AXIS: self.handle_state_hovering_axis,
            constants.GIZMO_3D_STATE_HOVERING_PLANE: self.handle_state_hovering_plane,
            constants.GIZMO_3D_STATE_TRANSLATING_ON_AXIS: self.handle_state_translate_on_axis,
            constants.GIZMO_3D_STATE_TRANSLATING_ON_PLANE: self.handle_state_translate_on_plane,
            constants.GIZMO_3D_STATE_ROTATE_AROUND_AXIS: self.handle_state_rotate_axis,
        }

    def initialise(self) -> bool:
        """
        Initialises the Gizmo3D system using the parameters given

        :return: bool, TRUE if all steps of initialisation succeeded
        """

        # Stage 1) For every camera, create a gizmo entity and associate their ids
        pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_id, camera_component in pool.items():
            if camera_entity_id in self.camera2gizmo_map:
                continue

            # Create new gizmo entity for this camera
            gizmo_entity_uid = self.scene.add_entity(entity_blueprint=GIZMO_3D_RIG_BLUEPRINT,
                                                     system_owned=True)
            self.camera2gizmo_map[camera_entity_id] = gizmo_entity_uid

            # And make sure only this camera can render it
            gizmo_meshes = self.scene.get_all_sub_entity_components(
                parent_entity_uid=gizmo_entity_uid,
                component_type=constants.COMPONENT_TYPE_MESH)
            for mesh in gizmo_meshes:
                mesh.exclusive_to_camera_uid = camera_entity_id

        # Stage 2) For every gizmo3D, find out which meshes correspond to their respective axes
        pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        for gizmo_3d_entity_uid, gizmo_3d_component in pool.items():

            children_uids = self.scene.get_children_uids(entity_uid=gizmo_3d_entity_uid)

            for index, axis_name in enumerate(constants.GIZMO_3D_AXES_NAME_ORDER):

                for child_uid in children_uids:

                    entity_name = self.scene.get_entity(child_uid).name

                    if entity_name == axis_name:
                        gizmo_3d_component.axes_entities_uids[index] = child_uid
                        continue

        # Step 3) Hide all gizmos before we begin
        self.set_all_gizmo_3d_visibility(visible=False)

        return True

    # ========================================================================
    #                             Event Handling
    # ========================================================================

    def handle_event_entity_selected(self, event_data: tuple):
        self.selected_entity_uid = event_data[0]
        self.set_all_gizmo_3d_visibility(visible=True)
        self.set_gizmo_to_selected_entity()

        # When the entity is selected, the user may choose to keep holding the entity to move it
        if self.gizmo_state == constants.GIZMO_3D_STATE_NOT_HOVERING:
            self.focused_gizmo_plane = constants.GIZMO_3D_PLANE_CAMERA
            self.gizmo_state = constants.GIZMO_3D_STATE_TRANSLATING_ON_PLANE

    def handle_event_entity_deselected(self, event_data: tuple):
        self.selected_entity_uid = None
        self.set_all_gizmo_3d_visibility(visible=False)

    def handle_event_mouse_enter_ui(self, event_data: tuple):
        self.gizmo_selection_enabled = False

    def handle_event_mouse_leave_ui(self, event_data: tuple):
        self.gizmo_selection_enabled = True

    def handle_event_mouse_button_press(self, event_data: tuple):

        """
        This event is called before the "entity_selected", when a entity is selected
        """

        if event_data[constants.EVENT_INDEX_MOUSE_BUTTON_BUTTON] != constants.MOUSE_LEFT:
            return

        if self.selected_entity_uid is None:
            return

        screen_gl_pixels = (event_data[constants.EVENT_INDEX_MOUSE_BUTTON_X],
                            event_data[constants.EVENT_INDEX_MOUSE_BUTTON_Y_OPENGL])
        ray_origin, ray_direction, self.focused_camera_uid = self.screen2ray(screen_gl_pixels=screen_gl_pixels)
        if self.focused_camera_uid is None:
            return

        if ray_origin is None or ray_direction is None:
            return

        self.state_handlers[self.gizmo_state](ray_origin=ray_origin, ray_direction=ray_direction, mouse_press=True)

    def handle_event_mouse_move(self, event_data: tuple):

        # On the "mouse_move" event, the event data is already in gl_pixels coordinates
        self.mouse_screen_position = event_data

        if self.selected_entity_uid is None:
            return

        ray_origin, ray_direction, self.focused_camera_uid = self.screen2ray(screen_gl_pixels=event_data)
        if self.focused_camera_uid is None:
            return

        if ray_origin is None or ray_direction is None:
            return

        self.state_handlers[self.gizmo_state](ray_origin=ray_origin, ray_direction=ray_direction, mouse_press=False)

    def handle_event_parameter_updated(self, event_data: tuple):
        if event_data[0] == "orientation":
            print(f"orientation changed: {event_data[1]}")
            self.gizmo_orientation = event_data[1]

    def handle_event_mouse_button_release(self, event_data: tuple):
        # When the LEFT MOUSE BUTTON is released, it should apply any transforms to the selected entity
        if event_data[constants.EVENT_INDEX_MOUSE_BUTTON_BUTTON] != constants.MOUSE_LEFT:
            return

        # TODO: Which state to move to? For not, I put not hovering, but this will create a bug
        self.gizmo_state = constants.GIZMO_3D_STATE_NOT_HOVERING
        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_LEAVE_GIZMO_3D,
                                     event_data=(None,),
                                     sender=self)
        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_GIZMO_3D_DEACTIVATED,
                                     event_data=(None,),
                                     sender=self)

    # ========================================================================
    #                             State Handling
    # ========================================================================

    def handle_state_not_hovering(self, ray_origin: np.array, ray_direction: np.array, mouse_press: bool):

        # AXIS COLLISION
        self.focused_gizmo_axis_index = self.mouse_ray_check_axes_collision(ray_origin=ray_origin,
                                                                            ray_direction=ray_direction)
        if self.focused_gizmo_axis_index == -1:
            return

        # TODO:PLANE COLLISION

        self.gizmo_state = constants.GIZMO_3D_STATE_HOVERING_AXIS
        self.event_publisher.publish(event_type=constants.EVENT_MOUSE_ENTER_GIZMO_3D,
                                     event_data=(self.focused_gizmo_axis_index,), sender=self)

    def handle_state_hovering_axis(self, ray_origin: np.array, ray_direction: np.array, mouse_press: bool):

        if not self.gizmo_selection_enabled:
            return

        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)

        if mouse_press:
            self.gizmo_state = constants.GIZMO_3D_STATE_TRANSLATING_ON_AXIS
            transform = transform_3d_pool[self.selected_entity_uid]
            self.original_active_local_position = np.array(transform.position, dtype=np.float32)
            self.original_active_world_matrix = transform.world_matrix.copy()
            self.original_active_local_matrix = transform.local_matrix.copy()
            self.local_axis_offset_point = self.get_projected_point_on_axis(ray_origin=ray_origin,
                                                                            ray_direction=ray_direction)
            self.event_publisher.publish(event_type=constants.EVENT_MOUSE_GIZMO_3D_ACTIVATED,
                                         event_data=(self.focused_gizmo_axis_index,),
                                         sender=self)
            return

        # Check if any other axis is now being hovered
        self.focused_gizmo_axis_index = self.mouse_ray_check_axes_collision(ray_origin=ray_origin,
                                                                            ray_direction=ray_direction)
        if self.focused_gizmo_axis_index == -1:
            self.gizmo_state = constants.GIZMO_3D_STATE_NOT_HOVERING
            self.event_publisher.publish(event_type=constants.EVENT_MOUSE_LEAVE_GIZMO_3D,
                                         event_data=(self.focused_gizmo_axis_index,), sender=self)
            return

        # PLANE COLLISION
        # TODO: Add collision check with planes

    def handle_state_hovering_plane(self, ray_origin: np.array, ray_direction: np.array, mouse_press: bool):

        pass

    def handle_state_translate_on_axis(self, ray_origin: np.array, ray_direction: np.array, mouse_press: bool):

        local_point_on_ray_0 = self.get_projected_point_on_axis(ray_origin=ray_origin, ray_direction=ray_direction)
        new_local_position = local_point_on_ray_0 - self.local_axis_offset_point + self.original_active_local_position
        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)

        selected_transform_component = transform_3d_pool[self.selected_entity_uid]
        selected_transform_component.position = tuple(new_local_position)
        selected_transform_component.input_values_updated = True

    def handle_state_translate_on_plane(self, ray_origin: np.array, ray_direction: np.array, mouse_press: bool):

        if self.focused_gizmo_plane == constants.GIZMO_3D_PLANE_CAMERA:

            pass

    def handle_state_rotate_axis(self, screen_gl_pixels: tuple, entering_state: bool):
        pass

    # ========================================================================
    #                            Core functions
    # ========================================================================

    def update(self, elapsed_time: float, context: moderngl.Context) -> bool:

        if self.selected_entity_uid is None:
            return True

        # Get component pools for easy access
        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)
        overlay_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_OVERLAY_2D)

        selected_transform_component = transform_3d_pool[self.selected_entity_uid]
        selected_world_position = np.ascontiguousarray(selected_transform_component.world_matrix[:3, 3])

        camera_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_uid, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_uid]
            gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]

            camera_matrix = transform_3d_pool[camera_entity_uid].world_matrix
            view_matrix = np.eye(4, dtype=np.float32)
            mat4.even_faster_inverse(in_mat4=camera_matrix, out_mat4=view_matrix)

            gizmo_scale = utils_camera.set_gizmo_scale(view_matrix=view_matrix, object_position=selected_world_position)
            viewport_height = camera_component.viewport_pixels[3]
            gizmo_scale *= constants.GIZMO_3D_VIEWPORT_SCALE_COEFFICIENT / viewport_height
            gizmo_transform_component.scale = (gizmo_scale, gizmo_scale, gizmo_scale)

            # TODO: [OPTIMISE] Seting this flag to TRUE every frame, even when nothing changes, wastes CPU time.
            #       It causes the transform_3d to recalcalculate its matrices at every frame.
            gizmo_transform_component.input_values_updated = True

            # Update gizmo's transform parameters for visual feedback
            if self.gizmo_orientation == constants.GIZMO_3D_ORIENTATION_GLOBAL:
                gizmo_transform_component.position = selected_transform_component.position
                gizmo_transform_component.rotation = (0, 0, 0)

            if self.gizmo_orientation == constants.GIZMO_3D_ORIENTATION_LOCAL:
                gizmo_transform_component.position = selected_transform_component.position
                gizmo_transform_component.rotation = selected_transform_component.rotation

            if self.gizmo_state in (constants.GIZMO_3D_STATE_NOT_HOVERING, constants.GIZMO_3D_STATE_HOVERING_AXIS):
                self.dehighlight_gizmo(camera_uid=camera_entity_uid)
                self.highlight_active_gizmo_part(camera_uid=camera_entity_uid)

        return True

    # ========================================================================
    #                            Utility functions
    # ========================================================================

    def update_camera_plane_xy_offset(self, ):
        """
        Incomplete
        :return:
        """
        self.local_camera_plane_offset_xy

    def screen2ray(self, screen_gl_pixels: tuple) -> tuple:
        """
        Converts any position in pixels using the OpenGL coordinates (not the viewport ones!) into a 3D ray with
        origin equal to the position of the camera and direction equal to its respective point on screen.

        All active viewports are tested to see which has the mouse and the ray is generated from it.

        :param screen_gl_pixels: tuple, pixel coordinates where zero os at the lower left corner of the screen
        :return: tuple, (ray_origin, ray_direction) <np.array, np.array>
        """

        active_camera_uid, active_camera_component = self.get_active_camera(screen_gl_pixels=screen_gl_pixels)
        if active_camera_uid is None:
            return None, None, None

        ray_origin, ray_direction = self.get_mouse_ray_point_on_axis(active_camera_uid=active_camera_uid,
                                                                     active_camera_component=active_camera_component)

        return ray_origin, ray_direction, active_camera_uid

    def get_projected_point_on_axis(self, ray_origin: np.array, ray_direction: np.array):
        """
        This function returns the local point on the selected
        :param ray_origin:
        :param ray_direction:
        :return:
        """

        # TODO: [OPTIMIZE] Extract the vectors we want from the transform in the first instance
        axis_origin = np.ascontiguousarray(self.original_active_world_matrix[:3, 3])

        # Select from which axis to take the direction vector from
        if self.gizmo_orientation == constants.GIZMO_3D_ORIENTATION_GLOBAL:
            axis_direction = np.ascontiguousarray(self.gizmo_world_matrix[:3, self.focused_gizmo_axis_index])

        if self.gizmo_orientation == constants.GIZMO_3D_ORIENTATION_LOCAL:
            axis_direction = np.ascontiguousarray(self.original_active_world_matrix[:3, self.focused_gizmo_axis_index])

        world_point_on_ray_0 = ray_intersection.ray2ray_nearest_point_on_ray_0(ray_0_origin=axis_origin,
                                                                               ray_0_direction=axis_direction,
                                                                               ray_1_origin=ray_origin,
                                                                               ray_1_direction=ray_direction)

        inverse_parent_matrix = np.eye(4, dtype=np.float32)
        entity = self.scene.get_entity(entity_uid=self.selected_entity_uid)
        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)

        if entity.parent_uid is None:
            inverse_parent_matrix = np.eye(4, dtype=np.float32)
        else:
            parent_world_matrix = transform_3d_pool[entity.parent_uid].world_matrix
            mat4.fast_inverse(parent_world_matrix, inverse_parent_matrix)

        return mat4.mul_vector3(in_mat4=inverse_parent_matrix, in_vec3=world_point_on_ray_0)

    def get_active_camera(self, screen_gl_pixels: tuple) -> tuple:
        camera_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        active_camera_component = None
        active_camera_uid = None
        for camera_entity_id, camera_component in camera_pool.items():
            if not camera_component.is_inside_viewport(screen_gl_position=screen_gl_pixels):
                continue
            active_camera_component = camera_component
            active_camera_uid = camera_entity_id

        if active_camera_component is None:
            return None, None

        return active_camera_uid, active_camera_component

    def get_mouse_ray_point_on_axis(self, active_camera_uid: int, active_camera_component) -> tuple:

        """
        WHen a gizmo axis is being hovered by the mouse, this function returns where the closes point between that axis
        and the mouse's ray is.

        :param active_camera_uid: int
        :param active_camera_component: Camera
        :return: tuple
        """

        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)

        gizmo_3d_entity_uid = self.camera2gizmo_map[active_camera_uid]

        gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]
        mat4.mul_vectors3(in_mat4=gizmo_transform_component.world_matrix,
                          in_vec3_array=constants.GIZMO_3D_AXES,
                          out_vec3_array=self.gizmo_transformed_axes)

        camera_matrix = transform_3d_pool[active_camera_uid].world_matrix

        viewport_position = utils_camera.screen_gl_position_pixels2viewport_position(
            position_pixels=self.mouse_screen_position,
            viewport_pixels=active_camera_component.viewport_pixels)

        if viewport_position is None:
            return None, None

        ray_direction, ray_origin = utils_camera.screen_pos2world_ray(
            viewport_coord_norm=viewport_position,
            camera_matrix=camera_matrix,
            inverse_projection_matrix=active_camera_component.get_inverse_projection_matrix())

        return ray_origin, ray_direction

    def mouse_ray_check_axes_collision(self, ray_origin: np.array, ray_direction: np.array) -> int:

        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)
        gizmo_3d_entity_uid = self.camera2gizmo_map[self.focused_camera_uid] # TODO [CLEANUP] All I need is the gizmo transform
        gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]

        # TODO: [CLEANUP] Clean this silly code. Change the intersection function to accommodate for this
        points_a = np.array([gizmo_transform_component.position,
                             gizmo_transform_component.position,
                             gizmo_transform_component.position], dtype=np.float32)

        # Perform intersection test
        intersection_distances = np.empty((3,), dtype=np.float32)
        ray_intersection.intersect_ray_capsules(
            ray_origin=ray_origin,
            ray_direction=ray_direction,
            points_a=points_a,
            points_b=self.gizmo_transformed_axes,
            radius=np.float32(0.1 * gizmo_transform_component.scale[0]),
            output_distances=intersection_distances)

        # Retrieve sub-indices of any axes being intersected by the mouse ray
        valid_axis_indices = np.where(intersection_distances > -1.0)[0]
        if valid_axis_indices.size == 0:
            return -1

        # And finally select the closest one to the camera
        return valid_axis_indices[intersection_distances[valid_axis_indices].argmin()]

    def mouse_ray_check_planes_collision(self, active_camera_uid: int, ray_origin: np.array, ray_direction: np.array):
        pass

    def dehighlight_gizmo(self, camera_uid: int):

        gizmo_3d_entity_uid = self.camera2gizmo_map[camera_uid]

        # De-highlight all axes
        material_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_MATERIAL)
        gizmo_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        gizmo_component = gizmo_3d_pool[gizmo_3d_entity_uid]
        for axis_entity_uid in gizmo_component.axes_entities_uids:
            material_pool[axis_entity_uid].state_highlighted = False

    def highlight_active_gizmo_part(self, camera_uid: int):

        if self.gizmo_state == constants.GIZMO_3D_STATE_NOT_HOVERING:
            return

        material_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_MATERIAL)
        gizmo_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        gizmo_component = gizmo_3d_pool[self.camera2gizmo_map[camera_uid]]
        axis_entity_uid = gizmo_component.axes_entities_uids[self.focused_gizmo_axis_index]
        axis_material = material_pool[axis_entity_uid]
        axis_material.state_highlighted = True

    def set_gizmo_to_selected_entity(self):

        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)
        selected_transform_component = transform_3d_pool.get(self.selected_entity_uid, None)

        camera_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        for camera_entity_id, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_id]
            gizmo_transform_component = transform_3d_pool[gizmo_3d_entity_uid]
            gizmo_transform_component.position = selected_transform_component.position
            gizmo_transform_component.rotation = selected_transform_component.rotation
            gizmo_transform_component.input_values_updated = True

    def set_all_gizmo_3d_visibility(self, visible=True):

        camera_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_CAMERA)
        gizmo_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_GIZMO_3D)
        mesh_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_MESH)

        for camera_entity_id, camera_component in camera_pool.items():

            gizmo_3d_entity_uid = self.camera2gizmo_map[camera_entity_id]
            gizmo_3d_component = gizmo_3d_pool[gizmo_3d_entity_uid]

            for mesh_entity_uid in gizmo_3d_component.axes_entities_uids:
                mesh_pool[mesh_entity_uid].visible = visible
