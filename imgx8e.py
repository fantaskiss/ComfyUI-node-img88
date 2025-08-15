import math
import comfy

class imgx8e:
    @classmethod
    def INPUT_TYPES(cls):
        # 定义所有可能的参数
        return {
            "required": {
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64, "step": 1}),
                "mode": (["flux", "qwen", "wan", "自定义"], {
                    "default": "自定义",
                    # 核心动态UI配置 - 定义每个模式对应的参数
                    "dynamic": {
                        "自定义": ["custom_width", "custom_height"],
                        "flux": ["flux_ratio", "flux_pixels"],
                        "wan": ["wan_option"],
                        "qwen": ["qwen_ratio"]
                    }
                }),
                # 自定义模式参数
                "custom_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "custom_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                # flux模式参数
                "flux_ratio": (["21:10", "16:9", "16:10", "4:3", "1:1"], {"default": "1:1"}),
                "flux_pixels": ("INT", {"default": 1048576, "min": 65536, "max": 16777216, "step": 65536}),
                # wan模式参数 - 直接提供所有分辨率选项
                "wan_option": ([
                    # 480p选项
                    "832×480 (16:9)", 
                    "480×832 (9:16)", 
                    "624×624 (1:1)",
                    # 720p选项
                    "1280×720 (16:9)", 
                    "720×1280 (9:16)", 
                    "960×960 (1:1)", 
                    "1088×832 (4:3)", 
                    "832×1088 (3:4)",
                    # 1080p选项
                    "1920×1080 (16:9)", 
                    "1080×1920 (9:16)", 
                    "1440×1440 (1:1)", 
                    "1632×1248 (4:3)", 
                    "1248×1632 (3:4)"
                ], {"default": "1280×720 (16:9)"}),
                # qwen模式参数 - 添加分辨率数值显示
                "qwen_ratio": ([
                    "1:1 (1328×1328)",
                    "16:9 (1664×928)",
                    "9:16 (928×1664)",
                    "4:3 (1472×1140)",
                    "3:4 (1140×1472)"
                ], {"default": "1:1 (1328×1328)"}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT")
    RETURN_NAMES = ("宽", "高", "批次")
    FUNCTION = "calculate_size"
    CATEGORY = "image"
    
    def calculate_size(self, batch_size, mode, 
                     custom_width, custom_height, 
                     flux_ratio, flux_pixels,
                     wan_option,
                     qwen_ratio):
        # 根据模式计算宽高
        if mode == "自定义":
            width, height = custom_width, custom_height
            
        elif mode == "flux":
            # 解析宽高比
            ratio_parts = flux_ratio.split(":")
            if len(ratio_parts) != 2:
                ratio_parts = ["1", "1"]
            ratio_w, ratio_h = float(ratio_parts[0]), float(ratio_parts[1])
            aspect_ratio = ratio_w / ratio_h
            
            # 计算初始尺寸
            area = flux_pixels
            height = int(math.sqrt(area / aspect_ratio))
            width = int(height * aspect_ratio)
            
            # 调整到64的倍数
            width = (width // 64) * 64
            height = (height // 64) * 64
            
            # 确保不超过像素容积
            while width * height > flux_pixels:
                if width > height:
                    width -= 64
                    height = int(width / aspect_ratio)
                else:
                    height -= 64
                    width = int(height * aspect_ratio)
                
                width = (width // 64) * 64
                height = (height // 64) * 64
                
                # 防止无限循环
                if width < 64 or height < 64:
                    width, height = 64, 64
                    break
                    
        elif mode == "wan":
            # 直接从选项字符串中提取分辨率数字
            # 查找第一个数字序列×数字序列的模式
            parts = wan_option.split("×")
            if len(parts) >= 2:
                # 提取宽度部分
                width_str = parts[0]
                # 提取高度部分（可能包含空格）
                height_str = parts[1].split(" ")[0]
                
                # 转换为整数
                try:
                    width = int(width_str)
                    height = int(height_str)
                except:
                    width, height = 1280, 720
            else:
                # 如果分割失败，使用默认值
                width, height = 1280, 720
            
        elif mode == "qwen":
            # 直接从选项字符串中提取分辨率
            # 使用简单字符串分割方法
            # 示例: "1:1 (1328×1328)"
            if "(" in qwen_ratio and ")" in qwen_ratio:
                # 提取括号内的内容
                resolution_part = qwen_ratio.split("(")[-1].split(")")[0]
                
                # 分割宽高
                if "×" in resolution_part:
                    wh_parts = resolution_part.split("×")
                    if len(wh_parts) == 2:
                        try:
                            width = int(wh_parts[0])
                            height = int(wh_parts[1])
                        except:
                            width, height = 1328, 1328
                    else:
                        width, height = 1328, 1328
                else:
                    width, height = 1328, 1328
            else:
                # 如果格式不匹配，使用默认值
                width, height = 1328, 1328
        
        # 确保最小值
        width = max(64, width)
        height = max(64, height)
        
        return (width, height, batch_size)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "imgx8e": imgx8e
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "imgx8e": "imgx8e 常见预设尺寸设置器"
}