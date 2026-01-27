import torch
import numpy as np
from PIL import Image

class img8seedvr2WHtrans:
    """
    为seedvr2节点转换目标尺寸的节点
    
    功能：
    1. target_short模式：用户输入直接向上矫正到能被8整除
    2. target_long模式：用原始值计算比例，结果四舍五入后再向上矫正
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_num": ("INT", {
                    "default": 4096,
                    "min": 8,
                    "max": 16384,
                    "step": 8
                }),
                "target_mode": (["target_long", "target_short"], {
                    "default": "target_long"
                }),
            }
        }
    
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seedvr2_short_side",)
    FUNCTION = "calculate"
    CATEGORY = "image/processing"
    DESCRIPTION = "为seedvr2节点转换目标尺寸参数"

    def calculate(self, image, target_num, target_mode):
        # 函数：向上矫正到能被8整除
        def round_up_to_multiple_of_8(value):
            return ((value + 7) // 8) * 8
        
        # 函数：检查是否能被8整除
        def is_multiple_of_8(value):
            return value % 8 == 0
        
        # 1. 如果是target_short模式，直接对用户输入向上矫正
        if target_mode == "target_short":
            corrected_output = round_up_to_multiple_of_8(target_num)
            print(f"[img8seedvr2WHtrans] target_short模式: 输入{target_num} -> 输出{corrected_output}")
            return (corrected_output,)
        
        # 2. 如果是target_long模式
        # 获取图像尺寸
        batch_size, height, width, channels = image.shape
        # 取第一张图片的尺寸（通常batch_size=1）
        h = int(height)
        w = int(width)
        
        # 计算原图的长边和短边
        long_side = max(w, h)
        short_side = min(w, h)
        
        # 如果是正方形图像
        if long_side == short_side:
            # 直接对用户输入向上矫正
            corrected_output = round_up_to_multiple_of_8(target_num)
            print(f"[img8seedvr2WHtrans] 正方形图像: 输入{target_num} -> 输出{corrected_output}")
            return (corrected_output,)
        
        # 使用用户输入的原始值（不矫正）进行计算
        # 计算：target_num × 原短边 ÷ 原长边
        float_output = target_num * short_side / long_side
        
        # 四舍五入到最接近的整数
        rounded_output = round(float_output)
        
        # 检查四舍五入后的结果是否能被8整除
        if is_multiple_of_8(rounded_output):
            final_output = rounded_output
        else:
            # 如果不能被8整除，向上矫正
            final_output = round_up_to_multiple_of_8(rounded_output)
        
        # 确保输出至少为8（最小有效值）
        final_output = max(8, final_output)
        
        # 调试信息
        print(f"[img8seedvr2WHtrans] 原图尺寸: {w}x{h}")
        print(f"[img8seedvr2WHtrans] 原长边: {long_side}, 原短边: {short_side}")
        print(f"[img8seedvr2WHtrans] 计算: {target_num} × {short_side} ÷ {long_side} = {float_output:.2f}")
        print(f"[img8seedvr2WHtrans] 四舍五入: {rounded_output}, 最终输出: {final_output}")
        print(f"[img8seedvr2WHtrans] 最终长边: ≈{final_output * long_side / short_side:.0f}")
        
        return (final_output,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "img8seedvr2WHtrans": img8seedvr2WHtrans
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "img8seedvr2WHtrans": "Image to seedvr2 WH Transformer"
}