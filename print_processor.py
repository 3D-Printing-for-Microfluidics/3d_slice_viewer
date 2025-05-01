import json
import os
import time
from PIL import Image
import numpy as np
from typing import Dict, Optional
from print_settings_parser import PrintSettingsParser, LayerInfo

class PrintProcessor:
    def __init__(self, texture_cache, on_status_update=None, on_progress_update=None):
        self.texture_cache = texture_cache
        self.slice_data = []
        self.settings_parser = PrintSettingsParser()
        self.pixel_size = 7.6  # microns
        self.layer_height = 10  # microns
        # Callback functions for status and progress updates
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update

        
    def load_print_directory(self, directory_path: str) -> bool:
        """Load a print directory containing minimized_slices and print_settings.json"""
        # Phase: Parsing JSON (print settings)
        if self.on_status_update:
            self.on_status_update("Parsing JSON")
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Print directory not found: {directory_path}")
            
        # Find print settings file
        settings_files = [f for f in os.listdir(directory_path) 
                          if f.startswith('print_settings') and f.endswith('.json')]
        if not settings_files:
            raise FileNotFoundError(f"No print settings file found in {directory_path}")
            
        # Load print settings
        settings_path = os.path.join(directory_path, settings_files[0])
        if self.on_status_update:
            self.on_status_update(f"Loading settings: {settings_path}")
        self.settings_parser.load_settings(settings_path)
        self.layer_height = self.settings_parser.get_layer_height()
        self.pixel_size = self.settings_parser.get_pixel_size()

        # Prepare progress tracking
        layer_sequence = self.settings_parser.layer_sequence
        # Compute total images for progress calculation
        self.total_images = sum(len(layer.images) for layer in layer_sequence)
        self.images_loaded = 0

        # Phase: Finding images (verify slices directory)
        if self.on_status_update:
            self.on_status_update("Finding images")
        slices_dir = os.path.join(directory_path, "minimized_slices")
        if not os.path.exists(slices_dir):
            raise FileNotFoundError(f"Minimized slices directory not found: {slices_dir}")
            
        if self.on_status_update:
            self.on_status_update("Loading layers")
        # Process slices directory
        self._process_print_layers(slices_dir)
        
        # Return True to indicate success.
        return True


    def _process_print_layers(self, slices_dir: str) -> None:
        """Process all print layers according to the sequence defined in settings"""
        self.slice_data = []
        
        # Get the complete layer sequence from settings
        layer_sequence = self.settings_parser.layer_sequence
        total_layers = len(layer_sequence)
        
        if total_layers == 0:
            return

        # Optional: notify total layers found
        if self.on_status_update:
            self.on_status_update(f"Processing {total_layers} layers")
        if self.on_progress_update:
            self.on_progress_update(0, f"0/{total_layers} layers loaded")
        
        # Process each layer in sequence
        for idx, layer_info in enumerate(layer_sequence, start=1):
            # Update status for loading this layer
            if self.on_status_update:
                self.on_status_update(f"Loading layer {idx}/{total_layers}")
            # Process the layer's images
            layer_data = self._process_layer_info(slices_dir, layer_info)
            if layer_data:
                layer_data['sequence_index'] = layer_info.sequence_index
                layer_data['layer_number'] = self._extract_layer_number(layer_info.images[0].image_file)
                if layer_info.duplicate_index is not None:
                    layer_data['duplicate_index'] = layer_info.duplicate_index
                self.slice_data.append(layer_data)

            # Update progress after processing this layer
            if self.on_progress_update:
                progress = int((idx / total_layers) * 100)
                self.on_progress_update(progress, f"{idx}/{total_layers} layers loaded")

        if self.on_status_update:
            self.on_status_update(f"Processed {len(self.slice_data)} layers using {self.settings_parser.get_unique_images()} unique images")

    
    def _process_layer_info(self, slices_dir: str, layer_info) -> Optional[Dict]:
        """Process a single layer based on its LayerInfo"""
        images = []
        exposure_times = []
        image_types = []
        texture_data = []  # Initialize texture_data list to hold texture info for each image

        for image_info in layer_info.images:
            full_path = os.path.join(slices_dir, image_info.image_file)
            
            if os.path.exists(full_path):
                if self.on_status_update:
                    self.on_status_update(f"Loading image: {image_info.image_file}")
                img = Image.open(full_path)
                img_array = np.array(img)
                images.append(img_array)
                exposure_times.append(image_info.exposure_time or 0.0)
                image_types.append(image_info.image_type)
                
                # Create texture data entry for this image (assuming texture generation here)
                texture_key = self.texture_cache.get_texture_key(img_array, True)  # Generate a texture key
                texture_data.append({
                    'img': img_array,
                    'texture_key': texture_key,
                    'image_type': image_info.image_type,
                    'exposure_time': image_info.exposure_time
                })

                # Incremental progress update for images
                if self.on_progress_update and hasattr(self, 'total_images'):
                    self.images_loaded += 1
                    progress = int((self.images_loaded / self.total_images) * 100)
                    self.on_progress_update(progress, f"Loaded image {self.images_loaded}/{self.total_images}")
            else:
                if self.on_status_update:
                    self.on_status_update(f"Warning: Image file not found: {full_path}")
                continue
                
        if not images:
            return None
            
        return {
            'images': images,
            'exposure_times': exposure_times,
            'image_types': image_types,
            'texture_data': texture_data  # Add texture data here
        }

    
    def _extract_layer_number(self, image_file: str) -> int:
        """Extract the layer number from an image filename"""
        filename = os.path.basename(image_file)
        try:
            return int(''.join(filter(str.isdigit, filename.split('_')[0])))
        except (ValueError, IndexError):
            return 0

    def get_slice_data(self):
        """Return the processed slice data."""
        return self.slice_data
    
    def get_slice_dimensions(self):
        """Get the dimensions of the slices in real-world units"""
        if not self.slice_data:
            return None
            
        height, width = self.slice_data[0]['images'][0].shape
        total_exposures = sum(len(layer['images']) for layer in self.slice_data)
        unique_images = self.settings_parser.get_unique_images()
        total_layers = self.settings_parser.get_total_layers()
        
        return {
            'width_microns': width * self.pixel_size,
            'height_microns': height * self.pixel_size,
            'depth_microns': len(self.slice_data) * self.layer_height,
            'unique_layers': unique_images,
            'total_layers': total_layers,
            'total_exposures': total_exposures
        }
