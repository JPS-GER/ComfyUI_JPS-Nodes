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
* SDXL - Resolutions: Optimized for a small node size with only one dropdown input and width + height outputs - AFAIK the smallest node that allows you to pick the resolutions recommended for SDXL.
* SDXL - Basic Settings: Includes "SDXL - Resolutions" and some other values you need for most SDXL workflows in a single node.
* SDXL - Recommended Resolution Calc: Changes Resolution values to the closest recommended SDXL resolution.

__MATH__
* Math - Resolution Multiply: Multiply width and height values by a defined factor (useful for SDXL workflows, it's recommended to use factor 2 for CLIPTextEncodeSDXL nodes)
* Math - Largest Integer: Input two INT values, get the higher one - useful to find larger size of an image
* Math - Multiply Int Int: Multiply two integer values, output as Integer and Float
* Math - Multiply Int Float: Multiply integer and float value, output as Integer and Float
* Math - Multiply Float Float: Multiply two float values, output as Integer and Float
* Math - Substract INT INT: Stubstract two integer values, output as Integer and Float
  
__SWITCHES__
* Switch - Generation Mode: Switch between TXT2IMG and IMG2IMG - useful in combiantion with latent image switch nodes, TXT2IMG will automatically set the image strength to zero.
* Switch - Generation Mode 4in1: Switch between TXT2IMG, IMG2IMG, Canny and Depth - adds Control Net Canny and Control Net Depth to the 2in1 switch. Now with inpainting (5in1).
* Switch - Revision Mode: Turn ON/OFF and finetune Revision through a single node.
* Switch - IP Adapter Mode: Turn ON/OFF and finetune IP Adapter through a single node.

__Menu__
* Menu - Sampler Scheduler: Can be used as menu item, but also allows you to redirect sampler and scheduler, which is not possible with "reroute" nodes.
* Menu - Disable Enable Switch: Use as input for Disable/Enable options
* Menu - Enable Disbale Switch: Use as input for Enable/Disable options (yes, somehow both data types exist, even in stock nodes)

__Filename__
* Filename - Get Date Time String: Get current date and time to contruct filenames - this one works, some similar nodes I found don't update without a browser refresh


# Credits

comfyanonymous/[ComfyUI](https://github.com/comfyanonymous/ComfyUI) - A powerful and modular stable diffusion GUI.

