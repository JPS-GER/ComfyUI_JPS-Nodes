#------------------------------------------------------------------------#
# JPS Custom Nodes          https://github.com/JPS-GER/ComfyUI_JPS-Nodes #
# for ComfyUI               https://github.com/comfyanonymous/ComfyUI    #
#------------------------------------------------------------------------#

import comfy.sd

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

class SDXL_Basic_Settings:
    resolution = ["square - 1024x1024 (1:1)","landscape - 1152x896 (4:3)","landscape - 1216x832 (3:2)","landscape - 1344x768 (16:9)","landscape - 1536x640 (21:9)", "portrait - 896x1152 (3:4)","portrait - 832x1216 (2:3)","portrait - 768x1344 (9:16)","portrait - 640x1536 (9:21)"]

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
                "cfg_base": ("FLOAT", {"default": 7, "min": 1, "max": 20, "step": 0.1}),
                "cfg_refiner": ("FLOAT", {"default": 0, "min": 0, "max": 20, "step": 0.1}),
                "ascore_refiner": ("FLOAT", {"default": 6, "min": 1, "max": 10, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "filename_prefix": ("STRING", {"default": "JPS"}),
        }}
    RETURN_TYPES = ("INT","INT",comfy.samplers.KSampler.SAMPLERS,comfy.samplers.KSampler.SCHEDULERS,"INT","INT","FLOAT","FLOAT","FLOAT","INT","STRING")
    RETURN_NAMES = ("width", "height", "sampler_name", "scheduler", "steps_total", "step_split","cfg_base","cfg_refiner","ascore_refiner","seed","filename_prefix")
    FUNCTION = "get_values"

    CATEGORY="JPS Nodes/SDXL"

    def get_values(self,resolution,sampler_name,scheduler,steps_total,base_percentage,cfg_base,cfg_refiner,ascore_refiner,seed,filename_prefix):
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
            
        return(int(width),int(height),sampler_name,scheduler,int(steps_total),int(step_split),float(cfg_base),float(cfg_refiner),float(ascore_refiner),int(seed),str(filename_prefix))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class SDXL_Additional_Settings:

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "offset_percentage": ("INT", {"default": 50, "min": -200, "max": 200, "step": 5}),
                "upscale_total_steps": ("INT", {"default": 50, "min": 10, "max": 100, "step": 5}),
                "upscale_percentage": ("INT", {"default": 33, "min": 0, "max": 100, "step": 5}),
                "facefix_percentage": ("INT", {"default": 15, "min": 0, "max": 100, "step": 5}),
        }}
    RETURN_TYPES = ("FLOAT","INT","INT","FLOAT")
    RETURN_NAMES = ("offset_strength", "upscale_total_steps", "upscale_start_step", "facefix_strength")
    FUNCTION = "get_addvalues"

    CATEGORY="JPS Nodes/SDXL"

    def get_addvalues(self,offset_percentage,upscale_total_steps,upscale_percentage,facefix_percentage):
        offset_strength = int(offset_percentage) / 100
        upscale_total_steps = int(upscale_total_steps)
        upscale_start_step = int(upscale_total_steps) * (100 - upscale_percentage) / 100 
        facefix_strength = int(facefix_percentage) / 100
            
        return(float(offset_strength),int(upscale_total_steps),int(upscale_start_step),float(facefix_strength))

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

    CATEGORY = "JPS Nodes/SDXL"

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

class Switch_Generation_Mode:
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

    CATEGORY="JPS Nodes/Switches"

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

