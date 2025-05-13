import tkinter as tk
from tkinter import Tk
from tkinter import ttk, filedialog
import ttkbootstrap as ttkb
from direct.showbase.ShowBase import ShowBase
import time
import sys
from panda3d.core import WindowProperties

import viewer_config  # Import configuration settings

class VerticalRangeSlider(tk.Canvas):
    def __init__(self, parent, min_val, max_val, initial_bottom, initial_top,
                 width=50, height=300, callback=None, bg=viewer_config.BG_COLOR, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.bottom_val = initial_bottom
        self.top_val    = initial_top
        self.callback   = callback 

        # background rectangle
        self.create_rectangle(0, 0, width, height, fill=bg, width=4, outline=viewer_config.SLIDER_OUTLINE)

        # coords for the slider line
        self.line_x = width // 2
        self.line_y0 = 10
        self.line_y1 = height - 10
        self.create_line(self.line_x, self.line_y0, self.line_x, self.line_y1,
                         fill=viewer_config.SLIDER_FG, width=4)

        # draw a “range” rectangle *behind* the handles:
        # note: width=0 for no border
        self.range_rect = self.create_rectangle(
            self.line_x-4, self.line_y0, self.line_x+4, self.line_y1,
            fill=viewer_config.SLIDER_BG, width=0
        )

        # handle circles
        self.scale   = float(self.tk.call('tk', 'scaling'))
        self.handle_radius  = int(8 * self.scale)
        self.bottom_handle = self.create_oval(0,0,0,0, fill=viewer_config.SLIDER_ACCENT, outline=viewer_config.BG_COLOR)
        self.top_handle    = self.create_oval(0,0,0,0, fill=viewer_config.SLIDER_ACCENT, outline=viewer_config.BG_COLOR)

        self.update_handle_positions()

        # bind events…
        self.tag_bind(self.bottom_handle, "<Button-1>", self.click_bottom)
        self.tag_bind(self.bottom_handle, "<B1-Motion>", self.drag_bottom)
        self.tag_bind(self.top_handle,    "<Button-1>", self.click_top)
        self.tag_bind(self.top_handle,    "<B1-Motion>", self.drag_top)
        self.bind("<ButtonRelease-1>", self.release)

        self.dragging = None

    def update_handle_positions(self):
        line_length = self.line_y1 - self.line_y0

        # compute y for each handle
        bottom_y = self.line_y0 + ((self.max_val - self.bottom_val)
                     / (self.max_val - self.min_val)) * line_length
        top_y    = self.line_y0 + ((self.max_val - self.top_val)
                     / (self.max_val - self.min_val)) * line_length
        x, r = self.line_x, self.handle_radius

        # move the handles
        self.coords(self.bottom_handle, x-r, bottom_y-r, x+r, bottom_y+r)
        self.coords(self.top_handle,    x-r,    top_y-r, x+r, top_y+r)

        # and update the “range” rectangle to sit *between* them
        self.coords(self.range_rect,
                    x-4,  top_y,   # left‐upper
                    x+4, bottom_y  # right‐lower
        )

    def click_bottom(self, event):
        self.dragging = "bottom"

    def drag_bottom(self, event):
        self.move_handle("bottom", event.y)

    def click_top(self, event):
        self.dragging = "top"

    def drag_top(self, event):
        self.move_handle("top", event.y)

    def move_handle(self, handle, y):
        # Confine the y coordinate between the top and bottom of the slider.
        y = min(max(y, self.line_y0), self.line_y1)
        line_length = self.line_y1 - self.line_y0
        # Convert y into a value
        value = self.max_val - ((y - self.line_y0) / line_length) * (self.max_val - self.min_val)
        value = round(value)
        if handle == "bottom":
            # Ensure the bottom handle cannot go above the top handle.
            if value >= self.top_val:
                value = self.top_val - 1
            self.bottom_val = max(self.min_val, value)
        else:
            if value <= self.bottom_val:
                value = self.bottom_val + 1
            self.top_val = min(self.max_val, value)
        self.update_handle_positions()
        if self.callback:
            self.callback(self.bottom_val, self.top_val)

    def release(self, event):
        self.dragging = None

if sys.platform.startswith("win"):
    import ctypes
    try:
        # Win 8.1+  — use the modern per-monitor-v2 setting
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        # Fallback for Win 7/early 8
        ctypes.windll.user32.SetProcessDPIAware()

class ViewerApp:
    def __init__(self):
        self.root = tk.Tk()

        # Force one geometry pass so fpixels is correct
        self.root.update_idletasks()

        # Calculate logical-to-physical scale
        pixels_per_inch = self.root.winfo_fpixels('1i')   # e.g. 144 on a 150 % laptop
        scale = pixels_per_inch / 72                      # points → px

        # Tell Tk (and optionally ttk-bootstrap) to use it
        self.root.tk.call('tk', 'scaling', scale)
        try:
            if isinstance(self.root, ttkb.Window):
                self.root.set_scaling(scale)
        except ModuleNotFoundError:
            pass

        self.layer_opacity = 0.01
        self.setup_window()
        self.create_widgets()
        self.setup_panda3d()
        self.update_slider_range(100)  # defaults to 100 layers

        self.progress_bar = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, mode='determinate', maximum=100)
        self.status_label = ttk.Label(self.root, text="Ready")
        
    def setup_window(self):
        """Configure the main window."""
        # Initialize ttkbootstrap style system
        style = ttkb.Style()

        self.root.title("3D Slice Viewer")
        # self.root.geometry(f"{viewer_config.WINDOW_WIDTH}x{viewer_config.WINDOW_HEIGHT}")
        self.root.configure(bg=viewer_config.BG_COLOR)  # Ensure consistent background

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.start_w = int(screen_w * 0.85)          # or tweak 0.85 → 0.90 if you prefer
        self.start_h = int(screen_h * 0.85)
        self.root.geometry(f"{self.start_w}x{self.start_h}")

        # Minimum window so the side bars never crunch together
        self.root.minsize(800, 600)

        # Apply custom theme from viewer_config.py
        style.configure('Viewer.TFrame', background=viewer_config.BG_COLOR)
        style.configure('Viewer.TLabel',
                        background=viewer_config.BG_COLOR,
                        foreground=viewer_config.FG_COLOR,
                        font=(viewer_config.FONT_FAMILY, viewer_config.FONT_SIZE))
        style.configure('Viewer.TButton',
                        background=viewer_config.BUTTON_BG,
                        foreground=viewer_config.BUTTON_FG,
                        padding=viewer_config.PADDING,
                        relief="flat")
        style.configure('ViewerFile.TButton',
                        background=viewer_config.BUTTON_BG,
                        foreground=viewer_config.BUTTON_FG,
                        padding=viewer_config.PADDING,
                        relief="flat")
        style.configure('Viewer.TCheckbutton',
                        background=viewer_config.BG_COLOR,
                        foreground=viewer_config.FG_COLOR,
                        font=(viewer_config.FONT_FAMILY, viewer_config.FONT_SIZE))

        # LabelFrames for headings with dark style
        style.configure('Viewer.TLabelframe', background=viewer_config.BG_COLOR)
        style.configure('Viewer.TLabelframe.Label',
                        background=viewer_config.BG_COLOR,
                        foreground=viewer_config.FG_COLOR,
                        font=(viewer_config.FONT_FAMILY, viewer_config.HEADER_FONT_SIZE, 'bold'))

        # Set the background color of the slider and its trough to match the dark theme
        style.configure("TScale",
                        background=viewer_config.BG_COLOR,  # Match background with dark theme
                        troughcolor=viewer_config.BUTTON_BG,  # Set the trough (slider track) color to dark
                        sliderlength=20,  # Size of the slider thumb
                        )

        # Buttons hover effect
        style.map("Viewer.TButton",
                background=[('active', viewer_config.BUTTON_ACTIVE_COLOR),
                            ('!active', viewer_config.BUTTON_INACTIVE_COLOR)],)
        style.map("Viewer.TButton",
                foreground=[('active', viewer_config.BG_COLOR),
                            ('!active', viewer_config.BG_COLOR)])
        style.map("ViewerFile.TButton",
                background=[('active', viewer_config.FILE_BUTTON_ACTIVE_COLOR),
                            ('!active', viewer_config.FILE_BUTTON_INACTIVE_COLOR)],)
        style.map("ViewerFile.TButton",
                foreground=[('active', viewer_config.BG_COLOR),
                            ('!active', viewer_config.BG_COLOR)])


        # Apply color changes to checkboxes when checked (orange checkmark)
        style.configure("Viewer.TCheckbutton",
                        focuscolor="transparent",
                        highlightthickness=0)
        style.map("Viewer.TCheckbutton",
                background=[('active', viewer_config.BG_COLOR)],
                highlightcolor=[('selected', viewer_config.BUTTON_ACTIVE_COLOR),
                                ('!selected', viewer_config.BG_COLOR)])
        style.map("Viewer.TCheckbutton",
                foreground=[('active', viewer_config.FG_COLOR),
                            ('!active', viewer_config.FG_COLOR)])


    def create_widgets(self):
        """Create and arrange all widgets."""
        # Main container
        self.main_container = ttk.Frame(self.root, style='Viewer.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Left control panel (sidebar on the left)
        # panel_width = viewer_config.CONTROL_PANEL_WIDTH
        panel_width = max(180, int(self.start_w * 0.14))   # ~14 % of the window
        self.control_panel = ttk.Frame(self.main_container, style='Viewer.TFrame', width=panel_width)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=viewer_config.PADDING, pady=viewer_config.PADDING)
        self.control_panel.pack_propagate(False)  # Prevent resizing to fit content

        # Create control sections on the left panel
        self.create_file_controls()
        self.create_layer_controls()
        self.create_quality_controls()

        # Section for image type toggles
        self.type_frame = ttk.LabelFrame(self.control_panel, text="Image Types", style='Viewer.TFrame')
        self.type_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Right panel for legend
        self.right_panel = ttk.Frame(self.main_container, style='Viewer.TFrame', width=panel_width)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=viewer_config.PADDING, pady=viewer_config.PADDING)
        self.right_panel.pack_propagate(False)  # Prevent resizing to fit content

        # Center viewer frame
        self.viewer_frame = ttk.Frame(self.main_container, style='Viewer.TFrame')
        self.viewer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Status bar (bottom)
        self.status_bar = ttk.Frame(self.root, style='Viewer.TFrame')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(self.status_bar, text="Ready", style='Viewer.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=viewer_config.PADDING)

        # Progress bar for file loading
        self.progress_bar = ttk.Progressbar(self.status_bar, orient=tk.HORIZONTAL,
                                            mode='determinate', maximum=100)
        # (Progress bar created but not packed here; it will be shown only during file loading)


    def create_legend_section(self):
        """Create and display a legend for exposure times and their assigned colors."""
        # Clear any existing legend content in the right panel
        for child in self.right_panel.winfo_children():
            child.destroy()
        
        legend_frame = ttk.LabelFrame(self.right_panel, text="Exposure Time Legend",
                                    style='Viewer.TLabelframe')
        legend_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)
        
        # Collect and sort unique exposure times
        exposure_times = sorted({
            td.get('exposure_time') 
            for layer in self.viewer.slice_data 
            for td in layer.get('texture_data', [])
            if td.get('exposure_time') is not None
        })

        # Group exposure times within ±50 ms (max 3 per group)
        groups = []
        current_group = []
        for exp in exposure_times:
            if not current_group:
                current_group = [exp]
            elif exp - current_group[0] <= 50 and len(current_group) < 3:
                current_group.append(exp)
            else:
                groups.append(current_group)
                current_group = [exp]
        if current_group:
            groups.append(current_group)
        
        # Determine color for each exposure time (light/base/dark per group)
        exposure_color_map = {}
        colors = viewer_config.EXPOSURE_COLORS
        for idx, group in enumerate(groups):
            base_hex = colors[idx % len(colors)]
            r = int(base_hex[1:3], 16); g = int(base_hex[3:5], 16); b = int(base_hex[5:7], 16)
            if len(group) == 1:
                exposure_color_map[group[0]] = base_hex
            elif len(group) == 2:
                # Two exposures: compute lighter and darker shades of the base color
                light_r = round(r + (255 - r) * 0.5); light_g = round(g + (255 - g) * 0.5); light_b = round(b + (255 - b) * 0.5)
                dark_r = round(r * 0.5); dark_g = round(g * 0.5); dark_b = round(b * 0.5)
                exposure_color_map[group[0]] = f"#{light_r:02x}{light_g:02x}{light_b:02x}"
                exposure_color_map[group[1]] = f"#{dark_r:02x}{dark_g:02x}{dark_b:02x}"
            elif len(group) == 3:
                # Three exposures: low→light, mid→base, high→dark
                light_r = round(r + (255 - r) * 0.5); light_g = round(g + (255 - g) * 0.5); light_b = round(b + (255 - b) * 0.5)
                dark_r = round(r * 0.5); dark_g = round(g * 0.5); dark_b = round(b * 0.5)
                exposure_color_map[group[0]] = f"#{light_r:02x}{light_g:02x}{light_b:02x}"
                exposure_color_map[group[1]] = base_hex
                exposure_color_map[group[2]] = f"#{dark_r:02x}{dark_g:02x}{dark_b:02x}"
        
        # Create legend entries for each exposure time with its color
        for exp_time in exposure_times:
            color_hex = exposure_color_map.get(exp_time, "#ffffff")
            entry_label = ttk.Label(legend_frame, text=f"{exp_time} ms",
                                    style='Viewer.TLabel', background=color_hex)
            entry_label.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

    def create_file_controls(self):
        """Create file operation controls."""
        file_frame = ttk.LabelFrame(self.control_panel, text="File Controls",
                                    style='Viewer.TLabelframe')
        file_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)
        open_button = ttk.Button(file_frame, text="Open Directory", style='ViewerFile.TButton', command=self.open_directory)
        open_button.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

    def create_layer_controls(self):
        """Create layer control section."""
        # Create the LabelFrame for "Layer Controls" with proper title and dark background
        layer_controls_frame = ttk.LabelFrame(self.control_panel, text="Layer Controls", style='Viewer.TLabelframe')
        layer_controls_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Layer range slider (vertical)
        scale = float(self.root.tk.call('tk', 'scaling'))   # 1.0 on 96 dpi; 1.5 on 144 dpi …

        # Create the slider with DPI-aware geometry
        self.range_slider = VerticalRangeSlider(
                layer_controls_frame,
                min_val    = 1,
                max_val    = 200,
                initial_bottom = 1,
                initial_top    = 200,
                width  = int(60  * scale),
                height = int(200 * scale),
                callback = self.update_layer_range,
        )
        self.range_slider.pack(padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Precise range controls frame
        precise_frame = ttk.Frame(layer_controls_frame, style='Viewer.TFrame')
        precise_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Top layer controls (Wrap label and button in frame to align right)
        top_frame = ttk.Frame(precise_frame, style='Viewer.TFrame')
        top_frame.pack(fill=tk.X, pady=2)

        # Label and button for top layer
        ttk.Label(top_frame, text="Top layer:", style='Viewer.TLabel').pack(side=tk.LEFT)
        self.top_layer_label = ttk.Label(top_frame, text=str(self.range_slider.top_val), style='Viewer.TLabel')
        self.top_layer_label.pack(side=tk.LEFT, padx=5)

        # Right-aligned buttons (modern flat buttons with outline)
        button_frame = ttk.Frame(top_frame, style='Viewer.TFrame')
        button_frame.pack(side=tk.RIGHT)

        # Arrow buttons with modern flat style
        top_up_button = ttk.Button(button_frame, text="▲", style="Viewer.TButton", width=2, command=self.increase_top_layer)
        top_up_button.pack(side=tk.LEFT)
        top_down_button = ttk.Button(button_frame, text="▼", style="Viewer.TButton", width=2, command=self.decrease_top_layer)
        top_down_button.pack(side=tk.LEFT)

        # Bottom layer controls (Wrap label and button in frame to align right)
        bottom_frame = ttk.Frame(precise_frame, style='Viewer.TFrame')
        bottom_frame.pack(fill=tk.X, pady=2)

        # Label and button for bottom layer
        ttk.Label(bottom_frame, text="Bottom layer:", style='Viewer.TLabel').pack(side=tk.LEFT)
        self.bottom_layer_label = ttk.Label(bottom_frame, text=str(self.range_slider.bottom_val), style='Viewer.TLabel')
        self.bottom_layer_label.pack(side=tk.LEFT, padx=5)

        # Right-aligned buttons for bottom layer
        button_frame_bottom = ttk.Frame(bottom_frame, style='Viewer.TFrame')
        button_frame_bottom.pack(side=tk.RIGHT)

        # Arrow buttons for bottom layer
        bottom_up_button = ttk.Button(button_frame_bottom, text="▲", style="Viewer.TButton", width=2, command=self.increase_bottom_layer)
        bottom_up_button.pack(side=tk.LEFT)
        bottom_down_button = ttk.Button(button_frame_bottom, text="▼", style="Viewer.TButton", width=2, command=self.decrease_bottom_layer)
        bottom_down_button.pack(side=tk.LEFT)

    def create_quality_controls(self):
        """Create quality control section along with opacity adjustments."""
        # Create the LabelFrame for "Quality Controls" with proper title and dark background
        quality_controls_frame = ttk.LabelFrame(self.control_panel, text="Quality Controls", style='Viewer.TLabelframe')
        quality_controls_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Quality toggle button (modern flat button with outline style)
        self.quality_button = ttk.Button(quality_controls_frame, text="Fast Render", style="Viewer.TButton", command=self.toggle_quality)
        self.quality_button.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Opacity controls (Wrap label and button in frame to align right)
        opacity_control_frame = ttk.Frame(quality_controls_frame, style='Viewer.TFrame')
        opacity_control_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=(viewer_config.PADDING, 10))  # Added bottom padding

        # Label and buttons for opacity control
        ttk.Label(opacity_control_frame, text="Layer Opacity:", style='Viewer.TLabel').pack(side=tk.LEFT)
        self.opacity_label = ttk.Label(opacity_control_frame, text="100%", style='Viewer.TLabel')
        self.opacity_label.pack(side=tk.LEFT, padx=5)

        # Button frame for opacity up/down arrows with modern flat style
        button_frame_opacity = ttk.Frame(opacity_control_frame, style='Viewer.TFrame')
        button_frame_opacity.pack(side=tk.RIGHT)

        # Arrow buttons with modern flat style
        opacity_up = ttk.Button(button_frame_opacity, text="▲", style="Viewer.TButton", width=2, command=self.increase_opacity)
        opacity_up.pack(side=tk.LEFT)
        opacity_down = ttk.Button(button_frame_opacity, text="▼", style="Viewer.TButton", width=2, command=self.decrease_opacity)
        opacity_down.pack(side=tk.LEFT)

        # Add the "Apply Opacity" button here
        apply_opacity_button = ttk.Button(quality_controls_frame, text="Apply Opacity", style="Viewer.TButton", command=self.apply_opacity)
        apply_opacity_button.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)


    def increase_top_layer(self):
        """Increase the top layer by 1 (if within range)."""
        new_val = self.range_slider.top_val + 1
        if new_val <= self.range_slider.max_val and new_val > self.range_slider.bottom_val:
            self.range_slider.top_val = new_val
            self.range_slider.update_handle_positions()
            self.top_layer_label.config(text=str(self.range_slider.top_val))
            self.update_layer_range(self.range_slider.bottom_val, self.range_slider.top_val)

    def decrease_top_layer(self):
        """Decrease the top layer by 1 (if above bottom layer)."""
        new_val = self.range_slider.top_val - 1
        if new_val > self.range_slider.bottom_val:
            self.range_slider.top_val = new_val
            self.range_slider.update_handle_positions()
            self.top_layer_label.config(text=str(self.range_slider.top_val))
            self.update_layer_range(self.range_slider.bottom_val, self.range_slider.top_val)

    def increase_bottom_layer(self):
        """Increase the bottom layer by 1 (if less than top layer)."""
        new_val = self.range_slider.bottom_val + 1
        if new_val < self.range_slider.top_val:
            self.range_slider.bottom_val = new_val
            self.range_slider.update_handle_positions()
            self.bottom_layer_label.config(text=str(self.range_slider.bottom_val))
            self.update_layer_range(self.range_slider.bottom_val, self.range_slider.top_val)

    def decrease_bottom_layer(self):
        """Decrease the bottom layer by 1 (if above the minimum)."""
        new_val = self.range_slider.bottom_val - 1
        if new_val >= self.range_slider.min_val:
            self.range_slider.bottom_val = new_val
            self.range_slider.update_handle_positions()
            self.bottom_layer_label.config(text=str(self.range_slider.bottom_val))
            self.update_layer_range(self.range_slider.bottom_val, self.range_slider.top_val)

    def update_layer_range(self, bottom, top):
        """Update the viewer's visible layer range based on the slider values 
        and update the precise control labels."""
        if hasattr(self, 'viewer'):
            self.viewer.set_layer_range(top=top, bottom=bottom)
        if hasattr(self, 'top_layer_label'):
            self.top_layer_label.config(text=str(top))
        if hasattr(self, 'bottom_layer_label'):
            self.bottom_layer_label.config(text=str(bottom))

    def manual_apply_range(self):
        """Apply the current layer range manually (if needed)."""
        bottom = self.range_slider.bottom_val
        top = self.range_slider.top_val
        self.update_layer_range(bottom, top)

    def increase_opacity(self):
        """Increase layer opacity by 0.1% up to a maximum of 100%."""
        new_opacity = min(self.layer_opacity + 0.01, 1.0)
        self.layer_opacity = new_opacity
        self.opacity_label.config(text=f"{self.layer_opacity*100:.1f}%")

    def decrease_opacity(self):
        """Decrease layer opacity by 0.1% down to a minimum of 0%."""
        new_opacity = max(self.layer_opacity - 0.01, 0.0)
        self.layer_opacity = new_opacity
        self.opacity_label.config(text=f"{self.layer_opacity*100:.1f}%")

    def apply_opacity(self):
        """Apply the current opacity setting to update the scene."""
        if hasattr(self, 'viewer'):
            # Update the viewer's layer opacity with the current UI value.
            self.viewer.layer_opacity = self.layer_opacity
            # Clear the texture cache to force re-generation with new opacity.
            self.viewer.texture_cache.clear()
            # Trigger the quality update so that _update_node_quality_async refreshes all nodes.
            self.viewer.set_quality_mode(self.viewer.high_quality)
            self.status_label.config(text=f"Opacity updated to {self.layer_opacity * 100:.1f}%")

    def update_slider_range(self, total_layers):
        """Update the slider widget to have a range from 1 to total_layers."""
        if not hasattr(self, 'range_slider') or self.range_slider is None:
            print("Range slider not initialized yet.")
            return
        self.range_slider.min_val = 1
        self.range_slider.max_val = total_layers
        self.range_slider.bottom_val = 1
        self.range_slider.top_val = total_layers
        self.range_slider.update_handle_positions()
        
    def setup_panda3d(self):
        """Initialize and embed the Panda3D viewer."""
        # Create a frame for Panda3D
        self.panda_frame = ttk.Frame(self.viewer_frame, style='Viewer.TFrame')
        self.panda_frame.pack(fill=tk.BOTH, expand=True)
        
        # Wait for the frame to be fully ready
        self.root.update()
        
        # Get the frame's window ID
        frame_window = self.panda_frame.winfo_id()
        
        # Initialize Panda3D with a windowless base.
        from panda3d.core import load_prc_file_data
        load_prc_file_data("", "want-tk true\ndisable-message-loop true")
        self.panda3d = ShowBase(windowType='none')
        
        # Create window properties for embedding.
        props = viewer_config.get_window_properties()
        props.setParentWindow(frame_window)
        props.setOrigin(0, 0)
        props.setSize(self.panda_frame.winfo_width(), self.panda_frame.winfo_height())
        
        # Create the Panda3D window using openWindow.
        self.panda3d.openWindow(props=props)

        self.panda_frame.bind(
            "<Configure>",
            lambda e: self._resize_panda3d(e.width, e.height)
        )

        self.panda_frame.bind("<Configure>", self._sync_panda_to_frame)
        
        # Local import to avoid circular dependency.
        from viewer_3d_panda import Viewer3D
        self.viewer = Viewer3D(self.panda3d)
        
        # Set up periodic task to update Panda3D (approx 30 FPS).
        self.root.after(33, self.update_panda3d)

        def _on_close(self):
            self.panda3d.taskMgr.stop()   # stop any running tasks
            self.root.destroy()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)


    def _resize_panda3d(self, width: int, height: int):
        """Resize Panda3D’s buffer whenever the Tk frame changes size."""
        if not getattr(self, "panda3d", None):          # not yet initialised
            return
        props = WindowProperties()
        props.setSize(width, height)
        self.panda3d.win.requestProperties(props)

    def _sync_panda_to_frame(self, event):
        """Resize *and* correctly reposition Panda3D inside `panda_frame`."""
        from panda3d.core import WindowProperties
        props = WindowProperties()

        # 1.  Width / height straight from the <Configure> event
        props.setSize(event.width, event.height)

        # 2.  Offset relative to the Tk root’s drawable area
        props.setOrigin(
            self.panda_frame.winfo_x(),   # ← already root-relative
            self.panda_frame.winfo_y()
        )
        self.panda3d.win.requestProperties(props)
        
    def update_panda3d(self):
        """Update Panda3D's task manager."""
        self.panda3d.taskMgr.step()
        self.root.after(33, self.update_panda3d)

    def _on_close(self) -> None:
        """Graceful shutdown when the user exits"""
        try:
            # Stop Panda’s task manager if it exists (may not if init failed)
            if hasattr(self, "panda3d") and self.panda3d.taskMgr.running:
                self.panda3d.taskMgr.stop()
        except Exception:
            pass      # don’t let shutdown errors hang the GUI

        # Destroy the Tk window and exit the app
        self.root.quit()
        self.root.destroy()
            
    def build_type_toggles(self, available_types):
        """Build the type toggles for image types in the control panel."""
        # Create the frame for the toggles with dark background and proper styling
        type_frame = ttk.LabelFrame(self.control_panel, text="Image Types", style='Viewer.TLabelframe')
        type_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Loop through available image types and create a checkbox for each one
        for image_type in available_types:
            # Create a checkbox for each image type with custom styling
            var = tk.BooleanVar(value=True)  # Default to True (checked)
            
            # Create the checkbox with custom styling
            chk = ttk.Checkbutton(
                type_frame,
                text=image_type,
                variable=var,
                style='Viewer.TCheckbutton',
                command=lambda t=image_type, v=var: self.viewer.toggle_image_type(t, v.get())
            )
            chk.pack(anchor=tk.W, padx=viewer_config.PADDING, pady=5)

    def build_exposure_toggles(self, available_exposures):
        """Build checkboxes to toggle visibility of images by exposure time."""
        # Create the frame for the exposure toggles with dark background and styling
        exp_frame = ttk.LabelFrame(self.right_panel, text="Show/Hide Exposures",
                                   style='Viewer.TLabelframe')
        exp_frame.pack(fill=tk.X, padx=viewer_config.PADDING, pady=viewer_config.PADDING)

        # Loop through available exposures and create a checkbox for each one
        for exp_time in available_exposures:
            var = tk.BooleanVar(value=True)  # Default to True (checked)
            chk = ttk.Checkbutton(
                exp_frame,
                text=f"{exp_time} ms",
                variable=var,
                style='Viewer.TCheckbutton',
                command=lambda e=exp_time, v=var: self.viewer.toggle_exposure(e, v.get())
            )
            chk.pack(anchor=tk.W, padx=viewer_config.PADDING, pady=5)

    def open_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            # Show and reset progress bar
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=viewer_config.PADDING)
            self.progress_bar['value'] = 0
            
            # Phase 1: Parsing JSON (UI will update via callback)
            self.handle_progress("Parsing JSON", immediate=True)
            
            # Load directory data (Parse JSON, initialize layers)
            if self.viewer.load_print_directory(directory,
                                            on_status_update=self.on_status_update,
                                            on_progress_update=self.on_progress_update):
                # Phase 2: Finding images
                self.handle_progress("Finding images")
                
                # Phase 3: Loading layers (once images are found, start loading layers)
                self.handle_progress("Loading layers", wait_for_layers=True)
                
                # Hide progress bar after loading
                self.progress_bar.pack_forget()
                
                # Clear existing toggles
                for widget in self.type_frame.winfo_children():
                    widget.destroy()
                
                # Rebuild the UI toggles...
                self.update_slider_range(self.viewer.total_layers)
                self.build_type_toggles(self.viewer.available_types)
                self.create_legend_section()
                self.build_exposure_toggles(self.viewer.available_exposures)
                
                # Final status
                self.status_label.config(
                    text=f"Loaded {self.viewer.total_layers} layers ({self.viewer.unique_layers} unique)"
                )
            else:
                self.progress_bar.pack_forget()
                self.status_label.config(text="Error loading directory")


    def handle_progress(self, phase, immediate=False, wait_for_layers=False):
        """Update status text and animate progress bar for the given phase."""
        try:
            if phase == "Parsing JSON":
                target = 10  # Fast step
            elif phase == "Finding images":
                target = 50  # Images phase is mid-way
            elif phase == "Loading layers":
                target = 100  # Final phase (layers)
            else:
                return

            # Update status text
            self.status_label.config(text=phase)

            # Handle progress bar updates
            current = int(self.progress_bar['value'])

            if immediate:
                # If the step is immediate (like Parsing JSON), update immediately
                self.progress_bar['value'] = target
                self.root.update_idletasks()
                return

            # Standard update for other phases
            for val in range(current, target + 1):
                self.progress_bar['value'] = val
                self.root.update_idletasks()
                time.sleep(0.01)
            
        except Exception as e:
            print(f"Error during progress update: {e}")
            self.status_label.config(text=f"Error: {e}")


    def on_status_update(self, message: str):
        """Callback to update the status label text."""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def on_progress_update(self, value: int, message: str):
        """Callback to update the progress bar value and optionally the status text."""
        self.progress_bar['value'] = value
        if message:
            self.status_label.config(text=message)
        self.root.update_idletasks()
            
    def apply_layer_range(self):
        """Apply the layer range from entry boxes."""
        try:
            top = self.top_layer_entry.get().strip()
            bottom = self.bottom_layer_entry.get().strip()
            self.viewer.set_layer_range(top if top else None, bottom if bottom else None)
        except ValueError:
            self.status_label.config(text="Invalid layer range values")
        
    def toggle_quality(self):
        """Toggle between fast and quality render modes."""
        current_text = self.quality_button.cget('text')
        is_fast = current_text == "Fast Render"
        new_text = "Quality Render" if is_fast else "Fast Render"
        self.quality_button.config(text=new_text)
        self.viewer.set_quality_mode(is_fast)
        self.status_label.config(text="Updating render quality...")
        
    def run(self):
        """Start the main application loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = ViewerApp()
    app.run()
