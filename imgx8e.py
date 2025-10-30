import math
import comfy

def gcd(a, b):
    """计算两个数的最大公约数"""
    while b:
        a, b = b, a % b
    return a

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
                        "flux": ["flux_ratio", "flip"],
                        "wan": ["wan_option", "flip"],
                        "qwen": ["qwen_ratio", "flip"]
                    }
                }),
                # 自定义模式参数
                "custom_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "custom_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                # flux模式参数
                "flux_ratio": ([
                    "1:1 (1152x1152)",
                    "2:3 (960x1440)",
                    "3:4 (1024x1344)",
                    "10:16 (896x1504)",
                    "9:16 (864x1568)"
                ], {"default": "1:1 (1152x1152)"}),
                # wan模式参数 - 直接提供所有分辨率选项
                "wan_option": ([
                    # 480p选项, 最大像素量 399360
                    "9:16 (480×832)",
                    "1:1 (624×624)",
                    # 540p选项, 最大像素量 522240
                    "9:16 (544×960)",
                    "1:1 (720×720)",
                    # 720p选项, 最大像素量 921600
                    "9:16 (720×1280)",
                    "1:1 (960×960)",
                    "3:4 (832×1088)",
                    # 1080p选项, 最大像素量 2073600
                    "9:16 (1080×1920)",
                    "1:1 (1440×1440)",
                    "3:4 (1248×1632)"
                ], {"default": "9:16 (480×832)"}), # 更新默认值
                # qwen模式参数
                "qwen_ratio": ([
                    "1:1 (1328×1328)",
                    "9:16 (928×1664)",
                    "3:4 (1140×1472)",
                    "4:5 (1152×1440)",
                    "10:16 (1056×1664)",
                    "2:3 (1056×1600)"
                ], {"default": "1:1 (1328×1328)"}),
            },
            "optional": {
                "flip": ("BOOLEAN", {"default": False, "label": "反转分辨率"}), # 添加反转分辨率开关
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "STRING") # 增加STRING类型输出
    RETURN_NAMES = ("宽", "高", "批次", "信息") # 更新返回名称
    FUNCTION = "calculate_size"
    CATEGORY = "image"

    def calculate_size(self, batch_size, mode,
                     custom_width=1024, custom_height=1024, # 为自定义模式参数提供默认值
                     flux_ratio="1:1 (1152x1152)", # 为flux模式参数提供默认值
                     wan_option="9:16 (480×832)", # 为wan模式参数提供默认值
                     qwen_ratio="1:1 (1328×1328)", # 为qwen模式参数提供默认值
                     flip=False): # 获取反转开关的值
        # 根据模式计算宽高
        if mode == "自定义":
            width, height = custom_width, custom_height
        elif mode == "flux":
            # 直接从选项字符串中提取分辨率
            if "(" in flux_ratio and ")" in flux_ratio:
                resolution_part = flux_ratio.split("(")[-1].split(")")[0]
                if "x" in resolution_part: # 检查是 x 还是 ×
                    wh_parts = resolution_part.split("x")
                elif "×" in resolution_part:
                    wh_parts = resolution_part.split("×")
                else:
                    wh_parts = [] # 如果格式都不匹配

                if len(wh_parts) == 2:
                    try:
                        width = int(wh_parts[0])
                        height = int(wh_parts[1])
                    except ValueError:
                        width, height = 1152, 1152 # 解析失败时的默认值
                else:
                    width, height = 1152, 1152 # 格式不匹配时的默认值
            else:
                width, height = 1152, 1152 # 格式不匹配时的默认值

        elif mode == "wan":
            # 直接从选项字符串中提取分辨率
            if "(" in wan_option and ")" in wan_option:
                resolution_part = wan_option.split("(")[-1].split(")")[0]
                if "×" in resolution_part:
                    wh_parts = resolution_part.split("×")
                elif "x" in resolution_part:
                    wh_parts = resolution_part.split("x")
                else:
                    wh_parts = []

                if len(wh_parts) == 2:
                    try:
                        width = int(wh_parts[0])
                        height = int(wh_parts[1])
                    except ValueError:
                        width, height = 480, 832 # 解析失败时的默认值 (使用默认选项)
                else:
                    width, height = 480, 832 # 格式不匹配时的默认值
            else:
                width, height = 480, 832 # 格式不匹配时的默认值

        elif mode == "qwen":
            # 直接从选项字符串中提取分辨率
            if "(" in qwen_ratio and ")" in qwen_ratio:
                resolution_part = qwen_ratio.split("(")[-1].split(")")[0]
                if "×" in resolution_part:
                    wh_parts = resolution_part.split("×")
                elif "x" in resolution_part:
                    wh_parts = resolution_part.split("x")
                else:
                    wh_parts = []

                if len(wh_parts) == 2:
                    try:
                        width = int(wh_parts[0])
                        height = int(wh_parts[1])
                    except ValueError:
                        width, height = 1328, 1328 # 解析失败时的默认值
                else:
                    width, height = 1328, 1328 # 格式不匹配时的默认值
            else:
                width, height = 1328, 1328 # 格式不匹配时的默认值

        # 确保最小值
        width = max(64, width)
        height = max(64, height)

        # 如果启用了反转，则交换宽高
        if flip:
            width, height = height, width

        # 计算总像素数
        total_pixels = width * height

        # --- 计算近似长宽比 ---
        if mode == "自定义":
            # 对于自定义模式，计算最简整数比
            common_divisor = gcd(width, height) # 使用交换后的宽高计算比例
            if common_divisor > 0:
                aspect_ratio = f"{width // common_divisor}:{height // common_divisor}"
            else:
                aspect_ratio = "1:1" # 防止除零错误
        else:
            # 对于预设模式，从原始选项字符串中提取
            source_string = {
                "flux": flux_ratio,
                "wan": wan_option,
                "qwen": qwen_ratio
            }.get(mode, "")
            # 提取冒号前的部分作为长宽比
            if ":" in source_string:
                original_aspect_ratio_str = source_string.split(":")[0] + ":" + source_string.split(":", 1)[1].split()[0] # 提取原始比例字符串 "X:Y"
                original_parts = original_aspect_ratio_str.split(":")
                if len(original_parts) == 2:
                    if flip:
                        # 如果翻转，交换比例数字
                        aspect_ratio = f"{original_parts[1]}:{original_parts[0]}"
                    else:
                        # 否则，使用原始比例
                        aspect_ratio = original_aspect_ratio_str
                else:
                    aspect_ratio = "1:1" # 如果格式不匹配，默认为1:1
            else:
                aspect_ratio = "1:1" # 如果格式不匹配，默认为1:1

        # --- 构造信息字符串 ---
        info = f"模式: {mode} | 分辨率: {width}x{height} | 长宽比: {aspect_ratio} | 总像素: {total_pixels}"

        return (width, height, batch_size, info)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "imgx8e": imgx8e
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "imgx8e": "imgx8e 常见预设尺寸设置器"
}