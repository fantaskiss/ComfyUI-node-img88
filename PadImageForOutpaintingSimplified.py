import torch
import math
from PIL import Image, ImageOps

class PadImageForOutpaintingSimplified:
    """
    简化版的图片外扩节点，带最大像素限制功能，支持遮罩同步处理
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "feather": ("INT", {"default": 40, "min": 0, "max": 0xffffffff, "step": 1}),
                "max_pixels": ("INT", {"default": 768432, "min": 64, "max": 0xffffffff, "step": 1}),
            },
            "optional": {
                "mask_opt": ("MASK",),  # 新增可选遮罩输入
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "MASK")
    RETURN_NAMES = ("image", "outpaint_mask", "processed_mask")
    FUNCTION = "expand_image"
    CATEGORY = "image"
    
    def expand_image(self, image, feather, max_pixels, mask_opt=None):
        # 第一步：获取原始图像尺寸
        batch_size, orig_h, orig_w, channels = image.shape
        orig_w, orig_h = int(orig_w), int(orig_h)
        
        # 计算满足64倍数的目标尺寸
        def round_to_64(x):
            return ((x + 63) // 64) * 64
        
        # 计算原始图像扩展后的尺寸
        W = round_to_64(orig_w)
        H = round_to_64(orig_h)
        
        # 第二步：检查像素数是否超过限制
        if W * H > max_pixels:
            # 计算缩放比例
            scale_factor = math.sqrt(max_pixels / (W * H))
            
            # 计算缩放后的尺寸（保持宽高比）
            new_w = max(64, int(orig_w * scale_factor))
            new_h = max(64, int(orig_h * scale_factor))
            
            # 确保缩放后尺寸是64的倍数
            new_w = round_to_64(new_w)
            new_h = round_to_64(new_h)
            
            # 使用双线性插值缩放图像
            image_permuted = image.permute(0, 3, 1, 2)  # [B, C, H, W]
            scaled_image = torch.nn.functional.interpolate(
                image_permuted,
                size=(new_h, new_w),
                mode='bilinear',
                align_corners=False
            )
            image = scaled_image.permute(0, 2, 3, 1)  # 恢复为 [B, H, W, C]
            
            # 如果有输入遮罩，同样缩放遮罩
            if mask_opt is not None:
                # 处理遮罩维度 (可能为2D或3D)
                if mask_opt.dim() == 2:
                    mask_opt = mask_opt.unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]
                elif mask_opt.dim() == 3:
                    mask_opt = mask_opt.unsqueeze(1)  # [B, 1, H, W]
                
                scaled_mask = torch.nn.functional.interpolate(
                    mask_opt,
                    size=(new_h, new_w),
                    mode='bilinear',
                    align_corners=False
                )
                # 恢复原始维度
                if scaled_mask.size(1) == 1:
                    scaled_mask = scaled_mask.squeeze(1)  # [B, H, W]
                mask_opt = scaled_mask
            
            # 更新尺寸信息
            orig_w, orig_h = new_w, new_h
            W, H = new_w, new_h  # 缩放后不需要再扩展
        
        # 第三步：计算填充量（仅当未缩放时）
        if W > orig_w or H > orig_h:
            x = (W - orig_w) // 2
            y = (H - orig_h) // 2
        else:
            x, y = 0, 0
        
        # 第四步：创建新图像
        new_image = torch.zeros((batch_size, H, W, channels))
        
        # 第五步：将原始图像放置到新图像中心
        new_image[:, y:y+orig_h, x:x+orig_w, :] = image
        
        # 第六步：创建遮罩
        mask = torch.ones((batch_size, H, W))
        
        # 内部区域为0（原始图像区域）
        mask[:, y:y+orig_h, x:x+orig_w] = 0
        
        # 处理输入遮罩（如果有）
        processed_mask = torch.zeros((batch_size, H, W))
        if mask_opt is not None:
            # 确保遮罩维度正确
            if mask_opt.dim() == 2:
                mask_opt = mask_opt.unsqueeze(0)  # [1, H, W]
            elif mask_opt.dim() == 3:
                # 检查批次大小是否匹配
                if mask_opt.size(0) != batch_size:
                    mask_opt = mask_opt[:batch_size]  # 截取匹配的批次
            
            # 将遮罩放置到中心
            processed_mask[:, y:y+orig_h, x:x+orig_w] = mask_opt[:, :orig_h, :orig_w]
        
        # 应用羽化
        if feather > 0:
            # 创建羽化遮罩
            feathered_mask = torch.ones((H, W))
            
            # 顶部羽化
            if y > 0:
                top_feather = torch.linspace(1, 0, feather).view(feather, 1)
                top_feather = top_feather.repeat(1, W)
                feathered_mask[:y, :] = 1
                feathered_mask[max(0, y-feather):y, :] = top_feather[max(0, feather-y):, :]
            
            # 底部羽化
            if y + orig_h < H:
                bottom_feather = torch.linspace(0, 1, feather).view(feather, 1)
                bottom_feather = bottom_feather.repeat(1, W)
                feathered_mask[y+orig_h:, :] = 1
                feathered_mask[y+orig_h:min(H, y+orig_h+feather), :] = bottom_feather[:min(feather, H - (y+orig_h)), :]
            
            # 左侧羽化
            if x > 0:
                left_feather = torch.linspace(1, 0, feather).view(1, feather)
                left_feather = left_feather.repeat(H, 1)
                feathered_mask[:, :x] = 1
                feathered_mask[:, max(0, x-feather):x] = left_feather[:, max(0, feather-x):]
            
            # 右侧羽化
            if x + orig_w < W:
                right_feather = torch.linspace(0, 1, feather).view(1, feather)
                right_feather = right_feather.repeat(H, 1)
                feathered_mask[:, x+orig_w:] = 1
                feathered_mask[:, x+orig_w:min(W, x+orig_w+feather)] = right_feather[:, :min(feather, W - (x+orig_w))]
            
            # 应用羽化到所有批次
            mask = mask * feathered_mask.unsqueeze(0)
        
        return (new_image, mask, processed_mask)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PadImageForOutpaintingSimplified": PadImageForOutpaintingSimplified
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PadImageForOutpaintingSimplified": "Pad Image for Outpainting (Simplified)"
}