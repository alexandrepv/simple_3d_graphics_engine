# Default Values
DEFAULT_DIR_STYLES = "core/styles"
DEFAULT_DIR_FONTS = "core/fonts"
DEFAULT_DIR_BLUEPRINTS = "core/blueprints"
DEFAULT_STYLE_NAME = 'default'
DEFAULT_WIDGET_SIZE = -1.0  # The notation -1.0 means 100% of the available space
DEFAULT_WIDGET_MAX_NUM_VERTICES = 1000
DEFAULT_PADDING_TOP_INDEX = 0
DEFAULT_PADDING_LEFT_INDEX = 1
DEFAULT_PADDING_BOTTOM_INDEX = 2
DEFAULT_PADDING_RIGHT_INDEX = 3

# OpenGL
OPENGL_VERSION = 330


# Fonts
FONT_NUM_VERTICES_PER_CHAR = 12
FONT_CHAR_SIZE = 32  # Resolution dpi, not actual pixels
FONT_SHEET_ROWS = 16
FONT_SHEET_COLS = 16
FONT_SHEET_CELL_WIDTH = 32
FONT_SHEET_CELL_HEIGHT = 32
FONT_NUM_GLYPHS = FONT_SHEET_ROWS * FONT_SHEET_COLS
FONT_TEXTURE_WIDTH = FONT_SHEET_CELL_WIDTH * FONT_SHEET_COLS
FONT_TEXTURE_HEIGHT = FONT_SHEET_CELL_HEIGHT * FONT_SHEET_ROWS

# UI Widget alignments
ALIGN_TOP = 0
ALIGN_LEFT = 1
ALIGN_CENTER = 2
ALIGN_BOTTOM = 3
ALIGN_RIGHT = 3
VALID_HORIZONTAL_ALIGN = (ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT)
VALID_VERTICAL_ALIGN = (ALIGN_TOP, ALIGN_CENTER, ALIGN_BOTTOM)
DEFAULT_SPACING_ROW = 5
DEFAULT_SPACING_COLUMN = 5

# UI Widgets Type IDs
WIDGET_TYPE_WINDOW = "window"
WIDGET_TYPE_ROW = "row"
WIDGET_TYPE_COLUMN = "column"
WIDGET_TYPE_BUTTON = "button"
WIDGET_TYPE_MAP = {
    WIDGET_TYPE_WINDOW: 0,
    WIDGET_TYPE_ROW: 1,
    WIDGET_TYPE_COLUMN: 2,
    WIDGET_TYPE_BUTTON: 3,
}
WIDGET_TYPE_INV_MAP = {
    0: WIDGET_TYPE_WINDOW,
    1: WIDGET_TYPE_ROW,
    2: WIDGET_TYPE_COLUMN,
    3: WIDGET_TYPE_BUTTON
}

# UI Definitions
MAX_WIDGETS = 200
MAX_STATIC_TEXTS = 1000
MAX_STATIC_TEXT_SIZE = 32  # 32 characters per

# UI Blueprint Sections
BLUEPRINT_FONT = 'font'
BLUEPRINT_STYLES = 'styles'
BLUEPRINT_LAYOUT = 'layout'

# UI Themes
THEME_EDGE_WIDTH = 'edge_width'
THEME_EDGE_COLOR_UP = 'edge_color_up'
THEME_EDGE_COLOR_HOVER = 'edge_color_hover'
THEME_EDGE_COLOR_DOWN = 'edge_color_down'
THEME_BACKGROUND_COLOR_UP = 'edge_color_up'
THEME_BACKGROUND_COLOR_HOVER = 'edge_color_hover'
THEME_BACKGROUND_COLOR_DOWN = 'edge_color_down'
THEME_PADDING = 'padding'

# UI Widgets XML attribute keys
WIDGET_TYPE = 'type'
WIDGET_ID = 'id'
WIDGET_WIDTH = 'width'
WIDGET_HEIGHT = 'height'
WIDGET_X = 'x'
WIDGET_Y = 'y'
WIDGET_V_ALIGN = 'vertical_alignment'
WIDGET_H_ALIGN = 'horizontal_alignment'

WIDGET_NUMERICAL_IDS = (
    WIDGET_WIDTH,
    WIDGET_HEIGHT,
    WIDGET_X,
    WIDGET_Y
)

# XML attribute keys
KEY_ATTRS_ID = "id"
KEY_ATTRS_WIDTH = "width"
KEY_ATTRS_HEIGHT = "height"
KEY_ATTRS_ALIGNMENT = "alignment"
KEY_ATTRS_SPACING = "spacing"
KEY_ELEMENT_UI = "ui"
KEY_ELEMENT_WINDOW = "window"
KEY_ELEMENT_ROW = "row"
KEY_ELEMENT_COLUMN = "column"
KEY_ELEMENT_BUTTON = "button"
KEY_ELEMENT_TEXT_FIELD = "text_field"