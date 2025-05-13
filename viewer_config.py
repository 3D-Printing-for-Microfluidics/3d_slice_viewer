from panda3d.core import Point3, Vec4, WindowProperties, TextNode
from direct.gui import DirectGuiGlobals as DGG

THEME = "dark"  # Options: "dark", "light", "midnight", "forest", "softBlue", "softPink", "softGreen"

# Window settings
WINDOW_TITLE = "3D Slice Viewer"
WINDOW_SIZE = (1400, 800)
WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_SIZE
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
    "#59cd90",  # Emerald
    "#3fa7d6",  # Picton Blue
    "#fac05e",  # Xanthous Yellow
    "#f79d84",  # Atomic Tangerine
    "#a3c4f3",  # Periwinkle
    "#b39ddb",  # Lavender
    "#6a0136",  # Tyrian Purple
    "#ee6352",  # Bittersweet Red
]

if THEME == "dark":
    # charcoal UI with a punchy orange accent and calm blue “file” buttons
    BUTTON_INACTIVE_COLOR       = "#ff7b00"   # vivid orange  (idle)
    BUTTON_ACTIVE_COLOR         = "#ffa337"   # softer orange (hover / press)
    FILE_BUTTON_INACTIVE_COLOR  = "#1e88e5"   # calm blue     (idle)
    FILE_BUTTON_ACTIVE_COLOR    = "#42a5f5"   # lighter blue  (hover / press)

    BG_COLOR      = "#2b2b2b"   # dark grey window background
    FG_COLOR      = "#ffffff"
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#3a3a3a"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#555555"   # lightGray
    SLIDER_BG      = "#d3d3d3"   # darkGray
    SLIDER_OUTLINE = FG_COLOR

    PANDA_BG_COLOR = "#424242"


elif THEME == "light":
    # clean “inverted” scheme — bright background, same orange accents / blue file btns
    BUTTON_INACTIVE_COLOR       = "#1e88e5"
    BUTTON_ACTIVE_COLOR         = "#42a5f5"
    FILE_BUTTON_INACTIVE_COLOR  = "#ff7b00"
    FILE_BUTTON_ACTIVE_COLOR    = "#ffa337"

    BG_COLOR      = "#dddddd"    # light grey
    FG_COLOR      = "#212121"    # near-black text
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#f5f5f5"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#d9d9d9"   # lightGray
    SLIDER_BG      = "#666666"   # darkGray
    SLIDER_OUTLINE = "#666666"   # darkGray

    PANDA_BG_COLOR = "#f0f0f0"


elif THEME == "midnight":
    # extra-dark UI, teal-purple highlights, buttons lean slate-grey
    BUTTON_INACTIVE_COLOR       = "#6b7280"   # slate-grey (idle)
    BUTTON_ACTIVE_COLOR         = "#8f949e"   # lighter slate (hover / press)
    FILE_BUTTON_INACTIVE_COLOR  = "#5c6bc0"   # softer indigo (hover / press)
    FILE_BUTTON_ACTIVE_COLOR    = "#3949ab"   # indigo (idle)

    BG_COLOR      = "#0d1117"    # near-black with a hint of blue
    FG_COLOR      = "#eceff4"
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#1b2130"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = "#5d6dff"   # electric blue-violet track / handles
    SLIDER_FG      = "#b0b0b0"
    SLIDER_BG      = "#404a5a"
    SLIDER_OUTLINE = FG_COLOR

    PANDA_BG_COLOR = "#1b2130"   # dark slate-grey


elif THEME == "forest":
    # deep green UI with a soft yellow-green accent, buttons are a bit darker
    BUTTON_INACTIVE_COLOR       = "#388e3c"   # deeper green
    BUTTON_ACTIVE_COLOR         = "#4caf50"   # primary green
    FILE_BUTTON_INACTIVE_COLOR  = "#e3bf20"   # goldenrod
    FILE_BUTTON_ACTIVE_COLOR    = "#dbc253"   # darker golderod

    BG_COLOR      = "#163b16"   # deep green
    FG_COLOR      = "#ffffff"
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#ffffff"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#dcdcdc"
    SLIDER_BG      = "#646464"
    SLIDER_OUTLINE = "#646464"

    PANDA_BG_COLOR = "#c8e6c9"   # light green-grey


elif THEME == "softBlue":
    # airy cream canvas, baby-blue accents, deeper aqua file buttons
    BUTTON_INACTIVE_COLOR       = "#4fc3f7"   # brighter baby-blue
    BUTTON_ACTIVE_COLOR         = "#a6d4fa"   # very light sky-blue
    FILE_BUTTON_INACTIVE_COLOR  = "#007acc"   # azure
    FILE_BUTTON_ACTIVE_COLOR    = "#2196f3"   # primary blue

    BG_COLOR      = "#b8cce0"   # light blue-grey
    FG_COLOR      = "#1a1a1a"
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#ffffff"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#dcdcdc"
    SLIDER_BG      = "#646464"
    SLIDER_OUTLINE = "#646464"

    PANDA_BG_COLOR = "#e6dec5"    # warm off-white


elif THEME == "softPink":
    # gentle cream canvas with blush-pink buttons, lavender file buttons
    BUTTON_INACTIVE_COLOR       = "#f48fb1"   # stronger blush
    BUTTON_ACTIVE_COLOR         = "#f8bbd0"   # pale blush
    FILE_BUTTON_INACTIVE_COLOR  = "#ba68c8"   # soft lavender
    FILE_BUTTON_ACTIVE_COLOR    = "#ab47bc"   # richer lavender

    BG_COLOR      = "#fae6f8"   # light pink-grey
    FG_COLOR      = "#1a1a1a"
    BUTTON_BG     = FG_COLOR
    BUTTON_FG     = "#262222"
    ENTRY_BG      = "#ffffff"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = FILE_BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#e3e3e3"
    SLIDER_BG      = "#646464"
    SLIDER_OUTLINE = "#646464"

    PANDA_BG_COLOR = "#d4cddb"   # light lavender-grey

elif THEME == "softGreen":
    # soft green canvas with minty buttons, deeper green file buttons
    BUTTON_INACTIVE_COLOR       = "#81c784"   # minty green
    BUTTON_ACTIVE_COLOR         = "#a5d6a7"   # lighter mint
    FILE_BUTTON_INACTIVE_COLOR  = "#388e3c"   # deeper green
    FILE_BUTTON_ACTIVE_COLOR    = "#4caf50"   # primary green

    BG_COLOR      = "#e8f5e9"    # soft green
    FG_COLOR      = "#1a1a1a"
    BUTTON_BG     = BG_COLOR
    BUTTON_FG     = FG_COLOR
    ENTRY_BG      = "#ffffff"
    ENTRY_FG      = FG_COLOR

    SLIDER_ACCENT  = BUTTON_INACTIVE_COLOR
    SLIDER_FG      = "#e3e3e3"
    SLIDER_BG      = "#646464"
    SLIDER_OUTLINE = "#646464"

    PANDA_BG_COLOR = "#c8e6c9"   # light green-grey


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


def get_window_properties():
    """Get the window properties for Panda3D."""
    props = WindowProperties()
    props.setTitle(WINDOW_TITLE)
    props.setSize(*WINDOW_SIZE)
    return props
