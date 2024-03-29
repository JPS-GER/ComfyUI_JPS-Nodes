"""
@author: JPS
@title: JPS Custom Nodes for ComfyUI
@nickname: JPS Custom Nodes
@description: Various nodes to handle SDXL Resolutions, SDXL Basic Settings, IP Adapter Settings, Revision Settings, SDXL Prompt Styler, Crop Image to Square, Crop Image to Target Size, Get Date-Time String, Resolution Multiply, Largest Integer, 5-to-1 Switches for Integer, Images, Latents, Conditioning, Model, VAE, ControlNet
"""

#------------------------------------------------------------------------#
# JPS Custom Nodes          https://github.com/JPS-GER/ComfyUI_JPS-Nodes #
# for ComfyUI               https://github.com/comfyanonymous/ComfyUI    #
#------------------------------------------------------------------------#

import torch
import json
import os
import comfy.sd
import folder_paths
from datetime import datetime
from PIL import Image, ImageOps, ImageSequence
import numpy as np
from PIL.PngImagePlugin import PngInfo
from comfy.cli_args import args
import torch.nn.functional as F

def min_(tensor_list):
    # return the element-wise min of the tensor list.
    x = torch.stack(tensor_list)
    mn = x.min(axis=0)[0]
    return torch.clamp(mn, min=0)
    
def max_(tensor_list):
    # return the element-wise max of the tensor list.
    x = torch.stack(tensor_list)
    mx = x.max(axis=0)[0]
    return torch.clamp(mx, max=1)

# From https://github.com/Jamy-L/Pytorch-Contrast-Adaptive-Sharpening/
def contrast_adaptive_sharpening(image, amount):
    img = F.pad(image, pad=(1, 1, 1, 1)).cpu()

    a = img[..., :-2, :-2]
    b = img[..., :-2, 1:-1]
    c = img[..., :-2, 2:]
    d = img[..., 1:-1, :-2]
    e = img[..., 1:-1, 1:-1]
    f = img[..., 1:-1, 2:]
    g = img[..., 2:, :-2]
    h = img[..., 2:, 1:-1]
    i = img[..., 2:, 2:]
    
    # Computing contrast
    cross = (b, d, e, f, h)
    mn = min_(cross)
    mx = max_(cross)
    
    diag = (a, c, g, i)
    mn2 = min_(diag)
    mx2 = max_(diag)
    mx = mx + mx2
    mn = mn + mn2
    
    # Computing local weight
    inv_mx = torch.reciprocal(mx)
    amp = inv_mx * torch.minimum(mn, (2 - mx))

    # scaling
    amp = torch.sqrt(amp)
    w = - amp * (amount * (1/5 - 1/8) + 1/8)
    div = torch.reciprocal(1 + 4*w)

    output = ((b + d + f + h)*w + e) * div
    output = output.clamp(0, 1)
    output = torch.nan_to_num(output)

    return (output)

