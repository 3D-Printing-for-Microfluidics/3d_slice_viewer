# 3D Slice Viewer Software

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

	NumPy - scientific computing
    TKinter and ttkbootstrap - gui magic
    Pillow - image processing
    Panda3D - 3D rendering and viewer