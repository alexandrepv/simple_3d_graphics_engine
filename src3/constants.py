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

DEFAULT_EDITOR_PROFILING_UPDATE_PERIOD = 0.5  # Seconds
DEFAULT_EDITOR_WINDOW_SIZE = (1600, 900)  # (1280, 720)
DEFAULT_EDITOR_DOUBLE_CLICK_TIME_THRESHOLD = 0.5  # in seconds - Windows default is 500ms

# =============================================================================
#                                GIZMO 3D
# =============================================================================

GIZMO_AXIS_SEGMENT_LENGTH = 1000.0
GIZMO_AXIS_DETECTION_RADIUS = 0.0025
GIZMO_MODE_TRANSLATION = "translation"
GIZMO_MODE_ROTATION = "rotation"
GIZMO_MODE_SCALE = "scale"

GIZMO_STATE_INACTIVE = "inactive"
GIZMO_STATE_HOVERING_AXES = "hovering_axes"
GIZMO_STATE_HOVERING_PLANES = "hovering_planes"
GIZMO_STATE_HOVERING_CENTER = "hovering_center"
GIZMO_STATE_START_DRAGGING = "start_dragging"
GIZMO_STATE_DRAGGING_AXIS = "dragging_axis"
GIZMO_STATE_DRAGGING_PLANE = "dragging_plane"

GIZMO_AXIS_LENGTH = 1.0
GIZMO_AXIS_LINE_WIDTH = 5.0
GIZMO_PLANE_LINE_WIDTH = 3.0
GIZMO_PLANE_SIZE = 0.2
GIZMO_PLANE_OFFSET = 0.1

GIZMO_X_AXIS_VERTICES = [
    [0.0, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH, 1.0, 0.0, 0.0, 1.0],
    [GIZMO_AXIS_LENGTH, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH, 1.0, 0.0, 0.0, 1.0]
]

GIZMO_Y_AXIS_VERTICES = [
    [0.0, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH, 0.0, 1.0, 0.0, 1.0],
    [0.0, GIZMO_AXIS_LENGTH, 0.0, GIZMO_AXIS_LINE_WIDTH, 0.0, 1.0, 0.0, 1.0]
]

GIZMO_Z_AXIS_VERTICES = [
    [0.0, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH, 0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, GIZMO_AXIS_LENGTH, GIZMO_AXIS_LINE_WIDTH, 0.0, 0.0, 1.0, 1.0]
]

GIZMO_XY_PLANE_VERTICES = [
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],

    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],

    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],

    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH, 1.0, 1.0, 0.0, 1.0],
]

GIZMO_XZ_PLANE_VERTICES = [
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],

    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],

    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],

    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 1.0, 0.0, 1.0, 1.0],
]

GIZMO_YZ_PLANE_VERTICES = [
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],

    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],

    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],

    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH, 0.0, 1.0, 1.0, 1.0],
]

# Concatenate all vertices into a single numpy array
GIZMO_TRANSLATION_VERTICES = np.array(
    GIZMO_X_AXIS_VERTICES + GIZMO_Y_AXIS_VERTICES + GIZMO_Z_AXIS_VERTICES +
    GIZMO_XY_PLANE_VERTICES + GIZMO_XZ_PLANE_VERTICES + GIZMO_YZ_PLANE_VERTICES,
    dtype='f4'
)

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