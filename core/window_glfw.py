import glfw
import numpy as np
from core import constants as constants


class WindowGLFW:

    """
    The WindowGLFW is a wrapper around the GLFW module to simplify development.
    A window is created when the costructor is called and should be utilised as:

    window = WindowGLFW(...)
    while not window.should_close():
        window.pool_events()

        # Your render code here

        window.swap_buffers()
    window.terminate()

    """
    
    __slots__ = ('window_size',
                 'window_title',
                 'vertical_sync',
                 'mouse_state',
                 'keyboard_state',
                 'window_glfw')
    
    # ========================================================================
    #                          Initialization functions
    # ========================================================================

    def __init__(self,
                 window_size=constants.WINDOW_DEFAULT_SIZE,
                 window_title=constants.WINDOW_DEFAULT_TITLE,
                 vertical_sync=False):

        # ModernGL variables
        self.window_size = window_size
        self.window_title = window_title
        self.vertical_sync = vertical_sync

        # Input variables
        self.mouse_state = self.initialise_mouse_state()
        self.keyboard_state = self.initialise_keyboard_state()

        if not glfw.init():
            raise ValueError("[ERROR] Failed to initialize GLFW")

        # TODO: Find out about samples hing before creating the window
        glfw.window_hint(glfw.SAMPLES, 4)

        self.window_glfw = glfw.create_window(width=self.window_size[0],
                                              height=self.window_size[1],
                                              title=window_title,
                                              monitor=None,
                                              share=None)

        # Create a windowed mode window and its OpenGL context
        if not self.window_glfw:
            glfw.terminate()
            raise Exception('[ERROR] Could not create GLFW window.')

        glfw.make_context_current(self.window_glfw)
        glfw.swap_interval(1 if self.vertical_sync else 0)

        # Assign callback functions
        glfw.set_key_callback(self.window_glfw, self.key_callback)
        glfw.set_cursor_pos_callback(self.window_glfw, self.mouse_move_callback)
        glfw.set_mouse_button_callback(self.window_glfw, self.mouse_button_callback)
        glfw.set_window_size_callback(self.window_glfw, self.window_resize_callback)
        glfw.set_scroll_callback(self.window_glfw, self.mouse_scroll_callback)
        glfw.set_framebuffer_size_callback(self.window_glfw, self.framebuffer_size_callback)
        glfw.set_drop_callback(self.window_glfw, self.drop_files_callback)
        
        # Update any initialisation variables after window GLFW has been created, if needed
        self.mouse_state[constants.MOUSE_POSITION] = glfw.get_cursor_pos(self.window_glfw)
        
    # ========================================================================
    #                           Input State Functions
    # ========================================================================

    def initialise_mouse_state(self) -> dict:
        return {
            constants.MOUSE_LEFT: constants.BUTTON_UP,
            constants.MOUSE_RIGHT: constants.BUTTON_UP,
            constants.MOUSE_MIDDLE: constants.BUTTON_UP,
            constants.MOUSE_POSITION: (0, 0),
            constants.MOUSE_POSITION_LAST_FRAME: (0, 0),
            constants.MOUSE_SCROLL_POSITION: 0
        }
        
    def initialise_keyboard_state(self) -> np.array:
        return np.ones((constants.KEYBOARD_SIZE,), dtype=np.int8) * constants.KEY_STATE_UP
    
    # ========================================================================
    #                       Window Callback functions
    # ========================================================================

    def key_callback(self, glfw_window, key, scancode, action, mods):
        if action == glfw.PRESS:
            self.keyboard_state[key] = constants.KEY_STATE_DOWN
        if action == glfw.RELEASE:
            self.keyboard_state[key] = constants.KEY_STATE_UP

    def mouse_button_callback(self, glfw_window, button, action, mods):
        
        for button in constants.MOUSE_BUTTONS:
            # NOTE: Button numbers already match the GLFW numbers in the constants
            if action == glfw.PRESS:
                self.mouse_state[button] = constants.BUTTON_PRESSED
            if action == glfw.RELEASE:
                self.mouse_state[button] = constants.BUTTON_RELEASED

    def mouse_move_callback(self, glfw_window, x, y):
        self.mouse_state[constants.MOUSE_POSITION] = (x, y)

    def mouse_scroll_callback(self, glfw_window, x_offset, y_offset):
        self.mouse_state[constants.MOUSE_SCROLL_POSITION] += y_offset
        print(self.mouse_state[constants.MOUSE_SCROLL_POSITION])

    def window_resize_callback(self, glfw_window, width, height):
        self.window_size = (width, height)

    def framebuffer_size_callback(self, glfw_window, width, height):
        raise NotImplementedError('[ERROR] Function not implemented')
    
    def drop_files_callback(self, glfw_window, file_list):
        raise NotImplementedError('[ERROR] Function not implemented')
    
    def update_inputs_per_frame(self):
        
        # Mouse Inputs
        for button in constants.MOUSE_BUTTONS:
            if self.mouse_state[button] == constants.BUTTON_PRESSED:
                self.mouse_state[button] = constants.BUTTON_DOWN
                
            if self.mouse_state[button] == constants.BUTTON_RELEASED:
                self.mouse_state[button] = constants.BUTTON_UP
                
        self.mouse_state[constants.MOUSE_POSITION_LAST_FRAME] = self.mouse_state[constants.MOUSE_POSITION]
        self.mouse_state[constants.MOUSE_SCROLL_POSITION_LAST_FRAME] = self.mouse_state[constants.MOUSE_SCROLL_POSITION]

    # ========================================================================
    #                             Main Functions
    # ========================================================================

    def should_close(self):
        return glfw.window_should_close(self.window_glfw)

    def pool_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window_glfw)

    def terminate(self):
        glfw.terminate()