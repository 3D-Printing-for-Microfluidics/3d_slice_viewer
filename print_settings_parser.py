import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import os

@dataclass
class ImageInfo:
    """Information about a single image in a layer"""
    image_file: str
    exposure_time: Optional[float]
    focus_position: Optional[float]
    image_type: str  # 'main', 'extra', 'lower', 'defocus'
    power_setting: Optional[int]

@dataclass
class LayerInfo:
    """Information about a layer in the print sequence"""
    sequence_index: int
    images: List[ImageInfo]
    duplicate_index: Optional[int] = None

class PrintSettingsParser:
    def __init__(self):
        self.settings = None
        self.layer_sequence = []
        self.named_settings = {}
        self.default_settings = {}
        self.unique_images = set()
        
    def load_settings(self, settings_path: str) -> None:
        """Load and parse print settings from JSON file"""
        if not os.path.exists(settings_path):
            raise FileNotFoundError(f"Settings file not found: {settings_path}")
            
        with open(settings_path, 'r') as f:
            self.settings = json.load(f)
            
        # Store default settings
        if "Default layer settings" in self.settings:
            self.default_settings = self.settings["Default layer settings"].get("Image settings", {})
            
        # Store named settings
        if "Named image settings" in self.settings:
            self.named_settings = self.settings["Named image settings"]
            
        # Parse layer sequence
        self._parse_layer_sequence()
        
    def _get_image_type(self, image_file: str) -> str:
        # Use the directory name (first path component) as the image type.
        if not image_file:
            return 'unknown'
        # Normalize any backslashes and split on forward slash
        parts = image_file.replace('\\', '/').split('/')
        # The folder under minimized_slices is your type
        return parts[0] if parts and parts[0] else 'unknown'
        
    def _get_image_settings(self, img_settings: Dict, named_settings: Dict = None) -> ImageInfo:
        """Get complete image settings, combining defaults, named settings, and overrides"""
        # Start with default settings
        settings = self.default_settings.copy()
        
        # Apply named settings if specified
        if named_settings and "Using named image settings" in img_settings:
            named_key = img_settings["Using named image settings"]
            if named_key in named_settings:
                settings.update(named_settings[named_key])
                
        # Apply direct overrides from image settings
        settings.update(img_settings)
        
        # Create ImageInfo object
        return ImageInfo(
            image_file=settings.get("Image file", ""),
            exposure_time=settings.get("Layer exposure time (ms)"),
            focus_position=settings.get("Relative focus position (um)"),
            image_type=self._get_image_type(settings.get("Image file", "")),
            power_setting=settings.get("Light engine power setting")
        )
        
    def _parse_layer_sequence(self) -> None:
        """Parse the JSON to determine the complete sequence of layers"""
        self.layer_sequence = []
        sequence_index = 0
        
        # Find all sections that might contain layer settings
        sections_to_process = []
        
        # Check all top-level entries for potential layer settings
        for key, value in self.settings.items():
            if isinstance(value, list):
                # If it's a list, process items in sequence
                for item in value:
                    if isinstance(item, dict):
                        if "Image settings list" in item:
                            # Get number of duplications from the same dictionary
                            num_copies = item.get("Number of duplications", 1)
                            if num_copies > 1:
                                print(f"Found {num_copies} duplications for layer {sequence_index + 1}")
                            sections_to_process.append((item, num_copies))
            elif isinstance(value, dict):
                # If it's a dictionary, check if it has Image settings list
                if "Image settings list" in value:
                    num_copies = value.get("Number of duplications", 1)
                    sections_to_process.append((value, num_copies))
        
        print(f"Found {len(sections_to_process)} sections with layer settings")
        
        # Process each section that contains layer settings
        for section, num_copies in sections_to_process:
            if "Image settings list" in section:
                # Process all images for this layer
                images = []
                for img_settings in section["Image settings list"]:
                    image_info = self._get_image_settings(img_settings, self.named_settings)
                    if image_info.image_file:  # Skip empty image files
                        images.append(image_info)
                        self.unique_images.add(image_info.image_file)
                
                if images:  # Only process if we have valid images
                    # Add the layer the specified number of times
                    for copy_idx in range(num_copies):
                        layer_info = LayerInfo(
                            sequence_index=sequence_index,
                            images=images,
                            duplicate_index=copy_idx if num_copies > 1 else None
                        )
                        self.layer_sequence.append(layer_info)
                        sequence_index += 1
        
        print(f"Total layers in sequence: {len(self.layer_sequence)}")
        if self.layer_sequence:
            print(f"First layer images: {[img.image_file for img in self.layer_sequence[0].images]}")
            print(f"Last layer images: {[img.image_file for img in self.layer_sequence[-1].images]}")
            
    def get_layer_height(self) -> float:
        """Get layer height in microns"""
        if self.settings and "Default layer settings" in self.settings:
            return self.settings["Default layer settings"].get("Position settings", {}).get("Layer thickness (um)", 10.0)
        return 10.0  # Default value
        
    def get_pixel_size(self) -> float:
        """Get pixel size in microns"""
        return 7.6  # Default value - could be added to JSON in future
        
    def get_total_layers(self) -> int:
        """Get total number of layers including duplicates"""
        return len(self.layer_sequence)
        
    def get_unique_images(self) -> int:
        """Get number of unique images used"""
        return len(self.unique_images) 