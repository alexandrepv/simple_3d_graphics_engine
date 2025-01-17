import logging
import moderngl
from collections import deque

from src.core.scene import Scene
from src.core.event_publisher import EventPublisher
from src.core.action_publisher import ActionPublisher
from src.core.data_manager import DataManager


class System:

    __slots__ = [
        "logger",
        "event_publisher",
        "action_publisher",
        "data_manager",
        "scene",
        "action_queue",
        "current_action",
        "parameters",
        "event_handlers",
        "average_update_period",
        "sum_update_periods",
        "num_updates"
    ]

    name = "base_system"

    def __init__(self,
                 logger: logging.Logger,
                 scene: Scene,
                 event_publisher: EventPublisher,
                 action_publisher: ActionPublisher,
                 data_manager: DataManager,
                 parameters: dict,
                 **kwargs):

        self.logger = logger
        self.event_publisher = event_publisher
        self.action_publisher = action_publisher
        self.data_manager = data_manager
        self.action_queue = deque()
        self.current_action = None
        self.scene = scene
        self.parameters = parameters

        # Event handling variables
        self.event_handlers = {}

        # Profiling variables
        self.average_update_period = -1.0
        self.sum_update_periods = 0.0
        self.num_updates = 0

    def on_event(self, event_type: int, event_data: tuple):
        handler = self.event_handlers.get(event_type, None)
        if handler is None:
            return
        handler(event_data=event_data)

    def on_action(self, action_type: int, action_data: tuple, entity_id: int, component_type: int):
        self.action_queue.appendleft((action_type, action_data, entity_id, component_type))

    def select_next_action(self) -> None:
        """
        Whatever part of the algorithm is performing an action, nas to set the self.current_action to None
        once it is done, so that the "select_next_action" can kick in
        """

        if self.current_action is None and len(self.action_queue) > 0:
            self.current_action = self.action_queue.pop()

    def initialise(self) -> bool:
        return True

    def update(self,
               elapsed_time: float,
               context: moderngl.Context) -> bool:
        return True

    def shutdown(self):
        pass