class Switch_Generation_Mode_4in1:
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
    RETURN_TYPES = ("INT","INT","FLOAT","FLOAT","FLOAT","FLOAT","INT","INT")
    RETURN_NAMES = ("gen_mode", "res_from", "img_strength", "ctrl_strength", "ctrl_start", "ctrl_stop", "ctrl_low", "ctrl_high")
    FUNCTION = "get_genmodefour"

    CATEGORY="JPS Nodes/Switches"

    def get_genmodefour(self, mode, resfrom, strength_percent, ctrl_start_percent, ctrl_stop_percent, ctrl_low_threshold, ctrl_high_threshold):
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
        
        return(int(gen_mode),int(res_from),float(img_strength),float(ctrl_strength),float(ctrl_start),float(ctrl_stop),int(ctrl_low),int(ctrl_high))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Switch_Revision_Mode:
    revmode = ["Revision Mode OFF","Revision Mode ON"]
    posprompt = ["Pos. Prompt OFF","Pos. Prompt ON"]    
    negprompt = ["Neg. Prompt OFF","Neg. Prompt ON"]    

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "revmode": (s.revmode,),
                "posprompt": (s.posprompt,),                
                "negprompt": (s.negprompt,),
                "rev_strength1": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),
                "rev_noise_aug1": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),
                "rev_strength2": ("FLOAT", {"default": 1, "min": 0, "max": 10, "step": 0.1}),
                "rev_noise_aug2": ("FLOAT", {"default": 0, "min": 0, "max": 1, "step": 0.1}),
            }
        }
    RETURN_TYPES = ("INT","INT","INT","FLOAT","FLOAT","FLOAT","FLOAT")
    RETURN_NAMES = ("rev_mode", "pos_prompt", "neg_prompt", "rev_strength1", "rev_noise_aug1","rev_strength2", "rev_noise_aug2")
    FUNCTION = "get_revmode"

    CATEGORY="JPS Nodes/Switches"

    def get_revmode(self,revmode,posprompt,negprompt,rev_strength1,rev_noise_aug1,rev_strength2,rev_noise_aug2):
        rev_mode = int(0)
        if(revmode == "Revision Mode OFF"):
            rev_mode = int(0)
            rev_strength1 = 0
            rev_noise_aug1 = 0
            rev_strength2 = 0
            rev_noise_aug2 = 0
        if(revmode == "Revision Mode ON"):
            rev_mode = int(1)
            rev_strength1 = rev_strength1
            rev_noise_aug1 = rev_noise_aug1
            rev_strength2 = rev_strength2
            rev_noise_aug2 = rev_noise_aug2
        if(posprompt == "Pos. Prompt OFF"):
            pos_prompt = int(0)
        if(posprompt == "Pos. Prompt ON"):
            pos_prompt = int(1)
        if(negprompt == "Neg. Prompt OFF"):
            neg_prompt = int(0)
        if(negprompt == "Neg. Prompt ON"):
            neg_prompt = int(1)

        return(int(rev_mode),int(pos_prompt),int(neg_prompt),float(rev_strength1),float(rev_noise_aug1),float(rev_strength2),float(rev_noise_aug2))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Switch_IP_Adapter_Mode:
    ipamode = ["IP Adapter Mode OFF","IP Adapter Mode ON"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ipamode": (s.ipamode,),
                "ipa_weight": ("FLOAT", {"default": 1, "min": -1, "max": 3, "step": 0.1}),
            }
        }
    RETURN_TYPES = ("INT","FLOAT")
    RETURN_NAMES = ("ipa_mode", "ipa_weight")
    FUNCTION = "get_ipamode"

    CATEGORY="JPS Nodes/Switches"

    def get_ipamode(self,ipamode,ipa_weight):
        ipa_mode = int(0)
        if(ipamode == "IP Adapter Mode OFF"):
            ipa_mode = int(0)
            ipa_weight = 0
        if(ipamode == "IP Adapter Mode ON"):
            ipa_mode = int(1)
            ipa_weight = ipa_weight

        return(int(ipa_mode),float(ipa_weight))

#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Menu_Sampler_Scheduler:
    CATEGORY = 'JPS Nodes/Menu Items'
    RETURN_TYPES = (comfy.samplers.KSampler.SAMPLERS,comfy.samplers.KSampler.SCHEDULERS,)
    RETURN_NAMES = ("sampler_name","scheduler",)
    FUNCTION = "get_samsched"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"sampler_name": (comfy.samplers.KSampler.SAMPLERS,),"scheduler": (comfy.samplers.KSampler.SCHEDULERS,)}}

    def get_samsched(self, sampler_name, scheduler):
        return (sampler_name, scheduler, )
            
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class Menu_Disable_Enable:
    match = ["Set to Disable","Set to Enable"]

    CATEGORY = 'JPS Nodes/Menu Items'
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

class Menu_Enable_Disable:
    match = ["Set to Enable","Set to Disable"]

    CATEGORY = 'JPS Nodes/Menu Items'
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

NODE_CLASS_MAPPINGS = {
    "SDXL Resolutions (JPS)": SDXL_Resolutions,
    "SDXL Basic Settings (JPS)": SDXL_Basic_Settings,
    "SDXL Additional Settings (JPS)": SDXL_Additional_Settings,
    "SDXL Recommended Resolution Calc (JPS)": SDXL_Recommended_Resolution_Calc,
    "Math Resolution Multiply (JPS)": Math_Resolution_Multiply,
    "Math Largest Int (JPS)": Math_Largest_Integer,
    "Math Multiply Int Int (JPS)": Math_Multiply_INT_INT,
    "Math Multiply Int Float (JPS)": Math_Multiply_INT_FLOAT,
    "Math Multiply Float Float (JPS)": Math_Multiply_FLOAT_FLOAT,
    "Switch Generation Mode (JPS)": Switch_Generation_Mode,
    "Switch Generation Mode 4in1 (JPS)": Switch_Generation_Mode_4in1,
    "Switch Revision Mode (JPS)": Switch_Revision_Mode,
    "Switch IP Adapter Mode (JPS)": Switch_IP_Adapter_Mode,
    "Menu Sampler Scheduler (JPS)": Menu_Sampler_Scheduler,
    "Menu Disable Enable Switch (JPS)": Menu_Disable_Enable,
    "Menu Enable Disable Switch (JPS)": Menu_Enable_Disable,
}
