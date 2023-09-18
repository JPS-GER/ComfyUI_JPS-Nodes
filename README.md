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

__IO__
* Lora Loader - Lora Loader with On/Off Switch - output is 1 or 2, so it works with most "x to 1"-switches

__Settings__
* SDXL Resolutions - small node that offers recommended SDXL resolutions and outputs height and width values
* SDXL Basic Settings - menu node for basic SDXL settings, required for most SDXL workflows (connect to "SDXL Basic Settings Pipe" to access the values)
* Generation TXT IMG Settings - menu node to switch between TXT2IMG and IMG2IMG
* Generation Settings - menu node to switch between, TXT2IMG, IMG2IMG, Control Net Canny, Control Net Depth, Inpainting (conntect to "Generation Settings Pipe" to access the values) 
* IP Adapter Settings - menu node to turn on/off two IP adapter input images and settings (conntect to "IP Adapter Settings Pipe" to access the values)
* Revision Settings - menu node to turn on/off two revision input images and settings (conntect to "Revision Settings Pipe" to access the values)
* Sampler Scheduler Settings - menu node for sampler + scheduler settings, can also be used as pipe

__Switches__
* Integer Switch - "5 to 1"-switch for integer values
* Image Switch - "5 to 1"-switch for images
* Latent Switch - "5 to 1"-switch for latent images
* Conditioning Switch - "5 to 1"-switch for conditioning
* Model Switch - "5 to 1"-switch for models
* VAE Switch - "5 to 1"-switch for VAE
* ControlNet Switch - "5 to 1"-switch for ControlNet
* Disable Enable Switch - input for nodes that use "disable/enable" types of input (for example K-Sampler)
* Enable Disable Switch - input for nodes that use "enable/disable" types of input (for example K-Sampler)

__Pipes__
* SDXL Basic Settings Pipe - used to access data from "SDXL Basic Settings" menu node - place outside of the menu structure of your workflow
* Generation Settings Pipe - used to access data from "Generation Settings" menu node - place outside of the menu structure of your workflow 
* IP Adapter Settings Pipe - used to access data from "IP Adapter Settings" menu node - place outside of the menu structure of your workflow
* Revision Settings Pipe - used to access data from "Revision Settings" menu node - place outside of the menu structure of your workflow
* SDXL Fundamentals MultiPipe - used to build a pipe for basic SDXL settings, has input/outputs for all supported types, so you can access/change values more easily than classic "from/to/edit"-pipes
* Images Masks MultiPipe - used to build a pipe for various images and masks used in my workflow, has input/outputs for all images, so you can access/change images and masks more easily than classic "from/to/edit"-pipes 

__Math__
* SDXL Recommended Resolution Calc - gives you the closest recommended SDXL resolution for the width and height values, useful for IMG2IMG and ControlNet input images, to bring them in line with SDXL workflows
* Resolution Multiply - multily height and width by some factor - useful to get 2x or 4x values for upscaling or SDXL target width and SDXL target height
* Largest Int - input two integer values, output will be the larger value
* Multiply Int Int - multiply two integer inputs, output is available as integer and float, so you can save an extra node converting to the required type
* Multiply Int Float - multiply integer and float inputs, output is available as integer and float, so you can save an extra node converting to the required type
* Multiply Float Float - multiply two flout inputs, output is available as integer and float, so you can save an extra node converting to the required type
* Substract Int Int - subscract one integer input from another integer input, output is available as integer and float, so you can save an extra node converting to the required type

__Text__
* Text Concatenate - combine multiple input strings to one output string
* Get Date Time String - get current date/time (has extra code to make sure it will not use cached data)
* SDXL Prompt Handling - control how text_g and text_l input will be handled (many options)
  
__Image__
* Get Image Size - get width and height value from an input image, useful in combination with "Resolution Multiply" node

__Style__
* SDXL Prompt Styler - add movie and general styles to your text prompt - uses json files, so you can extend the available options

# Credits

SDXL Prompt Styler is based on work by twri - https://github.com/twri/sdxl_prompt_styler

