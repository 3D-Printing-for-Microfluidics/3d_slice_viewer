from panda3d.core import Point3, Vec4, WindowProperties, TextNode
from direct.gui import DirectGuiGlobals as DGG

# Window settings
WINDOW_TITLE = "3D Slice Viewer"
WINDOW_SIZE = (1400, 800)
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
CONTROL_PANEL_WIDTH = 220

# Camera settings
INITIAL_CAMERA_DISTANCE = 5000.0
MIN_CAMERA_DISTANCE = 10
MAX_CAMERA_DISTANCE = 50000
INITIAL_CAMERA_H = 45
INITIAL_CAMERA_P = 35
INITIAL_CAMERA_POS = Point3(80, -80, 80)
INITIAL_CAMERA_TARGET = Point3(0, 0, 0)

# Camera control settings
ROTATION_SPEED = 100
PAN_SPEED_FACTOR = 0.5
ZOOM_SPEED_FACTOR = 0.5
WHEEL_ZOOM_FACTOR = 0.9  # For zooming in (use reciprocal for zooming out)

# Colors
EXPOSURE_COLORS = [
    "#ee6352",  # Bittersweet Red
    "#59cd90",  # Emerald
    "#3fa7d6",  # Picton Blue
    "#fac05e",  # Xanthous Yellow
    "#f79d84",  # Atomic Tangerine
    "#a3c4f3",  # Periwinkle
    "#b39ddb",  # Lavender
    "#6a0136",  # Tyrian Purple
]
MENU_FRAME_COLOR = Vec4(0.2, 0.2, 0.2, 0.8)
BUTTON_COLOR = Vec4(0.3, 0.3, 0.3, 1.0)
BUTTON_ACTIVE_COLOR = Vec4(0.4, 0.6, 0.4, 1.0)
BUTTON_INACTIVE_COLOR = Vec4(0.6, 0.3, 0.3, 1.0)
TEXT_COLOR = Vec4(1, 1, 1, 1)
HELP_TEXT_COLOR = Vec4(1, 1, 1, 0.7)
ENTRY_BG_COLOR = Vec4(0.15, 0.15, 0.15, 1.0)
BG_COLOR = "#2b2b2b"
FG_COLOR = "#ffffff"
BUTTON_BG = "#2b2b2b"
BUTTON_FG = "#ffffff"
ENTRY_BG = "#45494a"
ENTRY_FG = "#ffffff"

# Fonts
FONT_FAMILY = "Arial"
FONT_SIZE = 10
HEADER_FONT_SIZE = 12

# Padding and margins
PADDING = 5
SECTION_PADDING = 10

# # Layer visualization
# EXPOSURE_COLORS = {
#     'normal': Vec4(0.7, 1.0, 0.7, 0.1),  # Green tint for normal exposure
#     'long': Vec4(1.0, 0.7, 0.7, 0.1),    # Red tint for long exposure
#     'short': Vec4(0.7, 0.7, 1.0, 0.1)    # Blue tint for short exposure
# }
# EXPOSURE_THRESHOLD_LONG = 1.5  # Multiplier above default exposure
# EXPOSURE_THRESHOLD_SHORT = 0.5  # Multiplier below default exposure

# Gradient colors
GRADIENT_SHORT_COLOR = Vec4(0.0, 0.0, 1.0, 1.0)  # Blue with full opacity
GRADIENT_LONG_COLOR  = Vec4(1.0, 0.0, 0.0, 1.0)  # Red with full opacity

def lerp_color(v1, v2, t):
    """
    Linearly interpolate between two Vec4 colors.
    t is clamped between 0 and 1.
    """
    return Vec4(v1[0]*(1-t)+v2[0]*t,
                v1[1]*(1-t)+v2[1]*t,
                v1[2]*(1-t)+v2[2]*t,
                v1[3]*(1-t)+v2[3]*t)


