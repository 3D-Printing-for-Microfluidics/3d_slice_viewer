import numpy as np
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import (
    Point3, Vec3, Vec4, CardMaker, Texture, GeomVertexFormat, GeomVertexData,
    GeomVertexWriter, Geom, GeomTriangles, GeomNode, NodePath, WindowProperties,
    Filename, TextNode, TransparencyAttrib
)
from print_processor import PrintProcessor
import os
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib
import cv2

import viewer_config
from viewer_config import lerp_color

# Define a tiny epsilon value for separation, ensuring textures don't clip
EPSILON = 1e-5  # A very small value to prevent clipping

class TextureCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    def get_texture_key(self, img_data, show_positive):
        m = hashlib.md5()
        m.update(img_data.tobytes())
        m.update(str(show_positive).encode())
        return m.hexdigest()
    def get(self, key):
        with self._lock:
            return self._cache.get(key)
    def put(self, key, texture):
        with self._lock:
            self._cache[key] = texture
    def clear(self):
        with self._lock:
            self._cache.clear()

class Viewer3D:
    def __init__(self, base):
        self.base = base
        if not self.base.mouseWatcherNode:
            self.base.setupMouse(self.base.win)
        # camera
        self.camera_target = viewer_config.INITIAL_CAMERA_TARGET
        self.camera_distance = viewer_config.INITIAL_CAMERA_DISTANCE
        self.camera_h = viewer_config.INITIAL_CAMERA_H
        self.camera_p = viewer_config.INITIAL_CAMERA_P
        self.mouse_down = False
        self.right_mouse_down = False
        self.last_x = self.last_y = 0
        self._pan_start_target = None
        self.setup_controls()
        # scene root
        self.root = self.base.render.attachNewNode("root")
        self.base.render.setShaderAuto()
        # modes
        self.show_positive = True
        self.high_quality = False
        self.void_highlight = False
        self.void_only      = False
        # UI state
        self.visible_range = {'top': None, 'bottom': None}
        # data
        self.slice_data = None
        self.total_layers = 0
        self.unique_layers = 0
        self.layer_height = None
        # caches & pools
        self.texture_cache = TextureCache()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.BATCH_SIZE = 10
        self.layer_opacity = 0.5
        # hook up controls
        self.setup_controls()

    def setup_controls(self):
        bw = self.base
        # Mouse button bindings for navigation
        bw.accept("mouse1", self.on_left_mouse_down)    # Left-click drag to orbit
        bw.accept("mouse1-up", self.on_left_mouse_up)
        bw.accept("mouse3", self.on_right_mouse_down)   # Right-click drag to pan
        bw.accept("mouse3-up", self.on_right_mouse_up)
        bw.accept("wheel_up", self.on_mouse_wheel_up)   # Scroll up to zoom in
        bw.accept("wheel_down", self.on_mouse_wheel_down)  # Scroll down to zoom out
        bw.accept("h", self.reset_view)                 # 'H' key to reset camera view
        bw.taskMgr.add(self.update, "camera-update")    # Task to update camera each frame

    # ── Public API ────────────────────────────────────────────────────────────

    def load_print_directory(self, directory, on_status_update=None, on_progress_update=None):
        if getattr(self, 'is_loading', False):
            return False
        try:
            # Pass the UI callbacks into PrintProcessor
            processor = PrintProcessor(self.texture_cache,
                                       on_status_update=on_status_update,
                                       on_progress_update=on_progress_update)
            if processor.load_print_directory(directory):
                self.print_processor = processor
                slice_data = processor.get_slice_data()
                dimensions = processor.get_slice_dimensions()
                self.load_slices(slice_data, dimensions, processor.layer_height)
                return True
        except Exception as e:
            print(f"Error loading print directory: {e}")
        return False


    def load_slices(self, slice_data, dimensions, layer_height):
        """Initialize and kick off batch loading of all layers."""
        # guard re-entry
        if getattr(self, 'is_loading', False):
            return
        self.is_loading = True

        # store metadata
        self.slice_data = slice_data
        self.total_layers = dimensions['total_layers']
        self.unique_layers = dimensions['unique_layers']
        self.layer_height = layer_height

        # dynamic type toggles
        all_types = {t for layer in slice_data for t in layer['image_types']}
        self.available_types = sorted(all_types)
        self.enabled_types = set(self.available_types)

        # dynamic exposure toggles
        all_exposures = {
            td.get('exposure_time')
            for layer in slice_data
            for td in layer.get('texture_data', [])
            if td.get('exposure_time') is not None
        }
        self.available_exposures = sorted(all_exposures)
        self.enabled_exposures = set(self.available_exposures)

        # reset scene
        self.root.removeNode()
        self.root = self.base.render.attachNewNode("root")
        self.layer_nodes = {}
        self.texture_cache.clear()

        # compute ranges
        self.update_layer_visibility()
        self.compute_exposure_range()

        # start batch load
        self.loading_batch = self.thread_pool.submit(self._prepare_next_batch, 0)
        self.base.taskMgr.add(self._check_batch_loading, "batch-loader")

    def toggle_image_type(self, img_type, enabled):
        if enabled:
            self.enabled_types.add(img_type)
        else:
            self.enabled_types.discard(img_type)

        # Update the visibility of layers based on enabled image types.
        for seq, node in self.layer_nodes.items():
            layer_data = self.slice_data[seq - 1]  # layer data for this node

            # Ensure 'texture_data' exists in the layer before accessing it
            if 'texture_data' not in layer_data:
                print(f"Warning: Missing 'texture_data' for layer {seq}. Skipping.")
                continue

            # Show or hide texture cards for the specific image type
            for idx, tex_data in enumerate(layer_data['texture_data']):
                if tex_data['image_type'] == img_type:
                    face = node.find(f"exposure_{idx}")
                    if face.isEmpty():
                        continue
                    # Show only if both image type and exposure are enabled
                    if img_type in self.enabled_types and tex_data.get('exposure_time') in self.enabled_exposures:
                        face.show()
                    else:
                        face.hide()

    def toggle_exposure(self, exposure, enabled):
        if enabled:
            self.enabled_exposures.add(exposure)
        else:
            self.enabled_exposures.discard(exposure)

        # Update the visibility of layers based on enabled exposures.
        for seq, node in self.layer_nodes.items():
            layer_data = self.slice_data[seq - 1]

            # Ensure 'texture_data' exists in the layer before accessing it
            if 'texture_data' not in layer_data:
                continue

            # Show or hide texture cards for the specific exposure time
            for idx, tex_data in enumerate(layer_data['texture_data']):
                if tex_data.get('exposure_time') == exposure:
                    face = node.find(f"exposure_{idx}")
                    if face.isEmpty():
                        continue
                    # Show only if both exposure and image type are enabled
                    if exposure in self.enabled_exposures and tex_data.get('image_type') in self.enabled_types:
                        face.show()
                    else:
                        face.hide()

    def set_void_highlight(self, on: bool):
        self.void_highlight = on
        if on: self.void_only = False
        self.reload_all_layers()

    def set_void_only(self, on: bool):
        self.void_only = on
        if on: self.void_highlight = False
        self.reload_all_layers()

    def set_quality_mode(self, high_quality: bool):
        self.high_quality = high_quality
        self.update_layer_quality()

    def set_layer_range(self, top=None, bottom=None):
        try:
            self.visible_range['top'] = int(top) if top is not None else None
            self.visible_range['bottom'] = int(bottom) if bottom is not None else None
            self.update_layer_visibility()
        except:
            print("Invalid layer range")

    def toggle_pixel_mode(self):
        self.show_positive = not self.show_positive
        self.texture_cache.clear()
        self.update_layer_quality()

    def reload_all_layers(self):
        self.is_loading = False
        self.load_slices(self.slice_data,
                         {'total_layers': self.total_layers, 'unique_layers': self.unique_layers},
                         self.layer_height)

    def reload_layer_by_type(self, img_type):
        """Reload only the layers related to the specified image type."""
        for seq, node in self.layer_nodes.items():
            layer_data = self.slice_data[seq - 1]
            updated_texture_data = []
            
            # Check all textures for the current layer and adjust visibility
            for tex_data in layer_data['texture_data']:
                if tex_data['image_type'] == img_type:
                    tex = self.texture_cache.get(tex_data['texture_key'])
                    if tex is None:
                        tex = self.create_texture_from_image(tex_data['img'])  # Assuming this method exists
                    face = node.find(f"exposure_{seq}")
                    face.setTexture(tex)
                    face.setColorScale(self.get_exposure_color(tex_data['exposure_time'], layer_data['layer_number']))
                    # Apply visibility toggle
                    if img_type in self.enabled_types:
                        face.show()
                    else:
                        face.hide()


    # ── Internal helpers ──────────────────────────────────────────────────────

    def compute_exposure_range(self):
        min_e = None; max_e = None
        for layer in self.slice_data:
            for exp in layer['exposure_times']:
                if exp is None: continue
                min_e = exp if min_e is None or exp < min_e else min_e
                max_e = exp if max_e is None or exp > max_e else max_e
        if min_e is None: min_e = 0
        if max_e is None or max_e == min_e: max_e = min_e + 1
        self.min_exposure, self.max_exposure = min_e, max_e
        print(f"Computed exposure range: {min_e}–{max_e} ms")

    def _prepare_next_batch(self, start_index):
        end = min(start_index + self.BATCH_SIZE, self.total_layers)
        batch = [self._prepare_layer_data(self.slice_data[i], i) for i in range(start_index, end)]
        return batch, start_index, end

    def _prepare_layer_data(self, layer, index):
        seq = index + 1
        ln  = layer.get('layer_number', seq)
        tex_list = []
        for img, exp, ttype in zip(layer['images'], layer['exposure_times'], layer['image_types']):
            if ttype not in self.enabled_types:
                continue
            tex_list.append({
                'img': img,
                'aspect_ratio': img.shape[1]/img.shape[0],
                'exposure_time': exp,
                'image_type': ttype,
                'texture_key': self.texture_cache.get_texture_key(img, self.show_positive)
            })
        return {'sequence_number': seq,
                'layer_number': ln,
                'texture_data': tex_list,
                'duplicate_index': layer.get('duplicate_index')}

    def _check_batch_loading(self, task):
        if not self.loading_batch.done():
            return task.cont
        batch, start, end = self.loading_batch.result()
        for layer_data in batch:
            self._create_layer_node(layer_data)
        if end < self.total_layers:
            self.loading_batch = self.thread_pool.submit(self._prepare_next_batch, end)
            return task.cont
        else:
            self.is_loading = False
            # center pivot
            b = self.root.getBounds().getCenter()
            self.root.setPos(-b.getX(), -b.getY(), -b.getZ())
            return task.done

    def _create_layer_node(self, data):
        seq = data['sequence_number']
        ln  = data['layer_number']
        node = self.root.attachNewNode(f"layer_{ln}")
        self.layer_nodes[seq] = node
        first = None
        y_offset = 0  # Start stacking from y_offset = 0

        for idx, td in enumerate(data['texture_data']):
            if first is None: first = td
            tex = self.texture_cache.get(td['texture_key'])
            if tex is None:
                tex = self.create_texture_from_image(td['img'])
            
            cm = CardMaker(f"exposure_{idx}")
            cm.setFrame(-td['aspect_ratio']/2, td['aspect_ratio']/2, -0.5, 0.5)
            face = node.attachNewNode(cm.generate())
            face.setR(90)  # Rotate the card to align properly
            face.setTwoSided(True)
            face.setTexture(tex)
            ### face.setColorScale(self.get_exposure_color(td['exposure_time'], data['layer_number'])) ### for gradient style exposure colors
            face.setColorScale(self.get_exposure_color(td['exposure_time'], data['layer_number']))
            face.setTransparency(TransparencyAttrib.MAlpha)
            face.setAlphaScale(self.layer_opacity)
            face.setDepthWrite(False)
            face.setBin("transparent", 0)
            
            # Stack cards with the epsilon value in the y_offset direction
            face.setPos(0, y_offset, 0)
            y_offset += EPSILON  # Increase the offset slightly to avoid clipping
        
        # Update layer position based on texture size
        if first:
            img = first['img']
            spacing = viewer_config.REAL_PROPORTION * min(img.shape[1], img.shape[0]) * viewer_config.IMAGE_SCALE_FACTOR
            node.setPos(0, -seq * spacing, 0)
            node.setScale(img.shape[1]/first['aspect_ratio'])

    def get_exposure_color(self, exposure_time, layer_number):
        """
        Assign a color to the given exposure time, grouping exposure times within ±50ms.
        Exposure times in the same group share a base color with light/dark variants.
        """
        # Gather all distinct exposure times from the slice data
        exposure_times = sorted({
            exp for layer in self.slice_data for exp in layer['exposure_times']
            if exp is not None
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
        # Assign colors to each exposure time based on its group
        exposure_time_to_color = {}
        color_list = viewer_config.EXPOSURE_COLORS
        color_count = len(color_list)
        for idx, group in enumerate(groups):
            base_hex = color_list[idx % color_count]
            # Convert base color from hex to Vec4 (RGBA) for calculations
            r = int(base_hex[1:3], 16) / 255.0
            g = int(base_hex[3:5], 16) / 255.0
            b = int(base_hex[5:7], 16) / 255.0
            base_color = Vec4(r, g, b, self.layer_opacity)
            # Prepare white and black (with same opacity) for shading
            white = Vec4(1.0, 1.0, 1.0, self.layer_opacity)
            black = Vec4(0.0, 0.0, 0.0, self.layer_opacity)
            if len(group) == 1:
                # Single exposure uses the base color
                exposure_time_to_color[group[0]] = base_color
            elif len(group) == 2:
                # Two exposures: lighter shade for lower value, darker for higher value
                light_color = lerp_color(base_color, white, 0.5)
                dark_color = lerp_color(base_color, black, 0.5)
                exposure_time_to_color[group[0]] = light_color
                exposure_time_to_color[group[1]] = dark_color
            elif len(group) == 3:
                # Three exposures: low→light, mid→base, high→dark
                light_color = lerp_color(base_color, white, 0.5)
                dark_color = lerp_color(base_color, black, 0.5)
                exposure_time_to_color[group[0]] = light_color
                exposure_time_to_color[group[1]] = base_color
                exposure_time_to_color[group[2]] = dark_color
        # Return the Vec4 color (default to white if exposure_time not found)
        color = exposure_time_to_color.get(exposure_time, Vec4(1.0, 1.0, 1.0, self.layer_opacity))
        return color


### for gradient style exposure colors ###
    # def get_exposure_color(self, exposure_time, layer_number):
    #     """
    #     Compute a pastel color based on exposure_time vs. the DEFAULT from JSON.
    #     Below default → green→yellow; above → yellow→red.
    #     """
    #     # Endpoints
    #     pastel_green  = Vec4(0.7, 1.0, 0.7, 1.0)
    #     pastel_yellow = Vec4(1.0, 1.0, 0.8, 1.0)
    #     pastel_red    = Vec4(1.0, 0.8, 0.8, 1.0)

    #     # Pull default exposure from your JSON settings, fall back to 270 ms.
    #     default_exposure = 270.0
    #     try:
    #         default_exposure = float(
    #             self.print_processor.settings_parser.settings
    #                 .get("Default layer settings", {})
    #                 .get("Image settings", {})
    #                 .get("Layer exposure time (ms)", 270.0)
    #         )
    #     except Exception:
    #         pass

    #     # Use default if none provided
    #     if exposure_time is None:
    #         exposure_time = default_exposure

    #     # Below or at default → interpolate green→yellow
    #     if exposure_time <= default_exposure:
    #         t = exposure_time / default_exposure
    #         base = lerp_color(pastel_green, pastel_yellow, t)
    #     else:
    #         # Above → interpolate yellow→red
    #         span = max(self.max_exposure - default_exposure, 1.0)
    #         t = (exposure_time - default_exposure) / span
    #         t = max(0.0, min(1.0, t))
    #         base = lerp_color(pastel_yellow, pastel_red, t)

    #     # Apply your UI opacity
    #     return Vec4(base[0], base[1], base[2], self.layer_opacity)

    def create_texture_from_image(self, img):
        base_key = self.texture_cache.get_texture_key(img, self.show_positive)
        q_key = f"{base_key}_{self.high_quality}_{self.layer_opacity:.2f}"
        tex = self.texture_cache.get(q_key)
        if tex: return tex
        if not self.high_quality:
            sf = 0.25
            img = cv2.resize(img, (int(img.shape[1]*sf), int(img.shape[0]*sf)), interpolation=cv2.INTER_AREA)
        img_rgba = np.zeros((*img.shape,4),dtype=np.uint8)
        a = int(255*self.layer_opacity)
        if self.show_positive:
            img_rgba[img>0] = [255,255,255,a]
        else:
            img_rgba[img==0] = [255,255,255,a]
        # void‐mode
        if self.void_only or self.void_highlight:
            img_rgba[img>0] = [0,0,0,0]
            if self.void_only:
                img_rgba[img==0] = [255,255,255,a]
            else:
                img_rgba[img==0] = [0,0,255,a]
        tex = Texture("layer_tex")
        tex.setup2dTexture(img_rgba.shape[1], img_rgba.shape[0],
                           Texture.T_unsigned_byte, Texture.F_rgba)
        tex.setRamImage(img_rgba.tobytes())
        if not self.high_quality:
            tex.setCompression(Texture.CMDefault)
        self.texture_cache.put(q_key, tex)
        return tex

    def update_layer_visibility(self):
        """Show/hide nodes by visible_range."""
        for seq, node in self.layer_nodes.items():
            vis = True
            top = self.visible_range['top']
            bot = self.visible_range['bottom']
            if top is not None and seq > top: vis = False
            if bot is not None and seq < bot: vis = False
            node.show() if vis else node.hide()

    def update_layer_quality(self):
        if not self.layer_nodes: return
        if not hasattr(self, 'status_text'):
            self.status_text = OnscreenText("", pos=viewer_config.STATUS_TEXT_POS,
                                           scale=viewer_config.STATUS_TEXT_SCALE,
                                           mayChange=True)
        self.status_text.setText("High Quality" if self.high_quality else "Fast Render")
        self.thread_pool.submit(self._update_layer_quality_async)

    def _update_layer_quality_async(self):
        for seq, node in self.layer_nodes.items():
            if node.isHidden(): continue
            layer = self.slice_data[seq-1]
            data  = self._prepare_layer_data(layer, seq-1)
            self.base.taskMgr.add(self._update_node_quality,
                                  f"uq_{seq}", extraArgs=[data], appendTask=True)
        def done(task):
            self.status_text.setText("Done Quality Update")
            return task.done
        self.base.taskMgr.add(done, "uq_done")

    def _update_node_quality(self, layer_data, task):
        seq = layer_data['sequence_number']
        node = self.layer_nodes.get(seq)
        if node:
            for idx, td in enumerate(layer_data['texture_data']):
                tex = self._get_quality_texture(td)
                face = node.find(f"exposure_{idx}")
                if not face.isEmpty():
                    face.setTexture(tex)
                    face.setColorScale(self.get_exposure_color(td['exposure_time'], layer_data['layer_number']))
        return task.done

    def _get_quality_texture(self, td):
        base_key = td['texture_key']
        q_key = f"{base_key}_{self.high_quality}_{self.layer_opacity:.2f}"
        tex = self.texture_cache.get(q_key)
        if tex: return tex
        img = td['img']
        if not self.high_quality:
            sf = 0.25
            img = cv2.resize(img, (int(img.shape[1]*sf), int(img.shape[0]*sf)), interpolation=cv2.INTER_AREA)
        img_rgba = np.zeros((*img.shape,4),dtype=np.uint8)
        if self.show_positive:
            img_rgba[img>0] = [255,255,255,255]
        else:
            img_rgba[img==0] = [255,255,255,255]
        if self.void_only or self.void_highlight:
            img_rgba[img>0] = [0,0,0,0]
            if self.void_only:
                img_rgba[img==0] = [255,255,255,255]
            else:
                a = int(255*self.layer_opacity)
                img_rgba[img==0] = [0,0,255,a]
        tex = Texture("layer_tex")
        tex.setup2dTexture(img_rgba.shape[1], img_rgba.shape[0],
                           Texture.T_unsigned_byte, Texture.F_rgba)
        tex.setRamImage(img_rgba.tobytes())
        if not self.high_quality:
            tex.setCompression(Texture.CMDefault)
        self.texture_cache.put(q_key, tex)
        return tex

    # --- Navigation Event Handlers and Camera Controls ---

    def on_left_mouse_down(self):
        self._start_drag('left')

    def on_left_mouse_up(self):
        self.mouse_down = False
        # Debug log on orbit drag release:
        if self.base.mouseWatcherNode.hasMouse():
            # Get camera world position and target
            cam_pos = self.base.camera.getPos(self.base.render)
            cam_target = self.camera_target
            # Get camera orientation vectors in world coords
            forward_vec = self.base.render.getRelativeVector(self.base.camera, Vec3(0, 1, 0)).normalized()
            right_vec   = self.base.render.getRelativeVector(self.base.camera, Vec3(1, 0, 0))
            up_vec      = self.base.render.getRelativeVector(self.base.camera, Vec3(0, 0, 1))
            # Pan delta is not applicable for orbit (set to zero vector)
            pan_delta = Vec3(0, 0, 0)
            # Print the collected debug info
            # print(f"Camera world position: {cam_pos}")
            # print(f"Camera target position: {cam_target}")
            # print(f"Forward direction (normalized): {forward_vec}")
            # print(f"Right vector: {right_vec}")
            # print(f"Up vector: {up_vec}")
            # print(f"Pan delta (last drag): {pan_delta}")

    def on_right_mouse_down(self):
        self._start_drag('right')

    def on_right_mouse_up(self):
        self.right_mouse_down = False
        # Debug log on pan drag release:
        if self.base.mouseWatcherNode.hasMouse():
            cam_pos = self.base.camera.getPos(self.base.render)
            cam_target = self.camera_target
            forward_vec = self.base.render.getRelativeVector(self.base.camera, Vec3(0, 1, 0)).normalized()
            right_vec   = self.base.render.getRelativeVector(self.base.camera, Vec3(1, 0, 0))
            up_vec      = self.base.render.getRelativeVector(self.base.camera, Vec3(0, 0, 1))
            # Calculate total pan delta using the stored start target
            pan_delta = Vec3(0, 0, 0)
            if self._pan_start_target is not None:
                pan_delta = cam_target - self._pan_start_target
            print(f"Camera world position: {cam_pos}")
            print(f"Camera target position: {cam_target}")
            print(f"Forward direction (normalized): {forward_vec}")
            print(f"Right vector: {right_vec}")
            print(f"Up vector: {up_vec}")
            print(f"Pan delta (last drag): {pan_delta}")
        self._pan_start_target = None  # Reset pan start tracker

    def _start_drag(self, button):
        if not self.base.mouseWatcherNode.hasMouse():
            return
        self.last_x = self.base.mouseWatcherNode.getMouseX()
        self.last_y = self.base.mouseWatcherNode.getMouseY()
        if button == 'left':
            self.mouse_down = True
            self._pan_start_target = None
        elif button == 'right':
            self.right_mouse_down = True
            self._pan_start_target = Point3(self.camera_target)

    def on_mouse_wheel_up(self):
        """Zoom in towards the center of the camera view."""
        old_dist = self.camera_distance
        new_dist = max(viewer_config.MIN_CAMERA_DISTANCE, old_dist * viewer_config.WHEEL_ZOOM_FACTOR)
        self.camera_distance = new_dist
        self.update_camera_position()

    def on_mouse_wheel_down(self):
        """Zoom out from the center of the camera view."""
        old_dist = self.camera_distance
        new_dist = min(viewer_config.MAX_CAMERA_DISTANCE, old_dist / viewer_config.WHEEL_ZOOM_FACTOR)
        self.camera_distance = new_dist
        self.update_camera_position()

    def update(self, task):
        if self.base.mouseWatcherNode.hasMouse():
            x = self.base.mouseWatcherNode.getMouseX()
            y = self.base.mouseWatcherNode.getMouseY()
            dx, dy = x - self.last_x, y - self.last_y
            if self.mouse_down:
                # Update orbiting
                self.camera_h += dx * viewer_config.ROTATION_SPEED
                self.camera_p = max(-89, min(89, self.camera_p - dy * viewer_config.ROTATION_SPEED))
                # Recalculate camera position based on spherical coordinates
                self.update_camera_position()
            elif self.right_mouse_down:
                # Get camera's orientation vectors for screen axes
                mat = self.base.camera.getNetTransform().getMat()
                right_vec = mat.getRow3(0)   # camera local X-axis (right)
                up_vec    = mat.getRow3(2)   # camera local Z-axis (up)
                right_vec.normalize()
                up_vec.normalize()
                # Scale by distance to keep speed consistent
                pan_factor = self.camera_distance * viewer_config.PAN_SPEED_FACTOR
                # Calculate scene movement in the direction of the mouse drag
                pan_offset = (right_vec * dx + up_vec * dy) * pan_factor
                # Move the entire scene (root node) by this offset
                self.root.setPos(self.root.getPos() + pan_offset)

            self.last_x, self.last_y = x, y
        self.update_camera_position()
        return task.cont

    def update_camera_position(self):
        """Update the camera's position based on spherical coordinates."""
        # Recalculate camera position based on spherical coordinates and target
        ph = np.deg2rad(self.camera_h)
        pp = np.deg2rad(self.camera_p)
        x = self.camera_distance * np.cos(pp) * np.sin(ph)
        y = self.camera_distance * np.cos(pp) * np.cos(ph)
        z = self.camera_distance * np.sin(pp)
        self.base.camera.setPos(self.camera_target + Vec3(x, y, z))
        self.base.camera.lookAt(self.camera_target)

    def reset_view(self):
        """Reset camera to the initial home position and orientation."""
        self.camera_target = Point3(viewer_config.INITIAL_CAMERA_TARGET)
        self.camera_distance = viewer_config.INITIAL_CAMERA_DISTANCE
        self.camera_h = viewer_config.INITIAL_CAMERA_H
        self.camera_p = viewer_config.INITIAL_CAMERA_P
        self.base.camera.setPos(viewer_config.INITIAL_CAMERA_POS)
        self.base.camera.lookAt(self.camera_target)

if __name__ == "__main__":
    base = ShowBase()
    viewer = Viewer3D(base)
    base.run()
