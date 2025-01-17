import numpy as np
import moderngl
import logging

from src.core import constants
from src.core.scene import Scene
from src.systems.system import System
from src.core.event_publisher import EventPublisher
from src.core.action_publisher import ActionPublisher
from src.math import mat4

# DEBUG


class TransformSystem(System):

    name = "transform_system"

    __slots__ = [
        "update_tree",
        "entity_uid_update_order"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.entity_uid_update_order = []  # Ordered as a DAG
        self.update_tree = True

    def initialise(self) -> bool:
        return True

    def update(self, elapsed_time: float, context: moderngl.Context) -> bool:

        if self.update_tree:
            self.update_transform_tree()
            self.update_tree = False

        transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_TRANSFORM)
        multi_transform_3d_pool = self.scene.get_pool(component_type=constants.COMPONENT_TYPE_MULTI_TRANSFORM_3D)

        # TODO: [OPTIMIZE] Not all world matrices need to be recreated all the time! Take the dirty flags into account!
        for entity_uid in self.entity_uid_update_order:

            entity = self.scene.entities[entity_uid]
            transform = transform_3d_pool.get(entity_uid, None)
            if transform is None:
                continue

            local_matrix_updated = transform.update()

            if entity.parent_uid:
                parent_transform = transform_3d_pool[entity.parent_uid]
                transform.world_matrix = parent_transform.world_matrix @ transform.local_matrix
            else:
                transform.world_matrix = transform.local_matrix

            mat4.even_faster_inverse(in_mat4=transform.world_matrix,
                                     out_mat4=transform.inverse_world_matrix)

            # Multi-transform update
            multi_transform = multi_transform_3d_pool.get(entity_uid)
            if multi_transform is None:
                continue

            if local_matrix_updated:
                multi_transform.world_matrices = np.matmul(transform.world_matrix, multi_transform.local_matrices)
                multi_transform.world_matrices = multi_transform.world_matrices.transpose((0, 2, 1))
                multi_transform.dirty = True

        # ================= Process actions =================

        self.select_next_action()
        if self.current_action is None:
            return True

        return True

    def update_transform_tree(self):

        temp_update_order = []

        # Populate list out-of-order
        uid2index = {}
        for index, (entity_uid, entity) in enumerate(self.scene.entities.items()):
            uid2index[entity_uid] = index
            temp_update_order.append((entity_uid, entity.parent_uid if entity.parent_uid is not None else -1))

        order_array = np.array(temp_update_order, dtype=np.int32)

        # Sort list so that no child is updated before its parent
        for index in range(order_array.shape[0]):

            entity_uid = order_array[index, 0]
            parent_uid = order_array[index, 1]

            if parent_uid == -1:
                continue

            # Ir parent comes after the child, swap them
            while uid2index[parent_uid] > index:

                parent_index = uid2index[parent_uid]

                temp = order_array[index, :].copy()
                order_array[index, :] = order_array[parent_index, :].copy()
                order_array[parent_index, :] = temp

                uid2index[entity_uid] = parent_index
                uid2index[parent_uid] = index
                break

        # Now we can get rid of the map
        self.entity_uid_update_order = order_array[:, 0].tolist()
