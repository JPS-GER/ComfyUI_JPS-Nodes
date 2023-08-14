#------------------------------------------------------------------------#
# JPS CustomNodes           https://github.com/JPS-GER/ComfyUI_JPS-Nodes #
# for ComfyUI               https://github.com/comfyanonymous/ComfyUI    #
#------------------------------------------------------------------------#

class JPS_SDXL_Resolutions:
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
    RETURN_NAMES = ("height", "width")
    FUNCTION = "get_resolutions"

    CATEGORY="JPS Nodes/SDXL"

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

class JPS_SDXL_BasicSettings:
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "resolution": (s.resolution,),
                "steps_total": ("INT", {"default": 40, "min": 20, "max": 200, "step": 5}),
                "base_percentage": ("INT", {"default": 80, "min": 5, "max": 100, "step": 5}),
                "cfg_base": ("FLOAT", {"default": 6, "min": 1, "max": 20, "step": 0.1}),
                "cfg_refiner": ("FLOAT", {"default": 0, "min": 0, "max": 20, "step": 0.1}),
                "ascore_refiner": ("FLOAT", {"default": 6, "min": 1, "max": 10, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
        }}
    RETURN_TYPES = ("INT","INT","INT","INT","FLOAT","FLOAT","FLOAT","INT")
    RETURN_NAMES = ("width", "height", "steps_total", "step_split","cfg_base","cfg_refiner","ascore_refiner","seed")
    FUNCTION = "get_values"

    CATEGORY="JPS Nodes/SDXL"

    def get_values(self,resolution,steps_total,base_percentage,cfg_base,cfg_refiner,ascore_refiner,seed):
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
            
        return(int(width),int(height),int(steps_total),int(step_split),float(cfg_base),float(cfg_refiner),float(ascore_refiner),int(seed))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class JPS_SDXL_AdditionalSettings:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "offset_percentage": ("INT", {"default": 50, "min": -200, "max": 200, "step": 10}),
                "upscale_total_steps": ("INT", {"default": 30, "min": 10, "max": 100, "step": 5}),
                "upscale_percentage": ("INT", {"default": 32, "min": 0, "max": 100, "step": 1}),
                "facefix_percentage": ("INT", {"default": 10, "min": 0, "max": 100, "step": 1}),
                "filename_prefix": ("STRING", {"default": "JPS"}),
        }}
    RETURN_TYPES = ("FLOAT","INT","INT","FLOAT","STRING")
    RETURN_NAMES = ("offset_strength", "upscale_total_steps", "upscale_start_step", "facefix_strength","filename_prefix")
    FUNCTION = "get_addvalues"

    CATEGORY="JPS Nodes/SDXL"

    def get_addvalues(self,offset_percentage,upscale_total_steps,upscale_percentage,facefix_percentage,filename_prefix):
        offset_strength = int(offset_percentage) / 100
        upscale_total_steps = int(upscale_total_steps)
        upscale_start_step = int(upscale_total_steps) * (100 - upscale_percentage) / 100 
        facefix_strength = int(facefix_percentage) / 100
        filename_prefix = str(filename_prefix)
            
        return(float(offset_strength),int(upscale_total_steps),int(upscale_start_step),float(facefix_strength),str(filename_prefix))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class JPS_Math_ResolutionMultiply:
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 256, "max": 4096, "step": 16}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 100, "step": 16}),
                "factor": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
        }}
    RETURN_TYPES = ("INT","INT")
    RETURN_NAMES = ("width_resize", "height_resize")
    FUNCTION = "get_newres"

    CATEGORY="JPS Nodes/Math"

    def get_newres(self,width,height,factor):
        factor = int(factor)
        width = int(width)
        width_resize = int(width) * int(factor)
        height = int(height)
        height_resize = int (height) * int(factor)
            
        return(int(width_resize),int(height_resize))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class JPS_Math_LargestInt:

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
    RETURN_TYPES = ("INT", )
    RETURN_NAMES = ("largest_int", )
    FUNCTION = "get_lrg"

    CATEGORY="JPS Nodes/Math"

    def get_lrg(self,int_a,int_b):
        largest_int = int(int_b)

        if int_a >= int_b:
            largest_int = int(int_a)

        return(int(largest_int), )

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class JPS_Switch_GenerationMode:
    genmode = ["1 - TXT2IMG","2 - IMG2IMG"]
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "genmode": (s.genmode,),
                "image_percentage": ("INT", {"default": 50, "min": 0, "max": 100, "step": 1}),
            }
        }
    RETURN_TYPES = ("INT","FLOAT",)
    RETURN_NAMES = ("genmodevalue", "img_strength")
    FUNCTION = "get_genmode"

    CATEGORY="JPS Nodes/Switch"

    def get_genmode(self,genmode,image_percentage):
        genmodevalue = 1
        img_strength = 0
        if(genmode == "1 - TXT2IMG"):
            genmodevalue = int(1)
            img_strength = 0.001
        if(genmode == "2 - IMG2IMG"):
            genmodevalue = int(2)
            img_strength = image_percentage / 100
            
        return(int(genmodevalue),float(img_strength))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

NODE_CLASS_MAPPINGS = {
    "SDXL Resolutions (JPS)": JPS_SDXL_Resolutions,
    "SDXL BasicSettings (JPS)": JPS_SDXL_BasicSettings,
    "SDXL AdditionalSettings (JPS)": JPS_SDXL_AdditionalSettings,
    "Math ResolutionMultiply (JPS)": JPS_Math_ResolutionMultiply,
    "Math LargestInt (JPS)": JPS_Math_LargestInt,
    "Switch GenerationMode (JPS)": JPS_Switch_GenerationMode,
}