# GUI Layout
MENU_FRAME_SIZE = (-1, 1, -0.15, 0)
MENU_FRAME_POS = (0, 0, -0.85)
BUTTON_Y = -0.075

# Layer controls frame
LAYER_CONTROLS_FRAME_SIZE = (-0.3, 0.3, -0.2, 0.2)
LAYER_CONTROLS_POS = (-0.85, 0, 0)
LAYER_BUTTON_SPACING = 0.04
LAYER_BUTTON_SIZE = (-0.25, 0.25, -0.03, 0.03)

# Layer range controls
RANGE_ENTRY_SIZE = (-0.8, 0.8, -0.8, 0.8)
RANGE_LABEL_SCALE = 0.04
RANGE_ENTRY_SCALE = 0.04
RANGE_TOP_POS = (0, 0, 0.1)
RANGE_BOTTOM_POS = (0, 0, 0)
RANGE_APPLY_POS = (0, 0, -0.1)

# Button settings
BUTTON_SCALE = 0.035
BUTTON_TEXT_SCALE = 0.8
NAV_BUTTON_SIZE = (-1, 1, -0.8, 0.8)
WIDE_BUTTON_SIZE = (-4, 4, -0.8, 0.8)
LAYER_TOGGLE_SCALE = 0.04
LAYER_TOGGLE_TEXT_SCALE = 0.8

# Button positions
PREV_BUTTON_POS = (0.4, 0, BUTTON_Y)
NEXT_BUTTON_POS = (0.5, 0, BUTTON_Y)
TOGGLE_BUTTON_POS = (0.7, 0, BUTTON_Y)
OPEN_BUTTON_POS = (0.9, 0, BUTTON_Y)

# Text settings
STATUS_TEXT_POS = (-0.95, 0.9)
STATUS_TEXT_SCALE = 0.04
LAYER_INFO_TEXT_POS = (-0.95, 0.85)
LAYER_INFO_TEXT_SCALE = 0.035
HELP_TEXT_POS = (-0.95, -0.92)
HELP_TEXT_SCALE = 0.035
LAYER_CONTROLS_TITLE_SCALE = 0.05
LAYER_CONTROLS_TITLE_POS = (0, 0.15)

# Button text
PREV_BUTTON_TEXT = "<"
NEXT_BUTTON_TEXT = ">"
TOGGLE_POSITIVE_TEXT = "Show Positive"
TOGGLE_VOID_TEXT = "Show Void"
OPEN_BUTTON_TEXT = "Open Print Directory"
RANGE_APPLY_TEXT = "Apply Range"

# Help text
HELP_TEXT = ("Controls: Left Mouse = Rotate, Middle Mouse = Pan, Right Mouse = Zoom\n"
             "Up/Down = Change Layer, W = Toggle Pixels, Esc = Quit\n"
             "Use layer range controls to show/hide layers")

# Layer visualization settings
REAL_PROPORTION = 10.0 / 7.6  # Layer thickness divided by pixel size
IMAGE_SCALE_FACTOR = 0.00075  # Percentage of image width for spacing
EXPOSURE_SPACING_FACTOR = 0.1  # Relative spacing between exposures

def get_button_style(wide=False):
    """Get common button style settings."""
    return {
        'text_scale': BUTTON_TEXT_SCALE,
        'scale': BUTTON_SCALE,
        'frameColor': BUTTON_COLOR,
        'text_fg': TEXT_COLOR,
        'relief': DGG.RAISED,
        'frameSize': WIDE_BUTTON_SIZE if wide else NAV_BUTTON_SIZE
    }

def get_text_style(color=None, align=TextNode.ALeft):
    """Get common text style settings."""
    if color is None:
        color = TEXT_COLOR
    return {
        'fg': color,
        'align': align,
        'mayChange': True
    }

def get_window_properties():
    """Get the window properties for Panda3D."""
    props = WindowProperties()
    props.setTitle(WINDOW_TITLE)
    props.setSize(*WINDOW_SIZE)
    return props
