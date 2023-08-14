# JPS ComfyUI Custom Nodes

These nodes were originally made for use in JPS ComfyUI Workflows.

The nodes can be used in any ComfyUI workflow.

# Installation

If you have a previous version of the Comfyroll nodes from the Comfyroll Worflow Templates download, please delete this before installing these nodes.

1. cd custom_nodes
2. git clone https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git
3. Restart ComfyUI

You can also install the nodes using the following methods:
* install using [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)

# List of Custom Nodes

__SDXL__
* SDXL_Resolutions - optimized for a small size with only one dropdown input and width + heigt output
* SDXL BasicSettings - SDXL_Resolutions and some other values you need most of the time in a single node
* SDXL AdditionalSettings - additional settings used in my workflows (upscaler, face fix, etc.) 

__MATH__
* Math ResolutionMultiply - multiply width and height values by a defined factor (useful for SDXL workflows, try factor 2x)
* Math LargestInt - input two INT values, get the higher one - useful to find larger size of an image

__SWITCH__
* Switch GenerationMode - switch between TXT2IMG and IMG2IMG - useful in combiantion with latent image switch nodes

# Credits

comfyanonymous/[ComfyUI](https://github.com/comfyanonymous/ComfyUI) - A powerful and modular stable diffusion GUI.

