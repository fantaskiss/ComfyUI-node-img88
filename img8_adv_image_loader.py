# 保存为: ComfyUI/custom_nodes/img8_adv_image_loader.py
import hashlib
import os
import folder_paths
import numpy as np
import torch
import node_helpers
from PIL import Image, ImageOps, ImageSequence

class Img8AdvImageLoader:
    """高级图像加载器 - 支持完整路径输入，输出原始真实路径"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入完整图片路径，如：C:/Users/name/Pictures/image.jpg"
                }),
            },
        }
    
    CATEGORY = "utils"
    
    # 关键修正：恢复PATH类型输出，同时提供STRING类型
    RETURN_TYPES = ("IMAGE", "PATH", "STRING")
    RETURN_NAMES = ("image", "path", "path_string")
    FUNCTION = "load_image"

    def load_image(self, image_path):
        """从完整路径加载图像"""
        
        # 验证路径
        if not image_path or not os.path.exists(image_path):
            raise FileNotFoundError(f"图片路径不存在: {image_path}")
        
        # 验证文件格式
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.tif'}
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in valid_extensions:
            raise ValueError(f"不支持的图片格式: {file_ext}。支持: {', '.join(valid_extensions)}")
        
        # 使用原始完整路径
        original_path = os.path.abspath(image_path)
        
        # 加载图像（简化版，无遮罩处理）
        img = node_helpers.pillow(Image.open, original_path)
        img = node_helpers.pillow(ImageOps.exif_transpose, img)
        
        # 转换为RGB和Tensor格式
        if img.mode == "I":
            img = img.point(lambda i: i * (1 / 255))
        
        image = img.convert("RGB")
        image_np = np.array(image).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]
        
        # 关键：第一个路径输出保持为PATH类型对象
        # 第二个路径输出为STRING类型
        return (image_tensor, original_path, original_path)

    @classmethod
    def IS_CHANGED(cls, image_path):
        """用于检测文件是否更改（缓存机制）"""
        if not image_path or not os.path.exists(image_path):
            return ""
        
        m = hashlib.sha256()
        with open(image_path, "rb") as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(cls, image_path):
        """验证输入"""
        if not image_path:
            return "图片路径不能为空"
        
        if not os.path.exists(image_path):
            return f"文件不存在: {image_path}"
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in valid_extensions:
            return f"不支持的文件格式: {file_ext}"
        
        return True

# 注册节点
NODE_CLASS_MAPPINGS = {
    "Img8AdvImageLoader": Img8AdvImageLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Img8AdvImageLoader": "🖼️img8:qwenimgloader4realpath"
}