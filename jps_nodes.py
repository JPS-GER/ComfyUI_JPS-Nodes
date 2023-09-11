#------------------------------------------------------------------------#
# JPS Custom Nodes          https://github.com/JPS-GER/ComfyUI_JPS-Nodes #
# for ComfyUI               https://github.com/comfyanonymous/ComfyUI    #
#------------------------------------------------------------------------#

import json
import os
import comfy.sd
import folder_paths
from datetime import datetime

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

    text_positive = f"{text_g_positive} . {text_l_positive}" if text_l_positive else text_g_positive

    json_negative_prompt = template.get('negative_prompt', "")
    text_negative = f"{json_negative_prompt}, {negative_prompt}" if json_negative_prompt and negative_prompt else json_negative_prompt or negative_prompt

    return text_g_positive, text_l_positive, text_positive, text_negative


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
        return positive_prompt_g, positive_prompt_l, f"{positive_prompt_g} . {positive_prompt_l}", negative_prompt

    template = find_template_by_name(json_data, template_name)

    if template:
        return replace_prompts_in_template(template, positive_prompt_g, positive_prompt_l, negative_prompt)
    else:
        return positive_prompt_g, positive_prompt_l, f"{positive_prompt_g} . {positive_prompt_l}", negative_prompt

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
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]
    vaefrom = ["Separate VAE","Base Model VAE","Refiner Model VAE"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "resolution": (s.resolution,),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "vae_source": (s.vaefrom,),
                "steps_total": ("INT", {"default": 60, "min": 20, "max": 250, "step": 5}),
                "base_percentage": ("INT", {"default": 80, "min": 5, "max": 100, "step": 5}),
                "cfg_base": ("FLOAT", {"default": 7, "min": 1, "max": 20, "step": 0.5}),
                "cfg_refiner": ("FLOAT", {"default": 0, "min": 0, "max": 20, "step": 0.5}),
                "ascore_refiner": ("FLOAT", {"default": 6, "min": 1, "max": 10, "step": 0.5}),
                "clip_skip_base": ("INT", {"default": -1, "min": -24, "max": -1}),
                "clip_skip_refiner": ("INT", {"default": -1, "min": -24, "max": -1}),
                "filename": ("STRING", {"default": "JPS"}),
        }}
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("sdxl_basic_settings",)
    FUNCTION = "get_values"

    CATEGORY="JPS Nodes/Settings"

    def get_values(self,resolution,sampler_name,scheduler,vae_source,steps_total,base_percentage,cfg_base,cfg_refiner,ascore_refiner,clip_skip_base,clip_skip_refiner,filename):
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
        
        vae_select = 1
        if(vae_source == "Base Model VAE"):
            vae_select = 2
        if(vae_source == "Refiner Model VAE"):
            vae_select = 3

        sdxl_basic_settings = width, height, sampler_name, scheduler, vae_select, steps_total, step_split, cfg_base, cfg_refiner, ascore_refiner, clip_skip_base, clip_skip_refiner, filename
        

        return(sdxl_basic_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Basic_Settings_Pipe:
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]
    vaefrom = ["Separate VAE","Base Model VAE","Refiner Model VAE"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sdxl_basic_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("BASIC_PIPE","INT","INT",comfy.samplers.KSampler.SAMPLERS,comfy.samplers.KSampler.SCHEDULERS,"INT","INT","INT","FLOAT","FLOAT","FLOAT","INT","INT","STRING",)
    RETURN_NAMES = ("sdxl_basic_settings","width","height","sampler_name","scheduler","vae_select","steps_total","step_split","cfg_base","cfg_refiner","ascore_refiner","clip_skip_base","clip_skip_refiner","filename",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,sdxl_basic_settings):
        
        width, height, sampler_name, scheduler, vae_select, steps_total, step_split, cfg_base, cfg_refiner, ascore_refiner, clip_skip_base, clip_skip_refiner, filename = sdxl_basic_settings

        return(sdxl_basic_settings, int(width), int(height), sampler_name, scheduler, int(vae_select), int(steps_total), int(step_split), float(cfg_base), float(cfg_refiner), float(ascore_refiner), int(clip_skip_base), int(clip_skip_refiner), str(filename),)

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
                "factor": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
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
    time_format = ["%Y%m%d%H%M%S","%Y%m%d%H%M","%Y%m%d","%Y-%m-%d-%H_%M_%S","%Y-%m-%d-%H_%M","%Y-%m-%d","%Y-%m-%d %H_%M_%S","%Y-%m-%d %H_%M","%Y-%m-%d"]
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

class Generation_Settings:
    mode = ["Text Prompt","Image to Image", "Canny", "Depth", "Inpainting"]
    resfrom = ["Use Settings Resolution", "Use Image Resolution"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (s.mode,),
                "resfrom": (s.resfrom,),
                "strength_percent": ("INT", {"default": 50, "min": 0, "max": 100, "step": 5}),
                "ctrl_start_percent": ("INT", {"default": 0, "min": 0, "max": 100, "step": 5}),
                "ctrl_stop_percent": ("INT", {"default": 100, "min": 0, "max": 100, "step": 5}),
                "ctrl_low_threshold": ("INT", {"default": 100, "min": 0, "max": 255, "step": 5}),
                "ctrl_high_threshold": ("INT", {"default": 200, "min": 0, "max": 255, "step": 5}),
            }   
        }
    RETURN_TYPES = ("BASIC_PIPE",) 
    RETURN_NAMES = ("generation_settings",)
    FUNCTION = "get_genfull"

    CATEGORY="JPS Nodes/Settings"

    def get_genfull(self, mode, resfrom, strength_percent, ctrl_start_percent, ctrl_stop_percent, ctrl_low_threshold, ctrl_high_threshold):
        gen_mode = 1
        res_from = 1
        img_strength = 0
        ctrl_strength = 0
        ctrl_start = 0
        ctrl_stop = 0
        ctrl_low = 0
        ctrl_high = 0
        if(mode == "Text Prompt"):
            gen_mode = int(1)
            img_strength = 0.001
            ctrl_strength = 0
            ctrl_start = 0
            ctrl_stop = 0
            ctrl_low = 0
            ctrl_high = 0
        if(mode == "Image to Image"):
            gen_mode = int(2)
            img_strength = strength_percent / 100
            ctrl_strength = 0
            ctrl_start = 0
            ctrl_stop = 0
            ctrl_low = 0
            ctrl_high = 0
        if(mode == "Canny"):
            gen_mode = int(3)
            img_strength = 0.001
            ctrl_strength = strength_percent / 100
            ctrl_start = ctrl_start_percent / 100
            ctrl_stop = ctrl_stop_percent / 100
            ctrl_low = ctrl_low_threshold
            ctrl_high = ctrl_high_threshold
        if(mode == "Depth"):
            gen_mode = int(4)
            img_strength = 0.001
            ctrl_strength = strength_percent / 100
            ctrl_start = ctrl_start_percent / 100
            ctrl_stop = ctrl_stop_percent / 100
            ctrl_low = ctrl_low_threshold
            ctrl_high = ctrl_high_threshold
        if(mode == "Inpainting"):
            gen_mode = int(5)
            img_strength = (100 - strength_percent + 0.001) / 100
            ctrl_strength = 0
            ctrl_start = 0
            ctrl_stop = 0
            ctrl_low = 0
            ctrl_high = 0
        if(resfrom == "Use Settings Resolution"):
            res_from = int(1)
        if(resfrom == "Use Image Resolution"):
            res_from = int(2)
        
        generation_settings = gen_mode, res_from, img_strength, ctrl_strength, ctrl_start, ctrl_stop, ctrl_low, ctrl_high

        return(generation_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Generation_Settings_Pipe:
#    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]
#    vaefrom = ["Separate VAE","Base Model VAE","Refiner Model VAE"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "generation_settings": ("BASIC_PIPE",)
            },
        }
    RETURN_TYPES = ("BASIC_PIPE","INT","INT","FLOAT","FLOAT","FLOAT","FLOAT","INT","INT",)
    RETURN_NAMES = ("generation_settings","gen_mode", "res_from", "img_strength", "ctrl_strength", "ctrl_start", "ctrl_stop", "ctrl_low", "ctrl_high",)
    FUNCTION = "give_values"

    CATEGORY="JPS Nodes/Pipes"

    def give_values(self,generation_settings):
        
        gen_mode, res_from, img_strength, ctrl_strength, ctrl_start, ctrl_stop, ctrl_low, ctrl_high = generation_settings

        return(generation_settings, int(gen_mode), int(res_from), float(img_strength), float(ctrl_strength), float(ctrl_start), float(ctrl_stop), int(ctrl_low), int(ctrl_high),)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class IP_Adapter_Settings:
    ipa1switch = ["IP Adapter #1 OFF","IP Adapter #1 ON"]
    ipa2switch = ["IP Adapter #2 OFF","IP Adapter #2 ON"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ipa1_switch": (s.ipa1switch,),
                "ipa2_switch": (s.ipa2switch,),
                "ipa1_weight": ("FLOAT", {"default": 0.5, "min": -1, "max": 3, "step": 0.1}),
                "ipa2_weight": ("FLOAT", {"default": 0.5, "min": -1, "max": 3, "step": 0.1}),
            }
        }
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("ip_adapter_settings",)
    FUNCTION = "get_ipamode"

    CATEGORY="JPS Nodes/Settings"

    def get_ipamode(self,ipa1_switch,ipa2_switch,ipa1_weight,ipa2_weight):
        ipa1switch = int(1)
        ipa2switch = int(1)
        if(ipa1_switch == "IP Adapter #1 OFF"):
            ipa1switch = int(1)
            ipa1weight = 0
        if(ipa1_switch == "IP Adapter #1 ON"):
            ipa1switch = int(2)
            ipa1weight = ipa1_weight
        if(ipa2_switch == "IP Adapter #2 OFF"):
            ipa2switch = int(1)
            ipa2weight = 0
        if(ipa2_switch == "IP Adapter #2 ON"):
            ipa2switch = int(2)
            ipa2weight = ipa2_weight

        ip_adapter_settings = ipa1switch,ipa2switch,ipa1weight,ipa2weight

        return(ip_adapter_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class IP_Adapter_Settings_Pipe:
    #ipa1switch = ["IP Adapter #1 OFF","IP Adapter #1 ON"]
    #ipa2switch = ["IP Adapter #2 OFF","IP Adapter #2 ON"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ip_adapter_settings": ("BASIC_PIPE",),
            }
        }
    RETURN_TYPES = ("INT","INT","FLOAT","FLOAT",)
    RETURN_NAMES = ("ipa1_switch", "ipa2_switch", "ipa1_weight", "ipa2_weight",)
    FUNCTION = "get_ipamode"

    CATEGORY="JPS Nodes/Pipes"

    def get_ipamode(self,ip_adapter_settings):

        ipa1switch,ipa2switch,ipa1weight,ipa2weight = ip_adapter_settings

        return(int(ipa1switch),int(ipa2switch),float(ipa1weight),float(ipa2weight),)
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Revision_Settings:
    rev1switch = ["Revision #1 OFF","Revision #1 ON"]
    rev2switch = ["Revision #2 OFF","Revision #2 ON"]
    posprompt = ["Pos. Prompt OFF","Pos. Prompt ON"]    
    negprompt = ["Neg. Prompt OFF","Neg. Prompt ON"]    

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "rev1_switch": (s.rev1switch,),
                "rev2_switch": (s.rev2switch,),
                "pos_prompt": (s.posprompt,),                
                "neg_prompt": (s.negprompt,),
                "rev1_strength": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),
                "rev2_strength": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),
                "rev1_noiseaug": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),
                "rev2_noiseaug": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),
            }
        }
    RETURN_TYPES = ("BASIC_PIPE",)
    RETURN_NAMES = ("revision_settings",)
    FUNCTION = "get_revmode"

    CATEGORY="JPS Nodes/Settings"

    def get_revmode(self,rev1_switch,rev2_switch,pos_prompt,neg_prompt,rev1_strength,rev2_strength,rev1_noiseaug,rev2_noiseaug,):
        rev1switch = int(1)
        rev2switch = int(1)
        if(rev1_switch == "Revision #1 OFF"):
            rev1switch = int(1)
            rev1strength = 0
            rev1noiseaug = 0 
        if(rev1_switch == "Revision #1 ON"):
            rev1switch = int(2)
            rev1strength = rev1_strength
            rev1noiseaug = rev1_noiseaug
        if(rev2_switch == "Revision #2 OFF"):
            rev2switch = int(1)
            rev2strength = 0
            rev2noiseaug = 0
        if(rev2_switch == "Revision #2 ON"):
            rev2switch = int(2)
            rev2strength = rev2_strength
            rev2noiseaug = rev2_noiseaug
        if(pos_prompt == "Pos. Prompt OFF"):
            posprompt = int(1)
        if(pos_prompt == "Pos. Prompt ON"):
            posprompt = int(2)
        if(neg_prompt == "Neg. Prompt OFF"):
            negprompt = int(1)
        if(neg_prompt == "Neg. Prompt ON"):
            negprompt = int(2)
        if(rev1switch == int(1) and rev2switch == int(1)):
            posprompt = int(2)
            negprompt = int(2)

        revision_settings = rev1switch,rev2switch,posprompt,negprompt,rev1strength,rev2strength,rev1noiseaug,rev2_noiseaug

        return(revision_settings,)

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Revision_Settings_Pipe:
    #rev1switch = ["Revision #1 OFF","Revision #1 ON"]
    #rev2switch = ["Revision #2 OFF","Revision #2 ON"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "revision_settings": ("BASIC_PIPE",),
            }
        }
    RETURN_TYPES = ("INT","INT","INT","INT","FLOAT","FLOAT","FLOAT","FLOAT",)
    RETURN_NAMES = ("rev1_switch", "rev2_switch", "pos_prompt", "neg_prompt", "rev1_strength", "rev2_strength", "rev1_noiseaug", "rev2_noiseaug",)
    FUNCTION = "get_revmode"

    CATEGORY="JPS Nodes/Pipes"

    def get_revmode(self,revision_settings):

        rev1switch,rev2switch,posprompt,negprompt,rev1strength,rev2strength,rev1noiseaug,rev2noiseaug = revision_settings

        return(int(rev1switch),int(rev2switch),int(posprompt),int(negprompt),float(rev1strength),float(rev2strength),float(rev1noiseaug),float(rev2noiseaug),)

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

    @classmethod
    def INPUT_TYPES(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        self.json_data, styles = load_styles_from_directory(current_directory)
        
        return {
            "required": {
                "text_positive_g": ("STRING", {"default": "", "multiline": True}),
                "text_positive_l": ("STRING", {"default": "", "multiline": True}),
                "text_negative": ("STRING", {"default": "", "multiline": True}),
                "style": ((styles), ),
            },
        }

    RETURN_TYPES = ('STRING','STRING','STRING','STRING',)
    RETURN_NAMES = ('text_positive_g','text_positive_l','text_positive','text_negative',)
    FUNCTION = 'sdxlpromptstyler'
    CATEGORY = 'JPS Nodes/Style'

    def sdxlpromptstyler(self, text_positive_g, text_positive_l, text_negative, style):
        # Process and combine prompts in templates
        # The function replaces the positive prompt placeholder in the template,
        # and combines the negative prompt with the template's negative prompt, if they exist.
        text_positive_g_styled, text_positive_l_styled, text_positive_styled, text_negative_styled = read_sdxl_templates_replace_and_combine(self.json_data, style, text_positive_g, text_positive_l, text_negative)
 
        print(f"style: {style}")
        print(f"text_positive_g: {text_positive_g}")
        print(f"text_positive_l: {text_positive_l}")
        print(f"text_negative: {text_negative}")
        print(f"text_positive_g_styled: {text_positive_g_styled}")
        print(f"text_positive_l_styled: {text_positive_l_styled}")
        print(f"text_positive_styled: {text_positive_styled}")
        print(f"text_negative_styled: {text_negative_styled}")

        return text_positive_g_styled, text_positive_l_styled, text_positive_styled, text_negative_styled

#---------------------------------------------------------------------------------------------------------------------------------------------------#                       

NODE_CLASS_MAPPINGS = {
    "Lora Loader (JPS)": IO_Lora_Loader,
    "SDXL Resolutions (JPS)": SDXL_Resolutions,
    "SDXL Basic Settings (JPS)": SDXL_Basic_Settings,
    "Generation TXT IMG Settings (JPS)": Generation_TXT_IMG_Settings,
    "Generation Settings (JPS)": Generation_Settings,
    "Revision Settings (JPS)": Revision_Settings,
    "IP Adapter Settings (JPS)": IP_Adapter_Settings,
    "Sampler Scheduler Settings (JPS)": Sampler_Scheduler_Settings,
    "Integer Switch (JPS)": Integer_Switch,
    "Image Switch (JPS)": Image_Switch,
    "Latent Switch (JPS)": Latent_Switch,
    "Conditioning Switch (JPS)": Conditioning_Switch,
    "Model Switch (JPS)": Model_Switch,
    "VAE Switch (JPS)": VAE_Switch,
    "ControlNet Switch (JPS)": ControlNet_Switch,
    "Disable Enable Switch (JPS)": Disable_Enable_Switch,
    "Enable Disable Switch (JPS)": Enable_Disable_Switch,
    "SDXL Basic Settings Pipe (JPS)": SDXL_Basic_Settings_Pipe,
    "Generation Settings Pipe (JPS)": Generation_Settings_Pipe,
    "IP Adapter Settings Pipe (JPS)": IP_Adapter_Settings_Pipe,
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
    "SDXL Prompt Styler (JPS)": SDXL_Prompt_Styler,
    "SDXL Prompt Handling (JPS)": SDXL_Prompt_Handling,
}
