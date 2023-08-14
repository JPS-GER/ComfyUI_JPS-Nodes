# JPS Custom Nodes for ComfyUI

These nodes were originally made for use in JPS ComfyUI Workflows.

The nodes can be used in any ComfyUI workflow.

# Installation

If you have a previous version of the "JPS Custom Nodes for ComfyUI", please delete this before installing these nodes.

1. cd custom_nodes
2. git clone https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git
3. Restart ComfyUI

You can also install the nodes using the following methods:
* install using [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)

# List of Custom Nodes

__SDXL__
* SDXL - Resolutions: optimized for a small size with only one dropdown input and width + height outputs
* SDXL - Basic Settings: SDXL_Resolutions and some other values you need most of the time in a single node
* SDXL - Additional Settings: additional settings used in my workflows (upscaler, face fix, etc.) 

__MATH__
* Math - Resolution Multiply: multiply width and height values by a defined factor (useful for SDXL workflows, try factor 2x)
* Math - Largest Integer: input two INT values, get the higher one - useful to find larger size of an image

__SWITCH__
* Switch - Generation Mode: switch between TXT2IMG and IMG2IMG - useful in combiantion with latent image switch nodes

# Credits

comfyanonymous/[ComfyUI](https://github.com/comfyanonymous/ComfyUI) - A powerful and modular stable diffusion GUI.