def read_json_file(file_path):
    """
    Reads a JSON file's content and returns it.
    Ensures content matches the expected format.
    """
    if not os.access(file_path, os.R_OK):
        print(f"Warning: No read permissions for file {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = json.load(file)
            # Check if the content matches the expected format.
            if not all(['name' in item and 'prompt' in item and 'negative_prompt' in item for item in content]):
                print(f"Warning: Invalid content in file {file_path}")
                return None
            return content
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {str(e)}")
        return None

def read_sdxl_styles(json_data):
    """
    Returns style names from the provided JSON data.
    """
    if not isinstance(json_data, list):
        print("Error: input data must be a list")
        return []

    return [item['name'] for item in json_data if isinstance(item, dict) and 'name' in item]

def get_all_json_files(directory):
    """
    Returns all JSON files from the specified directory.
    """
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.json') and os.path.isfile(os.path.join(directory, file))]

def load_styles_from_directory(directory):
    """
    Loads styles from all JSON files in the directory.
    Renames duplicate style names by appending a suffix.
    """
    json_files = get_all_json_files(directory)
    combined_data = []
    seen = set()

    for json_file in json_files:
        json_data = read_json_file(json_file)
        if json_data:
            for item in json_data:
                original_style = item['name']
                style = original_style
                suffix = 1
                while style in seen:
                    style = f"{original_style}_{suffix}"
                    suffix += 1
                item['name'] = style
                seen.add(style)
                combined_data.append(item)

    unique_style_names = [item['name'] for item in combined_data if isinstance(item, dict) and 'name' in item]
    
    return combined_data, unique_style_names

def validate_json_data(json_data):
    """
    Validates the structure of the JSON data.
    """
    if not isinstance(json_data, list):
        return False
    for template in json_data:
        if 'name' not in template or 'prompt' not in template:
            return False
    return True

def find_template_by_name(json_data, template_name):
    """
    Returns a template from the JSON data by name or None if not found.
    """
    for template in json_data:
        if template['name'] == template_name:
            return template
    return None

def split_template(template: str) -> tuple:
    """
    Splits a template into two parts based on a specific pattern.
    """
    if "{prompt} ." in template:
        template_prompt_g, template_prompt_l = template.split("{prompt} .", 1)
        template_prompt_g = template_prompt_g.strip() + " {prompt}"
        template_prompt_l = template_prompt_l.strip()
    else:
        template_prompt_g = template
        template_prompt_l = ""

    return template_prompt_g, template_prompt_l

def replace_prompts_in_template(template, positive_prompt_g, positive_prompt_l, negative_prompt):
    """
    Replace the placeholders in a given template with the provided prompts and split them accordingly.
    
    Args:
    - template (dict): The template containing prompt placeholders.
    - positive_prompt_g (str): The main positive prompt to replace '{prompt}' in the template.
    - positive_prompt_l (str): The auxiliary positive prompt to be combined in a specific manner.
    - negative_prompt (str): The negative prompt to be combined with any existing negative prompt in the template.

    Returns:
    - tuple: A tuple containing the replaced main positive, auxiliary positive, combined positive and negative prompts.
    """
    template_prompt_g, template_prompt_l_template = split_template(template['prompt'])

    text_g_positive = template_prompt_g.replace("{prompt}", positive_prompt_g)

    text_l_positive = f"{template_prompt_l_template}, {positive_prompt_l}" if template_prompt_l_template and positive_prompt_l else template_prompt_l_template or positive_prompt_l

    json_negative_prompt = template.get('negative_prompt', "")
    text_negative = f"{json_negative_prompt}, {negative_prompt}" if json_negative_prompt and negative_prompt else json_negative_prompt or negative_prompt

    return text_g_positive, text_l_positive, text_negative


def read_sdxl_templates_replace_and_combine(json_data, template_name, positive_prompt_g, positive_prompt_l, negative_prompt):
    """
    Find a specific template by its name, then replace and combine its placeholders with the provided prompts in an advanced manner.
    
    Args:
    - json_data (list): The list of templates.
    - template_name (str): The name of the desired template.
    - positive_prompt_g (str): The main positive prompt.
    - positive_prompt_l (str): The auxiliary positive prompt.
    - negative_prompt (str): The negative prompt to be combined.

    Returns:
    - tuple: A tuple containing the replaced and combined main positive, auxiliary positive, combined positive and negative prompts.
    """
    if not validate_json_data(json_data):
        return positive_prompt_g, positive_prompt_l, negative_prompt

    template = find_template_by_name(json_data, template_name)

    if template:
        return replace_prompts_in_template(template, positive_prompt_g, positive_prompt_l, negative_prompt)
    else:
        return positive_prompt_g, positive_prompt_l, negative_prompt

accepted_ratios_horizontal = {
    "12:5": (1536, 640, 2.400000000),
    "7:4": (1344, 768, 1.750000000),
    "19:13": (1216, 832, 1.461538462),
    "9:7": (1152, 896, 1.285714286)
}

# Vertical aspect ratio
accepted_ratios_vertical = {
    "7:9": (896, 1152, 0.777777778),
    "13:19": (832, 1216, 0.684210526),
    "4:7": (768, 1344, 0.571428571),
    "5:12": (640, 1536, 0.416666667)
}
    
# Square aspect ratio
accepted_ratios_square = {
    "1:1": (1024, 1024, 1.00000000)
}


class SDXL_Resolutions:
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "resolution": (s.resolution,),
            }
        }
    RETURN_TYPES = ("INT","INT",)
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolutions"

    CATEGORY="JPS Nodes/Settings"

    def get_resolutions(self,resolution):
        width = 1024
        height = 1024
        width = int(width)
        height = int(height)
        if(resolution == "square - 1024x1024 (1:1)"):
            width = 1024
            height = 1024
        if(resolution == "landscape - 1152x896 (4:3)"):
            width = 1152
            height = 896
        if(resolution == "landscape - 1216x832 (3:2)"):
            width = 1216
            height = 832
        if(resolution == "landscape - 1344x768 (16:9)"):
            width = 1344
            height = 768
        if(resolution == "landscape - 1536x640 (21:9)"):
            width = 1536
            height = 640
        if(resolution == "portrait - 896x1152 (3:4)"):
            width = 896
            height = 1152
        if(resolution == "portrait - 832x1216 (2:3)"):
            width = 832
            height = 1216
        if(resolution == "portrait - 768x1344 (9:16)"):
            width = 768
            height = 1344
        if(resolution == "portrait - 640x1536 (9:21)"):
            width = 640
            height = 1536
            
        return(int(width),int(height))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Basic_Settings:
    resolution = ["Use Image Resolution", "square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "resolution": (s.resolution,),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "steps_total": ("INT", {"default": 60, "min": 20, "max": 250, "step": 5}),
                "base_percentage": ("INT", {"default": 80, "min": 5, "max": 100, "step": 5}),
                "cfg_base": ("FLOAT", {"default": 6.5, "min": 1, "max": 20, "step": 0.1}),
                "cfg_refiner": ("FLOAT", {"default": 6.5, "min": 0, "max": 20, "step": 0.1}),
                "ascore_refiner": ("FLOAT", {"default": 6, "min": 1, "max": 10, "step": 0.5}),
                "clip_skip": ("INT", {"default": -2, "min": -24, "max": -1}),
                "filename": ("STRING", {"default": "JPS"}),
        }}
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("sdxl_basic_settings",)
    FUNCTION = "get_values"

    CATEGORY="JPS Nodes/Settings"

    def get_values(self,resolution,sampler_name,scheduler,steps_total,base_percentage,cfg_base,cfg_refiner,ascore_refiner,clip_skip,filename):
        width = 1024
        height = 1024
        width = int(width)
        height = int(height)
        steps_total = int(steps_total)
        step_split = steps_total * base_percentage / 100
        cfg_base = float(cfg_base)
        cfg_refiner = float (cfg_refiner)
        ascore_refiner = float (ascore_refiner)
        base_percentage = int (base_percentage)
        image_res = 1

        if(resolution == "Use Image Resolution"):
            image_res = 2
        if(resolution == "square - 1024x1024 (1:1)"):
            width = 1024
            height = 1024
        if(resolution == "landscape - 1152x896 (4:3)"):
            width = 1152
            height = 896
        if(resolution == "landscape - 1216x832 (3:2)"):
            width = 1216
            height = 832
        if(resolution == "landscape - 1344x768 (16:9)"):
            width = 1344
            height = 768
        if(resolution == "landscape - 1536x640 (21:9)"):
            width = 1536
            height = 640
        if(resolution == "portrait - 896x1152 (3:4)"):
            width = 896
            height = 1152
        if(resolution == "portrait - 832x1216 (2:3)"):
            width = 832
            height = 1216
        if(resolution == "portrait - 768x1344 (9:16)"):
            width = 768
            height = 1344
        if(resolution == "portrait - 640x1536 (9:21)"):
            width = 640
            height = 1536

        if(cfg_refiner == 0):
            cfg_refiner = cfg_base
        
        sdxl_basic_settings = width, height, sampler_name, scheduler, steps_total, step_split, cfg_base, cfg_refiner, ascore_refiner, clip_skip, filename,image_res

        return(sdxl_basic_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Basic_Settings_Pipe:
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sdxl_basic_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("INT","INT","INT",comfy.samplers.KSampler.SAMPLERS,comfy.samplers.KSampler.SCHEDULERS,"INT","INT","FLOAT","FLOAT","FLOAT","INT","STRING",)
    RETURN_NAMES = ("image_res","width","height","sampler_name","scheduler","steps_total","step_split","cfg_base","cfg_refiner","ascore_refiner","clip_skip","filename",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,sdxl_basic_settings):
        
        width, height, sampler_name, scheduler, steps_total, step_split, cfg_base, cfg_refiner, ascore_refiner, clip_skip, filename,image_res = sdxl_basic_settings

        return(int(image_res), int(width), int(height), sampler_name, scheduler, int(steps_total), int(step_split), float(cfg_base), float(cfg_refiner), float(ascore_refiner), int(clip_skip), str(filename),)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Prompt_Handling_Plus:
    handling = ["Copy to Both if Empty","Use Positive_G + Positive_L","Copy Positive_G to Both","Copy Positive_L to Both","Ignore Positive_G Input", "Ignore Positive_L Input", "Combine Positive_G + Positive_L", "Combine Positive_L + Positive_G",]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "handling": (s.handling,),
                "pos_g": ("STRING", {"multiline": True, "placeholder": "Prompt Text pos_g"}),
                "pos_l": ("STRING", {"multiline": True, "placeholder": "Prompt Text pos_l"}),
            },
        }
    
    RETURN_TYPES = ("STRING","STRING",)
    RETURN_NAMES = ("pos_g","pos_l",)
    FUNCTION = "pick_handling"

    CATEGORY="JPS Nodes/Text"

    def pick_handling(self,handling,pos_g,pos_l):
        
        if(handling == "Copy Positive_G to Both"):
            pos_l = pos_g
        elif(handling == "Copy Positive_L to Both"):
            pos_g = pos_l
        elif(handling == "Ignore Positive_G Input"):
            pos_g = ''
        elif(handling == "Ignore Positive_L Input"):
            pos_l = ''
        elif(handling == "Combine Positive_G + Positive_L"):
            combine = pos_g + ' . ' + pos_l
            pos_g = combine
            pos_l = combine
        elif(handling == "Combine Positive_L + Positive_G"):
            combine = pos_l + ' . ' + pos_g
            pos_g = combine
            pos_l = combine
        elif(handling == "Copy to Both if Empty" and pos_l == ''):
            pos_l = pos_g
        elif(handling == "Copy to Both if Empty" and pos_g == ''):
            pos_g = pos_l

        return(pos_g,pos_l,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Text_Prompt:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "placeholder": "Prompt Text"}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "text_prompt"

    CATEGORY="JPS Nodes/Text"

    def text_prompt(self,text):

        return(text,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Prompt_Handling:
    handling = ["Copy to Both if Empty","Use Positive_G + Positive_L","Copy Positive_G to Both","Copy Positive_L to Both","Ignore Positive_G Input", "Ignore Positive_L Input", "Combine Positive_G + Positive_L", "Combine Positive_L + Positive_G",]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "handling": (s.handling,),
                "pos_g": ("STRING", {"default": ""}),
                "pos_l": ("STRING", {"default": ""}),
            },
        }
    RETURN_TYPES = ("STRING","STRING",)
    RETURN_NAMES = ("pos_g","pos_l",)
    FUNCTION = "pick_handling"

    CATEGORY="JPS Nodes/Text"

    def pick_handling(self,handling,pos_g,pos_l,):
        
        if(handling == "Copy Positive_G to Both"):
            pos_l = pos_g
        elif(handling == "Copy Positive_L to Both"):
            pos_g = pos_l
        elif(handling == "Ignore Positive_G Input"):
            pos_g = ''
        elif(handling == "Ignore Positive_L Input"):
            pos_l = ''
        elif(handling == "Combine Positive_G + Positive_L"):
            combine = pos_g + ' . ' + pos_l
            pos_g = combine
            pos_l = combine
        elif(handling == "Combine Positive_L + Positive_G"):
            combine = pos_l + ' . ' + pos_g
            pos_g = combine
            pos_l = combine
        elif(handling == "Copy to Both if Empty" and pos_l == ''):
            pos_l = pos_g
        elif(handling == "Copy to Both if Empty" and pos_g == ''):
            pos_g = pos_l

        return(pos_g,pos_l,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Resolution_Multiply:
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 256, "max": 8192, "step": 16}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 8192, "step": 16}),
                "factor": ("INT", {"default": 2, "min": 1, "max": 8, "step": 1}),
        }}
    RETURN_TYPES = ("INT","INT")
    RETURN_NAMES = ("width_resized", "height_resized")
    FUNCTION = "get_newres"

    CATEGORY="JPS Nodes/Math"

    def get_newres(self,width,height,factor):
        factor = int(factor)
        width = int(width)
        width_resized = int(width) * int(factor)
        height = int(height)
        height_resized = int (height) * int(factor)
            
        return(int(width_resized),int(height_resized))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Largest_Integer:

    def init(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "int_a": ("INT", {"default": 1,}),
                "int_b": ("INT", {"default": 1,}),
            }
        }

    RETURN_TYPES = ("INT","INT","INT")
    RETURN_NAMES = ("larger_int","smaller_int","is_a_larger")
    FUNCTION = "get_lrg"

    CATEGORY="JPS Nodes/Math"

    def get_lrg(self,int_a,int_b):
        larger_int = int(int_b)
        smaller_int = int(int_a)
        is_a_larger = int(0)
        if int_a > int_b:
            larger_int = int(int_a)
            smaller_int = int(int_b)
            is_a_larger = int(1)

        return(int(larger_int),int(smaller_int),int(is_a_larger))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Multiply_INT_INT:

    def init(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "int_a": ("INT", {"default": 1,}),
                "int_b": ("INT", {"default": 1,}),
            }
        }

    RETURN_TYPES = ("INT","FLOAT")
    RETURN_NAMES = ("int_multiply","float_multiply")
    FUNCTION = "get_multiply_int_int"

    CATEGORY="JPS Nodes/Math"

    def get_multiply_int_int(self,int_a,int_b):
        int_multiply = int(int_a) * int(int_b)
        float_multiply = int(int_a) * int(int_b)

        return(int(int_multiply),float(float_multiply))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Multiply_INT_FLOAT:

    def init(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "int_a": ("INT", {"default": 1,}),
                "float_b": ("FLOAT", {"default": 1,}),
            }
        }

    RETURN_TYPES = ("INT","FLOAT")
    RETURN_NAMES = ("int_multiply","float_multiply")
    FUNCTION = "get_multiply_int_float"

    CATEGORY="JPS Nodes/Math"

    def get_multiply_int_float(self,int_a,float_b):
        int_multiply = int(int_a) * float(float_b)
        float_multiply = int(int_a) * float(float_b)

        return(int(int_multiply),float(float_multiply))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Multiply_FLOAT_FLOAT:

    def init(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "float_a": ("FLOAT", {"default": 1,}),
                "float_b": ("FLOAT", {"default": 1,}),
            }
        }

    RETURN_TYPES = ("INT","FLOAT")
    RETURN_NAMES = ("int_multiply","float_multiply")
    FUNCTION = "get_multiply_float_float"

    CATEGORY="JPS Nodes/Math"

    def get_multiply_float_float(self,float_a,float_b):
        int_multiply = float(float_a) * float(float_b)
        float_multiply = float(float_a) * float(float_b)

        return(int(int_multiply),float(float_multiply))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Math_Substract_INT_INT:

    def init(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "int_a": ("INT", {"default": 1,}),
                "int_b": ("INT", {"default": 1,}),
            }
        }

    RETURN_TYPES = ("INT","FLOAT")
    RETURN_NAMES = ("int_substract","float_substract")
    FUNCTION = "get_substract_int_int"

    CATEGORY="JPS Nodes/Math"

    def get_substract_int_int(self,int_a,int_b):
        int_substract = int(int_a) - int(int_b)
        float_substract = int(int_a) - int(int_b)

        return(int(int_substract),float(float_substract))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Text_Concatenate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "delimiter": (["none", "space", "comma"],),
            },
            "optional": {
                "text1": ("STRING", {"forceInput": True}),
                "text2": ("STRING", {"forceInput": True}),      
                "text3": ("STRING", {"forceInput": True}),      
                "text4": ("STRING", {"forceInput": True}),      
                "text5": ("STRING", {"forceInput": True}),       
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "get_contxt"
    CATEGORY = "JPS Nodes/Text"

    def get_contxt(self, delimiter, text1=None, text2=None, text3=None, text4=None, text5=None):
        needdelim = False
        delim = ""
        if delimiter == "space":
            delim = " "
        if delimiter == "comma":
            delim = ", "

        concatenated = ""

        if text1:
            concatenated = text1
            needdelim = True
        
        if text2:
            if needdelim:
                concatenated += delim
            concatenated += text2
            needdelim = True
        
        if text3:
            if needdelim:
                concatenated += delim
            concatenated += text3
            needdelim = True

        if text4:
            if needdelim:
                concatenated += delim
            concatenated += text4
            needdelim = True

        if text5:
            if needdelim:
                concatenated += delim
            concatenated += text5
            needdelim = True

        return (concatenated,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Get_Date_Time_String:
    time_format = ["%Y%m%d%H%M%S","%Y%m%d%H%M","%Y%m%d","%Y-%m-%d-%H_%M_%S","%Y-%m-%d-%H_%M","%Y-%m-%d","%Y-%m-%d %H_%M_%S","%Y-%m-%d %H_%M","%Y-%m-%d","%H%M","%H%M%S","%H_%M","%H_%M_%S"]
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "style": (s.time_format,),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("time_format",)
    FUNCTION = "get_time"

    CATEGORY = "JPS Nodes/Text"

    def get_time(self, style):
        now = datetime.now()
        timestamp = now.strftime(style)

        return (timestamp,)

    @classmethod
    def IS_CHANGED(s, style):
        now = datetime.now()
        timestamp = now.strftime(style)
        return (timestamp,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Recommended_Resolution_Calc:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_width": ("INT", {
                    "default": 1024, 
                    "min": 0, 
                    "max": 8192, 
                    "step": 2 
                }),
                "target_height": ("INT", {
                    "default": 1024, 
                    "min": 0, 
                    "max": 8192, 
                    "step": 2 
                }),
            },
        }

    RETURN_TYPES = ("INT","INT",)
    RETURN_NAMES = ("SDXL_width","SDXL_height",)
    FUNCTION = "calcSDXLres"

    CATEGORY = "JPS Nodes/Math"

    def calcSDXLres(self, target_width, target_height):
        target_ratio = target_width / target_height
        
        closest_ratio = None
        closest_diff = float('inf')
        
        for ratio, (x_size, y_size, num_ratio) in accepted_ratios_horizontal.items():
            diff = abs(num_ratio - target_ratio)
            if diff < closest_diff:
                closest_ratio = ratio
                closest_diff = diff
        
        for ratio, (x_size, y_size, num_ratio) in accepted_ratios_vertical.items():
            diff = abs(num_ratio - target_ratio)
            if diff < closest_diff:
                closest_ratio = ratio
                closest_diff = diff
        
        # Compare with square aspect ratio
        x_size, y_size, num_ratio = accepted_ratios_square["1:1"]
        diff = abs(num_ratio - target_ratio)
        if diff < closest_diff:
            closest_ratio = "1:1"

        if closest_ratio in accepted_ratios_horizontal:
            SDXL_width, SDXL_height, _ = accepted_ratios_horizontal[closest_ratio]
        elif closest_ratio in accepted_ratios_vertical:
            SDXL_width, SDXL_height, _ = accepted_ratios_vertical[closest_ratio]
        else:
            SDXL_width, SDXL_height, _ = accepted_ratios_square[closest_ratio]
        
        return (SDXL_width, SDXL_height)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Generation_TXT_IMG_Settings:
    mode = ["Txt2Img","Img2Img"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (s.mode,),
                "img_percentage": ("INT", {"default": 50, "min": 0, "max": 100, "step": 5}),
            }
        }
    RETURN_TYPES = ("INT","FLOAT",)
    RETURN_NAMES = ("gen_mode", "img_strength")
    FUNCTION = "get_genmode"

    CATEGORY="JPS Nodes/Settings"

    def get_genmode(self,mode,img_percentage):
        gen_mode = 1
        img_strength = 0
        if(mode == "Txt2Img"):
            gen_mode = int(1)
            img_strength = 0.001
        if(mode == "Img2Img"):
            gen_mode = int(2)
            img_strength = img_percentage / 100
            
        return(int(gen_mode),float(img_strength))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CropImage_Settings:
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "source_crop_pos": (["center","top", "bottom", "left", "right"],),
                "source_crop_offset": ("INT", { "default": 0, "min": -2048, "max": 2048, "step": 1, "display": "number" }),
                "support_crop_pos": (["center","top", "bottom", "left", "right"],),
                "support_crop_offset": ("INT", { "default": 0, "min": -2048, "max": 2048, "step": 1, "display": "number" }),
                "crop_intpol": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("cropimage_settings",)
    FUNCTION = "get_cropimage"

    CATEGORY="JPS Nodes/Settings"

    def get_cropimage(self, source_crop_pos, source_crop_offset, support_crop_pos, support_crop_offset, crop_intpol,):
       
        cropimage_settings = source_crop_pos, source_crop_offset, support_crop_pos, support_crop_offset, crop_intpol

        return(cropimage_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CropImage_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cropimage_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = (["center","top", "bottom", "left", "right"],"INT",["center","top", "bottom", "left", "right"],"INT",["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],)
    RETURN_NAMES = ("source_crop_pos", "source_crop_offset", "support_crop_pos", "support_crop_offset", "crop_intpol",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,cropimage_settings):
        
        source_crop_pos, source_crop_offset, support_crop_pos, support_crop_offset, crop_intpol = cropimage_settings

        return(source_crop_pos, source_crop_offset, support_crop_pos, support_crop_offset, crop_intpol,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class ImageToImage_Settings:
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "img2img_strength": ("INT", {"default": 50, "min": 0, "max": 100, "step": 1}),
                "inpaint_strength": ("INT", {"default": 100, "min": 2, "max": 100, "step": 1}),
                "inpaint_grow_mask": ("INT", {"default": 20, "min": 0, "max": 200, "step": 2}),
                "unsampler_strength": ("INT", {"default": 30, "min": 0, "max": 100, "step": 1}),
                "unsampler_cfg": ("FLOAT", {"default": 1, "min": 1, "max": 10, "step": 0.1}),
                "unsampler_sampler": (comfy.samplers.KSampler.SAMPLERS,),
                "unsampler_scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("img2img_settings",)
    FUNCTION = "get_img2img"

    CATEGORY="JPS Nodes/Settings"

    def get_img2img(self, img2img_strength, inpaint_strength, inpaint_grow_mask, unsampler_strength, unsampler_cfg, unsampler_sampler, unsampler_scheduler,):

        img2img_strength = (img2img_strength + 0.001) / 100

        inpaint_strength = (100 - inpaint_strength + 0.001) / 100

        unsampler_strength = (unsampler_strength + 0.001) / 100
        
        img2img_settings = img2img_strength, inpaint_strength, inpaint_grow_mask, unsampler_strength, unsampler_cfg, unsampler_sampler, unsampler_scheduler

        return(img2img_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class ImageToImage_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "img2img_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("FLOAT", "FLOAT", "INT", "FLOAT", "FLOAT", comfy.samplers.KSampler.SAMPLERS, comfy.samplers.KSampler.SCHEDULERS,)
    RETURN_NAMES = ("img2img_strength", "inpaint_strength", "inpaint_grow_mask", "unsampler_strength", "unsampler_cfg", "unsampler_sampler", "unsampler_scheduler",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,img2img_settings):
        
        img2img_strength, inpaint_strength, inpaint_grow_mask, unsampler_strength, unsampler_cfg, unsampler_sampler, unsampler_scheduler = img2img_settings

        return(img2img_strength, inpaint_strength, inpaint_grow_mask, unsampler_strength, unsampler_cfg, unsampler_sampler, unsampler_scheduler,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_CannyEdge_Settings:
    cannyedgefrom = ["Source Image", "Support Image", "Support Direct"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cannyedge_from": (s.cannyedgefrom,),
                "cannyedge_strength": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 10.00, "step": 0.10}),
                "cannyedge_start": ("FLOAT", {"default": 0.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "cannyedge_end": ("FLOAT", {"default": 1.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "cannyedge_low": ("INT", {"default": 100, "min": 0, "max": 255, "step": 1}),
                "cannyedge_high": ("INT", {"default": 200, "min": 0, "max": 255, "step": 1}),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("cannyedge_settings",)
    FUNCTION = "get_ctrlnet_cannyedge"

    CATEGORY="JPS Nodes/Settings"

    def get_ctrlnet_cannyedge(self, cannyedge_from, cannyedge_strength, cannyedge_start, cannyedge_end, cannyedge_low, cannyedge_high):

        cannyedge_source = int (1)
        if (cannyedge_from == "Support Image"):
            cannyedge_source = int(2)
        if (cannyedge_from == "Support Direct"):
            cannyedge_source = int(3)
        
        cannyedge_settings = cannyedge_source, cannyedge_strength, cannyedge_start, cannyedge_end, cannyedge_low, cannyedge_high

        return(cannyedge_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_CannyEdge_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "cannyedge_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "FLOAT", "INT", "INT", )
    RETURN_NAMES = ("cannyedge_source", "cannyedge_strength", "cannyedge_start", "cannyedge_end", "cannyedge_low", "cannyedge_high",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,cannyedge_settings):
        
        cannyedge_source, cannyedge_strength, cannyedge_start, cannyedge_end, cannyedge_low, cannyedge_high = cannyedge_settings

        return(cannyedge_source, cannyedge_strength, cannyedge_start, cannyedge_end, cannyedge_low, cannyedge_high,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_OpenPose_Settings:
    openposefrom = ["Source Image", "Support Image", "Support Direct"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "openpose_from": (s.openposefrom,),
                "openpose_strength": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 10.00, "step": 0.10}),
                "openpose_start": ("FLOAT", {"default": 0.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "openpose_end": ("FLOAT", {"default": 1.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "openpose_body": (["enable","disable"],),
                "openpose_face": (["enable","disable"],),
                "openpose_hand": (["enable","disable"],),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("openpose_settings",)
    FUNCTION = "get_ctrlnet_openpose"

    CATEGORY="JPS Nodes/Settings"

    def get_ctrlnet_openpose(self, openpose_from, openpose_strength, openpose_start, openpose_end, openpose_body, openpose_face, openpose_hand):

        openpose_source = int (1)
        if (openpose_from == "Support Image"):
            openpose_source = int(2)
        if (openpose_from == "Support Direct"):
            openpose_source = int(3)
        
        openpose_settings = openpose_source, openpose_strength, openpose_start, openpose_end, openpose_body, openpose_face, openpose_hand

        return(openpose_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_OpenPose_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "openpose_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "FLOAT", ["enable","disable"], ["enable","disable"], ["enable","disable"],)
    RETURN_NAMES = ("openpose_source", "openpose_strength", "openpose_start", "openpose_end", "openpose_body", "openpose_face", "openpose_hand",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,openpose_settings):
        
        openpose_source, openpose_strength, openpose_start, openpose_end, openpose_body, openpose_face, openpose_hand = openpose_settings

        return(openpose_source, openpose_strength, openpose_start, openpose_end, openpose_body, openpose_face, openpose_hand,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_MiDaS_Settings:
    midasfrom = ["Source Image", "Support Image", "Support Direct"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "midas_from": (s.midasfrom,),
                "midas_strength": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 10.00, "step": 0.10}),
                "midas_start": ("FLOAT", {"default": 0.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "midas_end": ("FLOAT", {"default": 1.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "midas_a": ("FLOAT", {"default": 6.28, "min": 0.00, "max": 15.71, "step": 0.05}),
                "midas_bg": ("FLOAT", {"default": 0.10, "min": 0.00, "max": 1.00, "step": 0.05}),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("midas_settings",)
    FUNCTION = "get_ctrlnet_midas"

    CATEGORY="JPS Nodes/Settings"

    def get_ctrlnet_midas(self, midas_from, midas_strength, midas_start, midas_end, midas_a, midas_bg):

        midas_source = int (1)
        if (midas_from == "Support Image"):
            midas_source = int(2)
        if (midas_from == "Support Direct"):
            midas_source = int(3)
        
        midas_settings = midas_source, midas_strength, midas_start, midas_end, midas_a, midas_bg

        return(midas_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_MiDaS_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "midas_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT",)
    RETURN_NAMES = ("midas_source", "midas_strength", "midas_start", "midas_end", "midas_a", "midas_bg",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,midas_settings):
        
        midas_source, midas_strength, midas_start, midas_end, midas_a, midas_bg = midas_settings

        return(midas_source, midas_strength, midas_start, midas_end, midas_a, midas_bg,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_ZoeDepth_Settings:
    zoefrom = ["Source Image", "Support Image", "Support Direct"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "zoe_from": (s.zoefrom,),
                "zoe_strength": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 10.00, "step": 0.10}),
                "zoe_start": ("FLOAT", {"default": 0.000, "min": 0.000, "max": 1.000, "step": 0.05}),
                "zoe_end": ("FLOAT", {"default": 1.000, "min": 0.000, "max": 1.000, "step": 0.05}),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("zoedepth_settings",)
    FUNCTION = "get_ctrlnet_zoedepth"

    CATEGORY="JPS Nodes/Settings"

    def get_ctrlnet_zoedepth(self, zoe_from, zoe_strength, zoe_start, zoe_end):

        zoe_source = int (1)
        if (zoe_from == "Support Image"):
            zoe_source = int(2)
        if (zoe_from == "Support Direct"):
            zoe_source = int(3)
        
        zoedepth_settings = zoe_source, zoe_strength, zoe_start, zoe_end

        return(zoedepth_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class CtrlNet_ZoeDepth_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "zoedepth_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "FLOAT",)
    RETURN_NAMES = ("zoe_source", "zoe_strength", "zoe_start", "zoe_end",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,zoedepth_settings):
        
        zoe_source, zoe_strength, zoe_start, zoe_end = zoedepth_settings

        return(zoe_source, zoe_strength, zoe_start, zoe_end,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class IP_Adapter_Settings:
    ipaweight = ["Use IP Adapter #1 weight for all","Use separate IP Adapter weights"]
    ipawtype = ["Use IP Adapter #1 wtype for all","Use separate IP Adapter wtypes"]
    ipanoise = ["Use IP Adapter #1 noise for all","Use separate IP Adapter noises"]
    ipamasktype = ["No Mask","Mask Editor","Mask Editor (inverted)","Red from Image","Green from Image","Blue from Image"]    

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ipa_weight": (s.ipaweight,),
                "ipa_wtype": (s.ipawtype,),
                "ipa_noise": (s.ipanoise,),

                "ipa1_weight": ("FLOAT", {"default": 0.5, "min": 0, "max": 3, "step": 0.01}),
                "ipa1_wtype": (["original", "linear", "channel penalty"],),
                "ipa1_noise": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
                "ipa1_start": ("FLOAT", {"default": 0.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa1_stop": ("FLOAT", {"default": 1.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa1_crop": (["center","top", "bottom", "left", "right"],),
                "ipa1_offset": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "ipa1_mask": (s.ipamasktype,),

                "ipa2_weight": ("FLOAT", {"default": 0.5, "min": 0, "max": 3, "step": 0.01}),
                "ipa2_wtype": (["original", "linear", "channel penalty"],),
                "ipa2_noise": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
                "ipa2_start": ("FLOAT", {"default": 0.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa2_stop": ("FLOAT", {"default": 1.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa2_crop": (["center","top", "bottom", "left", "right"],),
                "ipa2_offset": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "ipa2_mask": (s.ipamasktype,),


                "ipa3_weight": ("FLOAT", {"default": 0.5, "min": 0, "max": 3, "step": 0.01}),
                "ipa3_wtype": (["original", "linear", "channel penalty"],),
                "ipa3_noise": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
                "ipa3_start": ("FLOAT", {"default": 0.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa3_stop": ("FLOAT", {"default": 1.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa3_crop": (["center","top", "bottom", "left", "right"],),
                "ipa3_offset": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "ipa3_mask": (s.ipamasktype,),


                "ipa4_weight": ("FLOAT", {"default": 0.5, "min": 0, "max": 3, "step": 0.01}),
                "ipa4_wtype": (["original", "linear", "channel penalty"],),
                "ipa4_noise": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
                "ipa4_start": ("FLOAT", {"default": 0.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa4_stop": ("FLOAT", {"default": 1.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa4_crop": (["center","top", "bottom", "left", "right"],),
                "ipa4_offset": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "ipa4_mask": (s.ipamasktype,),

                "crop_intpol": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),
                "crop_res": ("INT", { "default": 224 , "min": 224, "max": 1792, "step": 224, "display": "number" }),
            }
        }
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("ip_adapter_settings",)
    FUNCTION = "get_ipamode"

    CATEGORY="JPS Nodes/Settings"

    def get_ipamode(self,crop_res,crop_intpol,ipa1_crop,ipa1_offset,ipa2_crop,ipa2_offset,ipa3_crop,ipa3_offset,ipa4_crop,ipa4_offset,ipa_weight,ipa_wtype,ipa1_weight,ipa1_wtype,ipa2_weight,ipa2_wtype,ipa3_weight,ipa3_wtype,ipa4_weight,ipa4_wtype,ipa_noise,ipa1_noise,ipa2_noise,ipa3_noise,ipa4_noise,ipa1_start,ipa1_stop,ipa2_start,ipa2_stop,ipa3_start,ipa3_stop,ipa4_start,ipa4_stop,ipa1_mask,ipa2_mask,ipa3_mask,ipa4_mask):
        if(ipa_weight == "Use IP Adapter #1 weight for all"):
            ipa2_weight = ipa1_weight
            ipa3_weight = ipa1_weight
            ipa4_weight = ipa1_weight
        if(ipa_wtype == "Use IP Adapter #1 wtype for all"):
            ipa2_wtype = ipa1_wtype
            ipa3_wtype = ipa1_wtype
            ipa4_wtype = ipa1_wtype
        if(ipa_noise == "Use IP Adapter #1 noise for all"):
            ipa2_noise = ipa1_noise
            ipa3_noise = ipa1_noise
            ipa4_noise = ipa1_noise

        ipa1mask = int(0)
        if(ipa1_mask == "Mask Editor"):
            ipa1mask = int(1)
        elif(ipa1_mask == "Mask Editor (inverted)"):
            ipa1mask = int(2)
        elif(ipa1_mask == "Red from Image"):
            ipa1mask = int(3)
        elif(ipa1_mask == "Green from Image"):
            ipa1mask = int(4)
        elif(ipa1_mask == "Blue from Image"):
            ipa1mask = int(5)

        ipa2mask = int(0)
        if(ipa2_mask == "Mask Editor"):
            ipa2mask = int(1)
        elif(ipa2_mask == "Mask Editor (inverted)"):
            ipa2mask = int(2)
        elif(ipa2_mask == "Red from Image"):
            ipa2mask = int(3)
        elif(ipa2_mask == "Green from Image"):
            ipa2mask = int(4)
        elif(ipa2_mask == "Blue from Image"):
            ipa2mask = int(5)

        ipa3mask = int(0)
        if(ipa3_mask == "Mask Editor"):
            ipa3mask = int(1)
        elif(ipa3_mask == "Mask Editor (inverted)"):
            ipa3mask = int(2)
        elif(ipa3_mask == "Red from Image"):
            ipa3mask = int(3)
        elif(ipa3_mask == "Green from Image"):
            ipa3mask = int(4)
        elif(ipa3_mask == "Blue from Image"):
            ipa3mask = int(5)

        ipa4mask = int(0)
        if(ipa4_mask == "Mask Editor"):
            ipa4mask = int(1)
        elif(ipa4_mask == "Mask Editor (inverted)"):
            ipa4mask = int(2)
        elif(ipa4_mask == "Red from Image"):
            ipa4mask = int(3)
        elif(ipa4_mask == "Green from Image"):
            ipa4mask = int(4)
        elif(ipa4_mask == "Blue from Image"):
            ipa4mask = int(5)

        ipa1weight = ipa1_weight
        ipa1wtype = ipa1_wtype
        ipa1noise = ipa1_noise
        ipa2weight = ipa2_weight
        ipa2wtype = ipa2_wtype        
        ipa2noise = ipa2_noise
        ipa3weight = ipa3_weight
        ipa3wtype = ipa3_wtype
        ipa3noise = ipa3_noise
        ipa4weight = ipa4_weight
        ipa4wtype = ipa4_wtype
        ipa4noise = ipa4_noise


        ip_adapter_settings = crop_res,crop_intpol,ipa1_crop,ipa1_offset,ipa2_crop,ipa2_offset,ipa3_crop,ipa3_offset,ipa4_crop,ipa4_offset,ipa1weight,ipa1wtype,ipa2weight,ipa2wtype,ipa3weight,ipa3wtype,ipa4weight,ipa4wtype,ipa1noise,ipa2noise,ipa3noise,ipa4noise,ipa1_start,ipa1_stop,ipa2_start,ipa2_stop,ipa3_start,ipa3_stop,ipa4_start,ipa4_stop,ipa1mask,ipa2mask,ipa3mask,ipa4mask

        return(ip_adapter_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#
    
class IP_Adapter_Single_Settings:
    ipamasktype = ["No Mask","Mask Editor","Mask Editor (inverted)","Red from Image","Green from Image","Blue from Image"]    

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ipa_weight": ("FLOAT", {"default": 0.5, "min": 0, "max": 3, "step": 0.01}),
                "ipa_wtype": (["original", "linear", "channel penalty"],),
                "ipa_noise": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
                "ipa_start": ("FLOAT", {"default": 0.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa_stop": ("FLOAT", {"default": 1.00, "min": 0, "max": 1, "step": 0.05}),
                "ipa_crop": (["center","top", "bottom", "left", "right"],),
                "ipa_zoom": ("FLOAT", { "default": 1, "min": 1, "max": 5, "step": 0.1, "display": "number" }),
                "ipa_offset_x": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "ipa_offset_y": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),                
                "ipa_mask": (s.ipamasktype,),
                "crop_intpol": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),
                "sharpening": ("FLOAT", { "default": 0.0, "min": 0, "max": 1, "step": 0.05, "display": "number" }),
                "ipa_model": (["SDXL ViT-H", "SDXL Plus ViT-H", "SDXL Plus Face ViT-H"],),
            }
        }
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("ip_adapter_single_settings",)
    FUNCTION = "get_ipamodesingle"

    CATEGORY="JPS Nodes/Settings"

    def get_ipamodesingle(self,ipa_weight,ipa_wtype,ipa_noise,ipa_start,ipa_stop,ipa_crop,ipa_zoom,ipa_offset_x,ipa_offset_y,ipa_mask,crop_intpol,sharpening,ipa_model):

        ipamask = int(0)
        if(ipa_mask == "Mask Editor"):
            ipamask = int(1)
        elif(ipa_mask == "Mask Editor (inverted)"):
            ipamask = int(2)
        elif(ipa_mask == "Red from Image"):
            ipamask = int(3)
        elif(ipa_mask == "Green from Image"):
            ipamask = int(4)
        elif(ipa_mask == "Blue from Image"):
            ipamask = int(5)

        ipamodel = int (0)
        if(ipa_model == "SDXL ViT-H"):
            ipamodel = int(1)
        elif(ipa_model == "SDXL Plus ViT-H"):
            ipamodel = int(2)
        elif(ipa_model == "SDXL Plus Face ViT-H"):
            ipamodel = int(3)

        ipaweight = ipa_weight
        ipawtype = ipa_wtype
        ipanoise = ipa_noise
        ipastart = ipa_start
        ipastop = ipa_stop
        ipacrop = ipa_crop
        ipazoom = ipa_zoom
        ipaoffsetx = ipa_offset_x
        ipaoffsety = ipa_offset_y
        cropintpol = crop_intpol
        
        ip_adapter_settings = ipaweight,ipawtype,ipanoise,ipastart,ipastop,ipacrop,ipazoom,ipaoffsetx,ipaoffsety,ipamask,cropintpol,sharpening,ipamodel

        return(ip_adapter_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

class IP_Adapter_Settings_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ip_adapter_settings": ("BASIC_PIPE",),
            }
        }
    RETURN_TYPES = ("INT",["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],["center","top", "bottom", "left", "right"],"INT",["center","top", "bottom", "left", "right"],"INT",["center","top", "bottom", "left", "right"],"INT",["center","top", "bottom", "left", "right"],"INT","FLOAT",["original", "linear", "channel penalty"],"FLOAT",["original", "linear", "channel penalty"],"FLOAT",["original", "linear", "channel penalty"],"FLOAT",["original", "linear", "channel penalty"],"FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","FLOAT","INT","INT","INT","INT")
    RETURN_NAMES = ("crop_res", "crop_intpol", "ipa1_crop", "ipa1_offset", "ipa2_crop", "ipa2_offset", "ipa3_crop", "ipa3_offset", "ipa4_crop", "ipa4_offset", "ipa1_weight", "ipa1_wtype", "ipa2_weight", "ipa2_wtype", "ipa3_weight", "ipa3_wtype", "ipa4_weight", "ipa4_wtype", "ipa1_noise", "ipa2_noise", "ipa3_noise", "ipa4_noise", "ipa1_start", "ipa1_stop", "ipa2_start", "ipa2_stop", "ipa3_start", "ipa3_stop", "ipa4_start", "ipa4_stop","ipa1_mask","ipa2_mask","ipa3_mask","ipa4_mask")
    FUNCTION = "get_ipamode"

    CATEGORY="JPS Nodes/Pipes"

    def get_ipamode(self,ip_adapter_settings):

        crop_res,crop_intpol,ipa1_crop,ipa1_offset,ipa2_crop,ipa2_offset,ipa3_crop,ipa3_offset,ipa4_crop,ipa4_offset,ipa1weight,ipa1wtype,ipa2weight,ipa2wtype,ipa3weight,ipa3wtype,ipa4weight,ipa4wtype,ipa1noise,ipa2noise,ipa3noise,ipa4noise,ipa1_start,ipa1_stop,ipa2_start,ipa2_stop,ipa3_start,ipa3_stop,ipa4_start,ipa4_stop,ipa1mask,ipa2mask,ipa3mask,ipa4mask = ip_adapter_settings

        return(int(crop_res),crop_intpol,ipa1_crop,int(ipa1_offset),ipa2_crop,int(ipa2_offset),ipa3_crop,int(ipa3_offset),ipa4_crop,int(ipa4_offset),float(ipa1weight),ipa1wtype,float(ipa2weight),ipa2wtype,float(ipa3weight),ipa3wtype,float(ipa4weight),ipa4wtype,float(ipa1noise),float(ipa2noise),float(ipa3noise),float(ipa4noise),float(ipa1_start),float(ipa1_stop),float(ipa2_start),float(ipa2_stop),float(ipa3_start),float(ipa3_stop),float(ipa4_start),float(ipa4_stop),int(ipa1mask),int(ipa2mask),int(ipa3mask),int(ipa4mask),)

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

class IP_Adapter_Single_Settings_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ip_adapter_settings": ("BASIC_PIPE",),
            }
        }
    RETURN_TYPES = ("FLOAT",["original", "linear", "channel penalty"],"FLOAT","FLOAT","FLOAT",["center","top", "bottom", "left", "right"],"FLOAT","INT","INT","INT",["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],"FLOAT","INT")
    RETURN_NAMES = ("ipa_weight","ipa_wtype","ipa_noise","ipa_start","ipa_stop","ipa_crop","ipa_zoom","ipa_offset_x","ipa_offset_y","ipa_mask","crop_intpol","sharpening","ipa_model")
    FUNCTION = "get_ipamode_single"

    CATEGORY="JPS Nodes/Pipes"

    def get_ipamode_single(self,ip_adapter_settings):

        ipaweight,ipawtype,ipanoise,ipastart,ipastop,ipacrop,ipazoom,ipaoffsetx,ipaoffsety,ipamask,cropintpol,sharpening,ipamodel = ip_adapter_settings

        return(float(ipaweight),ipawtype,float(ipanoise),float(ipastart),float(ipastop),ipacrop,float(ipazoom),int(ipaoffsetx),int(ipaoffsety),int(ipamask),cropintpol,float(sharpening),int(ipamodel),)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Revision_Settings:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "rev1_strength": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),
                "rev2_strength": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),

                "rev1_noiseaug": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),
                "rev2_noiseaug": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),

                "rev1_crop": (["center","top", "bottom", "left", "right"],),
                "rev1_offset": ("INT", { "default": 0, "min": -2048, "max": 2048, "step": 1, "display": "number" }),

                "rev2_crop": (["center","top", "bottom", "left", "right"],),
                "rev2_offset": ("INT", { "default": 0, "min": -2048, "max": 2048, "step": 1, "display": "number" }),                

                "crop_intpol": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),                
                "crop_res": ("INT", { "default": 224 , "min": 224, "max": 1792, "step": 224, "display": "number" }),
            }
        }
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("revision_settings",)
    FUNCTION = "get_revmode"

    CATEGORY="JPS Nodes/Settings"

    def get_revmode(self,crop_res,crop_intpol,rev1_crop,rev1_offset,rev2_crop,rev2_offset,rev1_strength,rev2_strength,rev1_noiseaug,rev2_noiseaug,):
        rev1strength = 0
        rev1noiseaug = 0 
        rev2strength = 0
        rev2noiseaug = 0 
 
        rev1strength = rev1_strength
        rev1noiseaug = rev1_noiseaug
        rev2strength = rev2_strength
        rev2noiseaug = rev2_noiseaug

        revision_settings = crop_res,crop_intpol,rev1_crop,rev1_offset,rev2_crop,rev2_offset,rev1strength,rev2strength,rev1noiseaug,rev2_noiseaug

        return(revision_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Revision_Settings_Pipe:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "revision_settings": ("BASIC_PIPE",),
            }
        }
    RETURN_TYPES = ("INT",["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],["center","top", "bottom", "left", "right"],"INT",["center","top", "bottom", "left", "right"],"INT","FLOAT","FLOAT","FLOAT","FLOAT",)
    RETURN_NAMES = ("crop_res", "crop_intpol", "rev1_crop", "rev1_offset", "rev2_crop", "rev2_offset", "rev1_strength", "rev2_strength", "rev1_noiseaug", "rev2_noiseaug",)
    FUNCTION = "get_revmode"

    CATEGORY="JPS Nodes/Pipes"

    def get_revmode(self,revision_settings):

        crop_res,crop_intpol,rev1_crop,rev1_offset,rev2_crop,rev2_offset,rev1strength,rev2strength,rev1noiseaug,rev2noiseaug = revision_settings

        return(int(crop_res),crop_intpol,rev1_crop,int(rev1_offset),rev2_crop,int(rev2_offset),float(rev1strength),float(rev2strength),float(rev1noiseaug),float(rev2noiseaug),)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Sampler_Scheduler_Settings:
    CATEGORY = 'JPS Nodes/Settings'
    RETURN_TYPES = (comfy.samplers.KSampler.SAMPLERS,comfy.samplers.KSampler.SCHEDULERS,)
    RETURN_NAMES = ("sampler_name","scheduler",)
    FUNCTION = "get_samsched"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"sampler_name": (comfy.samplers.KSampler.SAMPLERS,),"scheduler": (comfy.samplers.KSampler.SCHEDULERS,)}}

    def get_samsched(self, sampler_name, scheduler):
        return (sampler_name, scheduler, )
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Image_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("img_out",)
    FUNCTION = "get_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "img_1": ("IMAGE",),
                "img_2": ("IMAGE",),
                "img_3": ("IMAGE",),
                "img_4": ("IMAGE",),
                "img_5": ("IMAGE",),
            }
        }

    def get_image(self,select,img_1,img_2=None,img_3=None,img_4=None,img_5=None,):
        
        img_out = img_1

        if (select == 2):
            img_out = img_2
        elif (select == 3):
            img_out  = img_3
        elif (select == 4):
            img_out = img_4
        elif (select == 5):
            img_out = img_5

        return (img_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Conditioning_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("con_out",)
    FUNCTION = "get_con"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "con_1": ("CONDITIONING",),
                "con_2": ("CONDITIONING",),
                "con_3": ("CONDITIONING",),
                "con_4": ("CONDITIONING",),
                "con_5": ("CONDITIONING",),
            }
        }

    def get_con(self,select,con_1,con_2=None,con_3=None,con_4=None,con_5=None,):
        
        con_out = con_1

        if (select == 2):
            con_out = con_2
        elif (select == 3):
            con_out  = con_3
        elif (select == 4):
            con_out = con_4
        elif (select == 5):
            con_out = con_5

        return (con_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Model_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model_out",)
    FUNCTION = "get_model"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "model_1": ("MODEL",),
                "model_2": ("MODEL",),
                "model_3": ("MODEL",),
                "model_4": ("MODEL",),
                "model_5": ("MODEL",),
            }
        }

    def get_model(self,select,model_1,model_2=None,model_3=None,model_4=None,model_5=None,):
        
        model_out = model_1

        if (select == 2):
            model_out = model_2
        elif (select == 3):
            model_out  = model_3
        elif (select == 4):
            model_out = model_4
        elif (select == 5):
            model_out = model_5

        return (model_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class IPA_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("IPADAPTER",)
    RETURN_NAMES = ("IPA_out",)
    FUNCTION = "get_ipa"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "ipa_1": ("IPADAPTER",),
                "ipa_2": ("IPADAPTER",),
                "ipa_3": ("IPADAPTER",),
                "ipa_4": ("IPADAPTER",),
                "ipa_5": ("IPADAPTER",),
            }
        }

    def get_ipa(self,select,ipa_1,ipa_2=None,ipa_3=None,ipa_4=None,ipa_5=None,):
        
        ipa_out = ipa_1

        if (select == 2):
            ipa_out = ipa_2
        elif (select == 3):
            ipa_out  = ipa_3
        elif (select == 4):
            ipa_out = ipa_4
        elif (select == 5):
            ipa_out = ipa_5

        return (ipa_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Latent_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent_out",)
    FUNCTION = "get_latent"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "latent_1": ("LATENT",),
                "latent_2": ("LATENT",),
                "latent_3": ("LATENT",),
                "latent_4": ("LATENT",),
                "latent_5": ("LATENT",),
            }
        }

    def get_latent(self,select,latent_1=None,latent_2=None,latent_3=None,latent_4=None,latent_5=None,):
        
        latent_out = latent_1

        if (select == 2):
            latent_out = latent_2
        elif (select == 3):
            latent_out = latent_3
        elif (select == 4):
            latent_out = latent_4
        elif (select == 5):
            latent_out = latent_5

        return (latent_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class VAE_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("VAE",)
    RETURN_NAMES = ("vae_out",)
    FUNCTION = "get_vae"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "vae_1": ("VAE",),
                "vae_2": ("VAE",),
                "vae_3": ("VAE",),
                "vae_4": ("VAE",),
                "vae_5": ("VAE",),
            }
        }

    def get_vae(self,select,vae_1=None,vae_2=None,vae_3=None,vae_4=None,vae_5=None,):
        
        vae_out = vae_1

        if (select == 2):
            vae_out = vae_2
        elif (select == 3):
            vae_out = vae_3
        elif (select == 4):
            vae_out = vae_4
        elif (select == 5):
            vae_out = vae_5

        return (vae_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Integer_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("int_out",)
    FUNCTION = "get_int"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "int_1": ("INT", {}),
                "int_2": ("INT", {}),
                "int_3": ("INT", {}),
                "int_4": ("INT", {}),
                "int_5": ("INT", {}),
            }
        }

    def get_int(self,select,int_1=None,int_2=None,int_3=None,int_4=None,int_5=None,):
        
        int_out = int_1

        if (select == 2):
            int_out = int_2
        elif (select == 3):
            int_out = int_3
        elif (select == 4):
            int_out = int_4
        elif (select == 5):
            int_out = int_5

        return (int_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Mask_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask_out",)
    FUNCTION = "get_mask"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "mask_1": ("MASK",),
                "mask_2": ("MASK",),
                "mask_3": ("MASK",),
                "mask_4": ("MASK",),
                "mask_5": ("MASK",),
            }
        }

    def get_mask(self,select,mask_1=None,mask_2=None,mask_3=None,mask_4=None,mask_5=None,):
        
        mask_out = None

        if (select == 1):
            mask_out = mask_1
        if (select == 2):
            mask_out = mask_2
        elif (select == 3):
            mask_out = mask_3
        elif (select == 4):
            mask_out = mask_4
        elif (select == 5):
            mask_out = mask_5

        return (mask_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class ControlNet_Switch:

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = ("CONTROL_NET",)
    RETURN_NAMES = ("ctrlnet_out",)
    FUNCTION = "get_ctrlnet"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {}),
            },
            "optional": {
                "ctrlnet_1": ("CONTROL_NET",),
                "ctrlnet_2": ("CONTROL_NET",),
                "ctrlnet_3": ("CONTROL_NET",),
                "ctrlnet_4": ("CONTROL_NET",),
                "ctrlnet_5": ("CONTROL_NET",),
            }
        }

    def get_ctrlnet(self,select,ctrlnet_1=None,ctrlnet_2=None,ctrlnet_3=None,ctrlnet_4=None,ctrlnet_5=None,):
        
        ctrlnet_out = ctrlnet_1

        if (select == 2):
            ctrlnet_out = ctrlnet_2
        elif (select == 3):
            ctrlnet_out = ctrlnet_3
        elif (select == 4):
            ctrlnet_out = ctrlnet_4
        elif (select == 5):
            ctrlnet_out = ctrlnet_5

        return (ctrlnet_out,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Fundamentals_MultiPipe:

    CATEGORY = 'JPS Nodes/Pipes'
    RETURN_TYPES = ("VAE","MODEL","MODEL","CLIP","CLIP","CONDITIONING","CONDITIONING","CONDITIONING","CONDITIONING","INT",)
    RETURN_NAMES = ("vae","model_base","model_refiner","clip_base","clip_refiner","pos_base","neg_base","pos_refiner","neg_refiner","seed",)
    FUNCTION = "get_sdxlfund"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "vae": ("VAE",),
                "model_base": ("MODEL",),
                "model_refiner": ("MODEL",),
                "clip_base": ("CLIP",),
                "clip_refiner": ("CLIP",),
                "pos_base": ("CONDITIONING",), 
                "neg_base": ("CONDITIONING",),
                "pos_refiner": ("CONDITIONING",),
                "neg_refiner": ("CONDITIONING",),
                "seed": ("INT", {}),
            }
        }

    def get_sdxlfund(self,vae=None,model_base=None,model_refiner=None,clip_base=None,clip_refiner=None,pos_base=None,neg_base=None,pos_refiner=None,neg_refiner=None,seed=None):
        
        return (vae,model_base,model_refiner,clip_base,clip_refiner,pos_base,neg_base,pos_refiner,neg_refiner,seed,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Images_Masks_MultiPipe:

    CATEGORY = 'JPS Nodes/Pipes'
    RETURN_TYPES = ("IMAGE","MASK","IMAGE","IMAGE","MASK","MASK","IMAGE","IMAGE","MODEL",)
    RETURN_NAMES = ("generation_img","generation_mask","ipa1_img","ipa2_img","ipa1_mask","ipa2_mask","revision1_img","revision2_img","inpaint_model",)
    FUNCTION = "get_imagemask"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "generation_img": ("IMAGE",),
                "generation_mask": ("MASK",),
                "ipa1_img": ("IMAGE",),
                "ipa2_img": ("IMAGE",),
                "ipa1_mask": ("MASK",),
                "ipa2_mask": ("MASK",),
                "revision1_img": ("IMAGE",),
                "revision2_img": ("IMAGE",),
                "inpaint_model": ("MODEL",),
            }
        }

    def get_imagemask(self,generation_img=None,generation_mask=None,ipa1_img=None,ipa2_img=None,ipa1_mask=None,ipa2_mask=None,revision1_img=None,revision2_img=None,inpaint_model=None,):
        
        return (generation_img,generation_mask,ipa1_img,ipa2_img,ipa1_mask,ipa2_mask,revision1_img,revision2_img,inpaint_model,)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Disable_Enable_Switch:
    match = ["Set to Disable","Set to Enable"]

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = (["disable","enable"],)
    RETURN_NAMES = ("disable_enable",)
    FUNCTION = "get_disenable"

    @classmethod
    def INPUT_TYPES(s):    
        return {
            "required": {
                "select": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),
                "compare": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),
                "match": (s.match,),
            }
        }

    def get_disenable(self,select,compare,match):
        disable_enable = "disable"
        if match == "Set to Enable" and (int(select) == int(compare)):
            disable_enable = "enable"
        elif match == "Set to Disable" and (int(select) == int(compare)):
            disable_enable = "disable"
        elif match == "Set to Enable" and (int(select) != int(compare)):
            disable_enable = "disable"
        elif match == "Set to Disable" and (int(select) != int(compare)):
            disable_enable = "enable"
        
        return (disable_enable, )
            
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Enable_Disable_Switch:
    match = ["Set to Enable","Set to Disable"]

    CATEGORY = 'JPS Nodes/Switches'
    RETURN_TYPES = (["enable","disable"],)
    RETURN_NAMES = ("enable_disable",)
    FUNCTION = "get_endisable"

    @classmethod
    def INPUT_TYPES(s):    
        return {
            "required": {
                "select": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),
                "compare": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),
                "match": (s.match,),
            }
        }

    def get_endisable(self,select,compare,match):
        enable_disable = "disable"
        if match == "Set to Enable" and (int(select) == int(compare)):
            enable_disable = "enable"
        elif match == "Set to Disable" and (int(select) == int(compare)):
            enable_disable = "disable"
        elif match == "Set to Enable" and (int(select) != int(compare)):
            enable_disable = "disable"
        elif match == "Set to Disable" and (int(select) != int(compare)):
            enable_disable = "enable"
        
        return (enable_disable, )
            
#---------------------------------------------------------------------------------------------------------------------------------------------------#
       
class IO_Lora_Loader:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        file_list = folder_paths.get_filename_list("loras")
        file_list.insert(0, "None")
        return {"required": { "model": ("MODEL",),
                              "clip": ("CLIP", ),
                              "switch": ([
                                "Off",
                                "On"],),
                              "lora_name": (file_list, ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                              "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                              }}
    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_lora"

    CATEGORY = "JPS Nodes/IO"

    def load_lora(self, model, clip, switch, lora_name, strength_model, strength_clip):
        if strength_model == 0 and strength_clip == 0:
            return (model, clip)

        if switch == "Off" or  lora_name == "None":
            return (model, clip)

        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                del self.loaded_lora

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return (model_lora, clip_lora)

#---------------------------------------------------------------------------------------------------------------------------------------------------#                       

class Get_Image_Size:
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("INT", "INT",)
    RETURN_NAMES = ("width", "height",)
    CATEGORY = "JPS Nodes/Image"

    FUNCTION = 'get_imagesize'

    def get_imagesize(self, image):
        samples = image.movedim(-1,1)
        size_w = samples.shape[3]
        size_h = samples.shape[2]

        return (size_w, size_h, )

#---------------------------------------------------------------------------------------------------------------------------------------------------#                       

class SDXL_Prompt_Styler:

    def __init__(self):
        pass

    uni_neg = ["OFF","ON"]

    @classmethod
    def INPUT_TYPES(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        self.json_data_artists, artists = load_styles_from_directory(os.path.join(current_directory, 'styles', 'artists'))
        self.json_data_movies, movies = load_styles_from_directory(os.path.join(current_directory, 'styles', 'movies'))
        self.json_data_styles, styles = load_styles_from_directory(os.path.join(current_directory, 'styles', 'main'))
        
        return {
            "required": {
                "text_positive_g": ("STRING", {"default": "", "multiline": True}),
                "text_positive_l": ("STRING", {"default": "", "multiline": True}),
                "text_negative": ("STRING", {"default": "", "multiline": True}),
                "artist": ((artists), ),
                "movie": ((movies), ),
                "style": ((styles), ),
                "universal_neg": (self.uni_neg,),
            },
        }

    RETURN_TYPES = ('STRING','STRING','STRING','STRING',)
    RETURN_NAMES = ('text_positive_g','text_positive_l','text_positive','text_negative',)
    FUNCTION = 'sdxlpromptstyler'
    CATEGORY = 'JPS Nodes/Style'

    def sdxlpromptstyler(self, text_positive_g, text_positive_l, text_negative, artist, movie, style,universal_neg):
        # Process and combine prompts in templates
        # The function replaces the positive prompt placeholder in the template,
        # and combines the negative prompt with the template's negative prompt, if they exist.

        text_pos_g_style = ""
        text_pos_l_style = ""
        text_pos_style = ""
        text_neg_style = ""

        text_pos_g_artist, text_pos_l_artist, text_neg_artist = read_sdxl_templates_replace_and_combine(self.json_data_artists, artist, text_positive_g, text_positive_l, text_negative)

        if(text_positive_g == text_positive_l):
            if(text_pos_l_artist != text_positive_l and text_pos_g_artist != text_positive_g):
                text_positive_l = ""
                text_pos_g_artist, text_pos_l_artist, text_neg_artist = read_sdxl_templates_replace_and_combine(self.json_data_artist, artist, text_positive_g, text_positive_l, text_negative) 
            elif(text_pos_g_artist != text_positive_g):
                text_pos_l_artist = text_pos_g_artist
            elif(text_pos_l_artist != text_positive_l):
                text_pos_g_artist = text_pos_l_artist

        text_pos_g_movie, text_pos_l_movie, text_neg_movie = read_sdxl_templates_replace_and_combine(self.json_data_movies, movie, text_pos_g_artist, text_pos_l_artist, text_negative)

        if(text_pos_g_artist == text_pos_l_artist):
            if(text_pos_l_movie != text_pos_l_artist and text_pos_g_movie != text_pos_g_artist):
                text_pos_l_artist = ""
                text_pos_g_movie, text_pos_l_movie, text_neg_movie = read_sdxl_templates_replace_and_combine(self.json_data_movie, movie, text_positive_g, text_positive_l, text_negative) 
            elif(text_pos_g_movie != text_pos_g_artist):
                text_pos_l_movie = text_pos_g_movie
            elif(text_pos_l_movie != text_pos_l_artist):
                text_pos_g_movie = text_pos_l_movie

        text_pos_g_style, text_pos_l_style, text_neg_style = read_sdxl_templates_replace_and_combine(self.json_data_styles, style, text_pos_g_movie, text_pos_l_movie, text_neg_movie)

        if(text_pos_g_movie == text_pos_l_movie):
            if(text_pos_l_movie != text_pos_l_style and text_pos_g_movie != text_pos_g_style):
                text_pos_l_movie = ""
                text_pos_g_style, text_pos_l_style, text_neg_style = read_sdxl_templates_replace_and_combine(self.json_data_styles, style, text_pos_g_movie, text_pos_l_movie, text_neg_movie) 
            elif(text_pos_g_movie != text_pos_g_style):
                text_pos_l_style = text_pos_g_style
            elif(text_pos_l_movie != text_pos_l_style):
                text_pos_g_style = text_pos_l_style

        if(text_pos_g_style != text_pos_l_style):
            if(text_pos_l_style != ""):
                text_pos_style = text_pos_g_style + ' . ' + text_pos_l_style
            else:
                text_pos_style = text_pos_g_style 
        else:
            text_pos_style = text_pos_g_style 

        if(universal_neg == "ON"):
            if (text_neg_style != ''):
                text_neg_style = text_neg_style + ', text, watermark, low-quality, signature, moire pattern, downsampling, aliasing, distorted, blurry, glossy, blur, jpeg artifacts, compression artifacts, poorly drawn, low-resolution, bad, distortion, twisted, excessive, exaggerated pose, exaggerated limbs, grainy, symmetrical, duplicate, error, pattern, beginner, pixelated, fake, hyper, glitch, overexposed, high-contrast, bad-contrast'
            else:
                text_neg_style = 'text, watermark, low-quality, signature, moire pattern, downsampling, aliasing, distorted, blurry, glossy, blur, jpeg artifacts, compression artifacts, poorly drawn, low-resolution, bad, distortion, twisted, excessive, exaggerated pose, exaggerated limbs, grainy, symmetrical, duplicate, error, pattern, beginner, pixelated, fake, hyper, glitch, overexposed, high-contrast, bad-contrast'

        return text_pos_g_style, text_pos_l_style, text_pos_style, text_neg_style

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

class Crop_Image_Square:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "crop_position": (["center", "top", "bottom", "left", "right"],),
                "offset_x": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "offset_y": ("INT", { "default": 0, "min": -4096, "max": 4096, "step": 1, "display": "number" }),
                "zoom": ("FLOAT", { "default": 1, "min": 1, "max": 5, "step": 0.1, "display": "number" }),
                "interpolation": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),
                "target_rez": ("INT", { "default": 0 , "min": 0, "step": 8, "display": "number" }),
                "sharpening": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "crop_square"
    CATEGORY = "JPS Nodes/Image"

    def crop_square(self, image, crop_position, offset_x, offset_y, zoom, interpolation, target_rez,sharpening):
        _, h, w, _ = image.shape
        crop_size = min(h, w)

        offset_x = int (offset_x * zoom)
        offset_y = int (offset_y * zoom)

        if "center" in crop_position:
            x = round((w*zoom-crop_size) / 2)
            y = round((h*zoom-crop_size) / 2)
        if "top" in crop_position:
            x = round((w*zoom-crop_size) / 2)
            y = 0
        if "bottom" in crop_position:
            x = round((w*zoom-crop_size) / 2)
            y = h*zoom-crop_size
        if "left" in crop_position:
            x = 0
            y = round((h*zoom-crop_size) / 2)
        if "right" in crop_position:
            x = w*zoom-crop_size
            y = round((h*zoom-crop_size) / 2)

        x = int(x)
        y = int(y)

        if (x + offset_x >= 0 and x + crop_size + offset_x <= int(w*zoom)):
            x = x + offset_x
        elif (x + offset_x >= 0):
            x = int(w*zoom) - crop_size
        elif (x + crop_size + offset_x <= int(w*zoom)):
            x = 0

        if (y + offset_y >= 0 and y + crop_size + offset_y <= int(h*zoom)):
            y = y + offset_y
        elif (y + offset_y >= 0):
            y = int(h*zoom) - crop_size
        elif (y + crop_size + offset_y <= int(h*zoom)):
            y = 0

        x2 = x+crop_size
        y2 = y+crop_size

        zoomedimage = image[:, 0:h, 0:w, :]

        zoomedimage = zoomedimage.permute([0,3,1,2])        

        zoomedimage = comfy.utils.lanczos(zoomedimage, int(w*zoom), int(h*zoom))

        zoomedimage = zoomedimage.permute([0,2,3,1])

        output = zoomedimage[:, y:y2, x:x2, :]

        output = output.permute([0,3,1,2])

        if target_rez != 0:
            if interpolation == "lanczos":
                output = comfy.utils.lanczos(output, target_rez, target_rez)
            else:
                output = F.interpolate(output, size=(target_rez, target_rez), mode=interpolation)

        if sharpening > 0:
            output = contrast_adaptive_sharpening(output, sharpening)
    
        output = output.permute([0,2,3,1])

        return(output, )

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

class Crop_Image_TargetSize:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_w": ("INT", { "default": 0 , "min": 0, "step": 8, "display": "number" }),
                "target_h": ("INT", { "default": 0 , "min": 0, "step": 8, "display": "number" }),                
                "crop_position": (["center","top", "bottom", "left", "right"],),
                "offset": ("INT", { "default": 0, "min": -2048, "max": 2048, "step": 1, "display": "number" }),
                "interpolation": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],),
                "sharpening": ("FLOAT", {"default": 0.0, "min": 0, "max": 1, "step": 0.05}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "crop_targetsize"
    CATEGORY = "JPS Nodes/Image"

    def crop_targetsize(self, image, target_w, target_h, crop_position, offset, interpolation, sharpening):
        _, current_h, current_w, _ = image.shape

        current_ar = current_w / current_h

        if target_w / current_ar >= target_h:
            new_w = target_w
            new_h = round(new_w / current_ar)
            offset_h = offset
            offset_w = 0
        else:
            new_h = target_h
            new_w = round(new_h * current_ar)
            offset_w = offset
            offset_h = 0

  #      print("New Size")
  #      print(new_w)
  #      print(new_h)

        resized_image = image.permute([0,3,1,2])

        if interpolation == "lanczos":
            resized_image = comfy.utils.lanczos(resized_image, new_w, new_h)
        else:
            resized_image = F.interpolate(resized_image, size=(new_h, new_w), mode=interpolation)

        resized_image = resized_image.permute([0,2,3,1])

        output_image = resized_image

        if (crop_position == "left"):
            newoffset_w = offset_w
        elif (crop_position == "right"):
            newoffset_w = new_w - target_w + offset_w
        else:
            newoffset_w = (new_w - target_w) // 2 + offset_w

        if (crop_position == "top"):
            newoffset_h = offset_h
        elif (crop_position == "bottom"):
            newoffset_h = new_h - target_h + offset_h
        else:
            newoffset_h = (new_h - target_h) // 2 + offset_h

        if newoffset_w < 0:
            newoffset_w = 0
        elif newoffset_w + target_w > new_w:
            newoffset_w = new_w - target_w

        if newoffset_h < 0:
            newoffset_h = 0
        elif newoffset_h + target_h > new_h:
            newoffset_h = new_h - target_h
        
        x = newoffset_w
        x2 = newoffset_w+target_w
        y = newoffset_h
        y2 = newoffset_h+target_h

 #       print("x: "+str(x))
 #       print("x2: "+str(x2))
 #       print("y: "+str(y))
 #       print("y2: "+str(y2))

        if sharpening > 0:
            output_image = contrast_adaptive_sharpening(output_image, sharpening)

        output_image = output_image[:, y:y2, x:x2, :]

        return(output_image, )

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

class Save_Images_Plus:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {"required": 
                    {"images": ("IMAGE", ),
                     "filename_prefix": ("STRING", {"default": "ComfyUI"})},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("dummy_out",)
    FUNCTION = "save_images_plus"

    OUTPUT_NODE = True

    CATEGORY = "JPS Nodes/IO"

    def save_images_plus(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            file = f"{filename}_{counter:03}.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        #return { "ui": { "images": results } }
        return(int(1), )            

#---------------------------------------------------------------------------------------------------------------------------------------------------#    

NODE_CLASS_MAPPINGS = {
    "Lora Loader (JPS)": IO_Lora_Loader,
    "SDXL Resolutions (JPS)": SDXL_Resolutions,
    "SDXL Basic Settings (JPS)": SDXL_Basic_Settings,
    "Generation TXT IMG Settings (JPS)": Generation_TXT_IMG_Settings,
    "Crop Image Settings (JPS)": CropImage_Settings,
    "ImageToImage Settings (JPS)": ImageToImage_Settings,    
    "CtrlNet CannyEdge Settings (JPS)": CtrlNet_CannyEdge_Settings,
    "CtrlNet ZoeDepth Settings (JPS)": CtrlNet_ZoeDepth_Settings,
    "CtrlNet MiDaS Settings (JPS)": CtrlNet_MiDaS_Settings,
    "CtrlNet OpenPose Settings (JPS)": CtrlNet_OpenPose_Settings,
    "Revision Settings (JPS)": Revision_Settings,
    "IP Adapter Settings (JPS)": IP_Adapter_Settings,
    "IP Adapter Single Settings (JPS)": IP_Adapter_Single_Settings,
    "Sampler Scheduler Settings (JPS)": Sampler_Scheduler_Settings,
    "Integer Switch (JPS)": Integer_Switch,
    "Image Switch (JPS)": Image_Switch,
    "Latent Switch (JPS)": Latent_Switch,
    "Conditioning Switch (JPS)": Conditioning_Switch,
    "Model Switch (JPS)": Model_Switch,
    "IPA Switch (JPS)": IPA_Switch,
    "VAE Switch (JPS)": VAE_Switch,
    "Mask Switch (JPS)": Mask_Switch,
    "ControlNet Switch (JPS)": ControlNet_Switch,
    "Disable Enable Switch (JPS)": Disable_Enable_Switch,
    "Enable Disable Switch (JPS)": Enable_Disable_Switch,
    "SDXL Basic Settings Pipe (JPS)": SDXL_Basic_Settings_Pipe,
    "Crop Image Pipe (JPS)": CropImage_Pipe,
    "ImageToImage Pipe (JPS)": ImageToImage_Pipe,
    "CtrlNet CannyEdge Pipe (JPS)": CtrlNet_CannyEdge_Pipe,
    "CtrlNet ZoeDepth Pipe (JPS)": CtrlNet_ZoeDepth_Pipe,
    "CtrlNet MiDaS Pipe (JPS)": CtrlNet_MiDaS_Pipe,
    "CtrlNet OpenPose Pipe (JPS)": CtrlNet_OpenPose_Pipe,    
    "IP Adapter Settings Pipe (JPS)": IP_Adapter_Settings_Pipe,
    "IP Adapter Single Settings Pipe (JPS)": IP_Adapter_Single_Settings_Pipe,
    "Revision Settings Pipe (JPS)": Revision_Settings_Pipe,
    "SDXL Fundamentals MultiPipe (JPS)": SDXL_Fundamentals_MultiPipe,
    "Images Masks MultiPipe (JPS)": Images_Masks_MultiPipe,
    "SDXL Recommended Resolution Calc (JPS)": SDXL_Recommended_Resolution_Calc,
    "Resolution Multiply (JPS)": Math_Resolution_Multiply,
    "Largest Int (JPS)": Math_Largest_Integer,
    "Multiply Int Int (JPS)": Math_Multiply_INT_INT,
    "Multiply Int Float (JPS)": Math_Multiply_INT_FLOAT,
    "Multiply Float Float (JPS)": Math_Multiply_FLOAT_FLOAT,
    "Substract Int Int (JPS)": Math_Substract_INT_INT,
    "Text Concatenate (JPS)": Text_Concatenate,
    "Get Date Time String (JPS)": Get_Date_Time_String,
    "Get Image Size (JPS)": Get_Image_Size,
    "Crop Image Square (JPS)": Crop_Image_Square,
    "Crop Image TargetSize (JPS)": Crop_Image_TargetSize,
    "SDXL Prompt Styler (JPS)": SDXL_Prompt_Styler,
    "SDXL Prompt Handling (JPS)": SDXL_Prompt_Handling,
    "SDXL Prompt Handling Plus (JPS)": SDXL_Prompt_Handling_Plus,
    "Text Prompt (JPS)": Text_Prompt,
    "Save Images Plus (JPS)": Save_Images_Plus,
}
