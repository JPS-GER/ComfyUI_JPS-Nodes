"""
@author: JPS
@title: JPS Custom Nodes for ComfyUI
@nickname: JPS Custom Nodes
@description: Various nodes to handle SDXL Resolutions, SDXL Basic Settings, IP Adapter Settings, Revision Settings, SDXL Prompt Styler, Crop Image to Square, Crop Image to Target Size, Get Date-Time String, Resolution Multiply, Largest Integer, 5-to-1 Switches for Integer, Images, Latents, Conditioning, Model, VAE, ControlNet
"""

from .jps_nodes import NODE_CLASS_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS']
