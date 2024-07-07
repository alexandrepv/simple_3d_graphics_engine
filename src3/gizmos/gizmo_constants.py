import numpy as np

# =============================================================================
#                               Transform Gizmo
# =============================================================================

GIZMO_SIZE_ON_SCREEN_PIXELS = 150.0

GIZMO_CENTER_RADIUS = 0.1
GIZMO_CENTER_RADIUS_2 = GIZMO_CENTER_RADIUS ** 2

GIZMO_DISK_RADIUS = 0.5
GIZMO_DISK_RADIUS_2 = GIZMO_DISK_RADIUS ** 2

GIZMO_PLANE_LINE_WIDTH = 3.0
GIZMO_PLANE_SIZE = 0.25
GIZMO_PLANE_OFFSET = 0.25

GIZMO_AXIS_OFFSET = 0.2
GIZMO_AXIS_OFFSET_2 = GIZMO_AXIS_OFFSET ** 2
GIZMO_AXIS_LENGTH = 1.0
GIZMO_AXIS_LINE_WIDTH = 5.0
GIZMO_AXIS_GUIDE_LINE_WIDTH = 3.0
GIZMO_AXIS_SEGMENT_LENGTH = 1000.0
GIZMO_AXIS_DETECTION_RADIUS = 0.075
GIZMO_AXIS_DETECTION_RADIUS_2 = GIZMO_AXIS_DETECTION_RADIUS ** 2

GIZMO_ORIENTATION_GLOBAL = "global"
GIZMO_ORIENTATION_LOCAL = "local"
GIZMO_ORIENTATIONS = [
    GIZMO_ORIENTATION_GLOBAL,
    GIZMO_ORIENTATION_LOCAL
]

GIZMO_MODE_TRANSLATION = "translation"
GIZMO_MODE_ROTATION = "rotation"
GIZMO_MODE_SCALE = "scale"
GIZMO_MODES = [
    GIZMO_MODE_TRANSLATION,
    GIZMO_MODE_ROTATION,
    GIZMO_MODE_SCALE
]

GIZMO_STATE_INACTIVE = "inactive"
GIZMO_STATE_HOVERING_AXIS = "hovering_axis"
GIZMO_STATE_HOVERING_PLANE = "hovering_plane"
GIZMO_STATE_HOVERING_CENTER = "hovering_center"
GIZMO_STATE_HOVERING_DISK = "hovering_disk"
GIZMO_STATE_DRAGGING_AXIS = "dragging_axis"
GIZMO_STATE_DRAGGING_PLANE = "dragging_plane"
GIZMO_STATE_DRAGGING_CENTER = "dragging_center"
GIZMO_STATE_DRAGGING_DISK = "dragging_disk"

GIZMO_HIGHLIGHT = [0.8, 0.8, 0.0]

GIZMO_AXIS_X_COLOR_NORMAL = [1.0, 0.0, 0.0]
GIZMO_AXIS_Y_COLOR_NORMAL = [0.0, 1.0, 0.0]
GIZMO_AXIS_Z_COLOR_NORMAL = [0.0, 0.0, 1.0]

GIZMO_PLANE_XY_COLOR_NORMAL = [0.0, 0.0, 1.0]
GIZMO_PLANE_XZ_COLOR_NORMAL = [0.0, 1.0, 0.0]
GIZMO_PLANE_YZ_COLOR_NORMAL = [1.0, 0.0, 0.0]

GIZMO_MODE_TRANSLATION_VERTICES = np.array([
    # Axis X
    [GIZMO_AXIS_OFFSET, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH],
    [GIZMO_AXIS_OFFSET + GIZMO_AXIS_LENGTH, 0.0, 0.0, GIZMO_AXIS_LINE_WIDTH],

    # Axis Y
    [0.0, GIZMO_AXIS_OFFSET, 0.0, GIZMO_AXIS_LINE_WIDTH],
    [0.0, GIZMO_AXIS_OFFSET + GIZMO_AXIS_LENGTH, 0.0, GIZMO_AXIS_LINE_WIDTH],

    # Axis Z
    [0.0, 0.0, GIZMO_AXIS_OFFSET, GIZMO_AXIS_LINE_WIDTH],
    [0.0, 0.0, GIZMO_AXIS_OFFSET + GIZMO_AXIS_LENGTH, GIZMO_AXIS_LINE_WIDTH],

    # Plane XY
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_LINE_WIDTH],

    # Plane XZ
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [GIZMO_PLANE_OFFSET, 0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],

    # Plane YZ
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET + GIZMO_PLANE_SIZE, GIZMO_PLANE_LINE_WIDTH],
    [0.0, GIZMO_PLANE_OFFSET, GIZMO_PLANE_OFFSET, GIZMO_PLANE_LINE_WIDTH],
], dtype='f4')

GIZMO_MODE_TRANSLATION_DEFAULT_COLORS = np.array([

    # Axis X [0] - in floats
    GIZMO_AXIS_X_COLOR_NORMAL,
    GIZMO_AXIS_X_COLOR_NORMAL,

    # Axis Y [8]
    GIZMO_AXIS_Y_COLOR_NORMAL,
    GIZMO_AXIS_Y_COLOR_NORMAL,

    # Axis Z [12]
    GIZMO_AXIS_Z_COLOR_NORMAL,
    GIZMO_AXIS_Z_COLOR_NORMAL,

    # Plane XY [44]
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,
    GIZMO_PLANE_XY_COLOR_NORMAL,

    # Plane XZ [76]
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,
    GIZMO_PLANE_XZ_COLOR_NORMAL,

    # Plane YZ [108]
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL,
    GIZMO_PLANE_YZ_COLOR_NORMAL
], dtype='f4')

GIZMO_TRANSLATION_VERTICES_AXIS_GUIDE = np.array(
    [   # These values are placeholders. They are overwritten dynamically
        [-10.0, 0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 1.0],
        [10.0, 0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 1.0]
    ],
    dtype='f4'
)

GIZMO_MODE_TRANSLATION_RANGES = {
    (GIZMO_STATE_HOVERING_AXIS, 0): (0, 2),
    (GIZMO_STATE_HOVERING_AXIS, 1): (2, 4),
    (GIZMO_STATE_HOVERING_AXIS, 2): (4, 6),
    (GIZMO_STATE_DRAGGING_AXIS, 0): (0, 2),
    (GIZMO_STATE_DRAGGING_AXIS, 1): (2, 4),
    (GIZMO_STATE_DRAGGING_AXIS, 2): (4, 6),

    (GIZMO_STATE_HOVERING_PLANE, 0): (6, 14),
    (GIZMO_STATE_HOVERING_PLANE, 1): (14, 22),
    (GIZMO_STATE_HOVERING_PLANE, 2): (22, 30),
    (GIZMO_STATE_DRAGGING_PLANE, 0): (6, 14),
    (GIZMO_STATE_DRAGGING_PLANE, 1): (14, 22),
    (GIZMO_STATE_DRAGGING_PLANE, 2): (22, 30),
}