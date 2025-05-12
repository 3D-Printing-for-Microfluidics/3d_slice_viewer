# 3D Slice Viewer Software

## How to Use

### Installation
- Download all files from GitHub as .zip
- Extract the zip to wherever you want the program to be installed (ie C:/Homegrown Software/)
- Ensure that the extracted folder is named "3d_slice_viewer"
- Run "installer.bat"
- After that, you can use the included shortcut (3d_slice_viewer.lnk) to run the program. Shortcut can be placed on your desktop or anywhere else.
	- *Program will auto-update on start-up*
### To Use
- You will need a sliced print file that is UNZIPPED
- Make sure the highest level slices folder (same folder as the print_settings.json) is named "minimized_slices"
- Start the slice viewer program
- Click "Open Directory" in the top left (blue button) and select your print file folder
- Your print file should load in as a stack of slices arranged in 3D space and color-coded based on exposure time.
- The right side is populated with a color legend and toggles for turning each color on and off
- On the left, there are controls for which layers are visible, the opacity, and fast/quality render toggle. The quality stated on the button is the mode you are in.
- When switching to quality render, it will apply the higher resolution settings to only the currently visible layers. To reduce the time it takes to load, swap into quality mode only after you have found a specific selection of the layers that need analysis.
### 3D Navigation
- Left click and drag: orbit the model
- Right click and drag: pan the model (Currently always moves relative to the origin; the controls may not feel intuitive. Will be fixed in the future to pan relative to the camera.)
- Scroll wheel: zoom in and out

## Objectives

- An intuitive way to view slices with their exposures and how they may interact with nearby layers
- Learn more about TKinter for migrating/upgrading the current slicer from PySimpleGUI (paid now)
- Use the print files rather than an STL for a 3d view of your print

## Current Status

The software currently works like so:
- Takes an unzipped print file
- parses JSON for data about print and each layer
- finds all images and uses them to create textures
- each texture is colored according to the exposure time
	- colors assigned to each exposure time found in the JSON, each receiving a unique color
	- exposures +/-50 ms from each other are given a tint or shade of a middle color (groups no bigger than 3)
	- after loading, a legend is populated with the colors and their correspoding exposure time
	- after loading, a list of checkboxes is populated to toggle the visibility of each exposure time
- textures are applied to "cards" that are arranged as layers
	- cards on the same layer are separated by an "epsilon" value to avoid clipping
	- cards of different layers are arranged according to the layer height found in JSON
- loaded as batches of 10, the layers appear in the viewer and you can click and drag to navigate
	- panning has caused me a lot of problems, it doesn't quite work yet
- checkboxes for "Image Types" are also populated in the bottom left, usually it denotes which stl files are visible
- a slider in the control bar allows you to smoothly scroll through layers of a device for analysis
- to aid in loading speed, the layers are initially not full resolution. 
- a button can be used to swap into "Quality" mode, where textures have full resolution. 
- switching to quality mode can take a long time if a lot of layers are visible
- opacity can also be changed for analysis of the device, though the controls are currently just up/down arrow buttons

## Dependencies

program uses the following libraries:
*(full list and versions can be found in requirements.txt)*

	NumPy - scientific computing
    TKinter and ttkbootstrap - gui magic
    Pillow - image processing
    Panda3D - 3D rendering and viewer

## Next Steps

- Program only works with print files that contain a "minimized_slices" folder. For now, you can rename the highest-level folder of slices to "minimized_slices" and it should work fine.
- Currently doesn't support multi-resolution print files. The framework is there, though.
- The exposure times shown on the right bar when viewing a print are based on the JSON and not on the specified slicer exposure times. Maybe not an error, but definitely an important note.
- I think I want to combine the color legend with the hide/show selection boxes to make it more intuitive.