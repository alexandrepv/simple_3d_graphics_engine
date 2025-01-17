import os
import numpy as np

# =============================================================================
#                                Directories
# =============================================================================

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src3")
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
SHADERS_DIR = os.path.join(SRC_DIR, "shaders")

# =============================================================================
#                                GLOBAL
# =============================================================================

DEFAULT_BACKGROUND_COLOR = (0.09803921568, 0.09803921568, 0.09803921568)
DEFAULT_EDITOR_PROFILING_UPDATE_PERIOD = 0.5  # Seconds
DEFAULT_EDITOR_WINDOW_SIZE = (1600, 900)  # (1280, 720)
DEFAULT_EDITOR_DOUBLE_CLICK_TIME_THRESHOLD = 0.5  # in seconds - Windows default is 500ms

# =============================================================================
#                                Events
# =============================================================================

# Basic types
EVENT_KEYBOARD_PRESS = "keyboard_press"            # args: (key, scancode, mods) <int, int, int>
EVENT_KEYBOARD_RELEASE = "keyboard_release"        # args: (key, scancode, mods) <int, int, int>
EVENT_KEYBOARD_REPEAT = "keyboard_repeat"          # args: (key, scancode, mods) <int, int, int>
EVENT_MOUSE_ENTER_UI = "mouse_enter_ui"
EVENT_MOUSE_LEAVE_UI = "mouse_leave_ui"
EVENT_MOUSE_BUTTON_PRESS = "mouse_button_press"    # args: (button, mods, x, y) <int, int, int, int>
EVENT_MOUSE_BUTTON_RELEASE = "mouse_button_release"  # args: (button, mods, x, y) <int, int, int, int>
EVENT_MOUSE_DRAG = "mouse_drag"             # args: (x, y_gl, y_gui, dx, dy) <float, float, float, float, float>
EVENT_MOUSE_MOVE = "mouse_move"             # args: (x, y_gl, y_gui, dx, dy) <float, float, float, float, float>
EVENT_MOUSE_SCROLL = "mouse_scroll"                # args: (GIZMO_PLANE_OFFSET_x, GIZMO_PLANE_OFFSET_y) <float, float>
EVENT_MOUSE_DOUBLE_CLICK = "mouse_double_click"
EVENT_MOUSE_ENTER_GIZMO_3D = "mouse_enter_gizmo_3d"
EVENT_MOUSE_LEAVE_GIZMO_3D = "mouse_leave_gizmo_3d"
EVENT_MOUSE_GIZMO_3D_ACTIVATED = "mouse_gizmo_3d_activated"
EVENT_MOUSE_GIZMO_3D_DEACTIVATED = "mouse_gizmo_3d_deactivated"
EVENT_EXIT_APPLICATION = "exit_application"
EVENT_ENTITY_SELECTED = "entity_selected"
EVENT_ENTITY_DESELECTED = "entity_deselected"
EVENT_MULTIPLE_ENTITIES_SELECTED = "multiple_entities_selected"
EVENT_PROFILING_SYSTEM_PERIODS = "profiling_system_periods"  # args (("system_a", 0.2), ("system_b" 0.37), ...) <(string, float) ...>
EVENT_WINDOW_SIZE = "window_size"                           # args: (width, height) <int, int>
EVENT_WINDOW_FRAMEBUFFER_SIZE = "window_framebuffer_size"   # args: (width, height) <int, int>
EVENT_WINDOW_DROP_FILES = "window_drop_files"               # args: (filepath, ...) <str, ...>

# =============================================================================
#                             ModernGL Variables
# =============================================================================

# Input buffer names
SHADER_INPUT_POSITION = "in_position"
SHADER_INPUT_NORMAL = "in_normal"
SHADER_INPUT_COLOR = "in_color"
SHADER_INPUT_JOINT = "in_joint"
SHADER_INPUT_WEIGHT = "in_weight"
SHADER_INPUT_UV = "in_uv"

# Meshes
MESH_RENDER_MODE_POINTS = 0x0000     # Value from ModernGL -> also matches OpenGL
MESH_RENDER_MODE_LINES = 0x0001      # Value from ModernGL -> also matches OpenGL
MESH_RENDER_MODE_TRIANGLES = 0x0004  # Value from ModernGL -> also matches OpenGL
MESH_RENDER_MODES = {
    "points": MESH_RENDER_MODE_POINTS,
    "lines": MESH_RENDER_MODE_LINES,
    "triangles": MESH_RENDER_MODE_TRIANGLES
}
MESH_LIGHTING_MODE_SOLID = 0
MESH_LIGHTING_MODE_LIT = 0

# Uniform Buffer Object binding points. They should match the GLSL code:
# E.G: layout (std140, binding = 0) uniform UBO_MVP { ... }
UBO_BINDING_MVP = 0
UBO_BINDING_LIGHTS = 0


# =============================================================================
#                                BEZIER CURVE
# =============================================================================

BEZIER_COEFFS = np.array([[-1,  3, -3, 1],
                          [ 3, -6,  3, 0],
                          [-3,  3,  0, 0],
                          [ 1,  0,  0, 0]], dtype=np.float32)

# =============================================================================
#                                CAMERA 3D
# =============================================================================

CAMERA_SPEED_NORMAL = 2.5
CAMERA_SPEED_FAST = 7.0

# =============================================================================
#                                INPUT
# =============================================================================

MOUSE_LEFT = 1
MOUSE_RIGHT = 2
MOUSE_MIDDLE = 3
MOUSE_BUTTONS = (MOUSE_LEFT, MOUSE_RIGHT, MOUSE_MIDDLE)
MOUSE_POSITION = 'position'
MOUSE_POSITION_LAST_FRAME = 'position_last_frame'
MOUSE_SCROLL_POSITION = 'scroll_position'
MOUSE_SCROLL_POSITION_LAST_FRAME = 'scroll_position_last_frame'

BUTTON_PRESSED = 0
BUTTON_DOWN = 1
BUTTON_RELEASED = 2
BUTTON_UP = 3

# Keyboard
KEYBOARD_SIZE = 512
KEY_STATE_DOWN = 0
KEY_STATE_UP = 1
KEY_LEFT_CTRL = 65507
KEY_LEFT_SHIFT = 65505
KEY_LEFT_ALT = 65513

