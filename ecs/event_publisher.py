from ecs import constants
from ecs.systems.system import System


class EventPublisher:

    __slots__ = ["listeners"]

    def __init__(self):

        # Do it manually here to avoid having to check at every publish() call
        self.listeners = {
            constants.EVENT_KEYBOARD_PRESS: [],
            constants.EVENT_KEYBOARD_RELEASE: [],
            constants.EVENT_KEYBOARD_REPEAT: [],
            constants.EVENT_MOUSE_BUTTON_PRESS: [],
            constants.EVENT_MOUSE_BUTTON_RELEASE: [],
            constants.EVENT_MOUSE_MOVE: [],
            constants.EVENT_MOUSE_SCROLL: [],
            constants.EVENT_WINDOW_RESIZE: [],
            constants.EVENT_WINDOW_FRAMEBUFFER_RESIZE: [],
            constants.EVENT_WINDOW_DROP_FILES: [],
        }

    def subscribe(self, event_type: int, listener: System):
        # Add listener to list of that particular event
        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type, listener: System):
        if listener in self.listeners[event_type]:
            self.listeners[event_type].remove(listener)

    def publish(self, event_type, event_data: tuple):
        for listener in self.listeners[event_type]:
            listener.on_event(event_type=event_type, event_data=event_data)