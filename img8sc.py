import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np

class Img8sc:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 480, "min": 8, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 832, "min": 8, "max": 8192, "step": 1}),
                "scale_method": (["nearest", "bilinear", "lanczos"], {"default": "lanczos"}),
                "position": (["up", "left", "down", "right", "middle"], {"default": "middle"}),
            },
            "optional": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "process"
    CATEGORY = "image"

    def process(self, width, height, scale_method, position, image=None, mask=None):
        # 步骤1: 调整尺寸为8的倍数
        target_width = self.round_to_multiple_of_8(width)
        target_height = self.round_to_multiple_of_8(height)

        if image is not None:
            # 将tensor转换为PIL Image
            i = 255. * image[0].cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            orig_width, orig_height = img.size
            
            # 计算缩放比例，确保完全覆盖目标尺寸
            scale_w = target_width / orig_width
            scale_h = target_height / orig_height
            
            # 选择较大的缩放比例以确保完全覆盖
            scale = max(scale_w, scale_h)
            
            # 计算缩放后的尺寸
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            
            # 使用指定算法进行缩放
            if scale_method == "nearest":
                resample = Image.NEAREST
            elif scale_method == "bilinear":
                resample = Image.BILINEAR
            elif scale_method == "lanczos":
                resample = Image.LANCZOS
            
            img_resized = img.resize((new_width, new_height), resample)
            
            # 裁剪到目标尺寸
            img_cropped = self.crop_image(img_resized, target_width, target_height, position)
            
            # 转换回tensor
            img_out = np.array(img_cropped).astype(np.float32) / 255.0
            img_out = torch.from_numpy(img_out)[None,]
        else:
            img_out = torch.zeros((1, target_height, target_width, 3), dtype=torch.float32)
        
        if mask is not None:
            # 处理遮罩
            m = mask.squeeze().cpu().numpy()
            mask_pil = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8), mode="L")
            
            orig_mask_width, orig_mask_height = mask_pil.size
            
            # 按相同比例缩放遮罩
            scale_w = target_width / orig_mask_width
            scale_h = target_height / orig_mask_height
            scale = max(scale_w, scale_h)
            
            new_mask_width = int(orig_mask_width * scale)
            new_mask_height = int(orig_mask_height * scale)
            
            mask_resized = mask_pil.resize((new_mask_width, new_mask_height), resample)
            mask_cropped = self.crop_image(mask_resized, target_width, target_height, position)
            
            # 转换回tensor
            mask_out = np.array(mask_cropped).astype(np.float32) / 255.0
            mask_out = torch.from_numpy(mask_out)
        else:
            mask_out = torch.zeros((target_height, target_width), dtype=torch.float32)

        return (img_out, mask_out)

    def round_to_multiple_of_8(self, n):
        """将数字调整为最接近的8的倍数"""
        remainder = n % 8
        if remainder <= 4:
            return n - remainder
        else:
            return n + (8 - remainder)

    def crop_image(self, img, target_width, target_height, position):
        """根据位置裁剪图像"""
        orig_width, orig_height = img.size
        
        # 计算需要裁剪的区域
        delta_width = orig_width - target_width
        delta_height = orig_height - target_height
        
        if delta_width > 0:
            # 如果宽度超出，按位置裁剪
            if position in ["left", "up"]:  # up用于宽度裁剪时视为left
                left = 0
            elif position in ["right", "down"]:  # down用于宽度裁剪时视为right
                left = delta_width
            else:  # middle
                left = delta_width // 2
            right = left + target_width
        else:
            left = 0
            right = orig_width
        if delta_height > 0:
            # 如果高度超出，按位置裁剪
            if position in ["up", "left"]:  # left用于高度裁剪时视为up
                top = 0
            elif position in ["down", "right"]:  # right用于高度裁剪时视为down
                top = delta_height
            else:  # middle
                top = delta_height // 2
            bottom = top + target_height
        else:
            top = 0
            bottom = orig_height
        
        return img.crop((left, top, right, bottom))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "img8sc": Img8sc
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "img8sc": "img8sc (Image Scale & Crop)"
}