import torch
import math

class img8x:
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
                "multiple": ("INT", {"default": 64, "min": 1, "max": 1024, "step": 1}), # 新增输入：边长倍数
            },
            "optional": {
                "mask_opt": ("MASK",),  # 新增可选遮罩输入
            }
        }
    # 修改 RETURN_TYPES，添加 INT 类型用于输出 x 和 y 坐标
    RETURN_TYPES = ("IMAGE", "MASK", "MASK", "INT", "INT")
    # 修改 RETURN_NAMES，添加对应的名称
    RETURN_NAMES = ("image", "outpaint_mask", "processed_mask", "x", "y")
    FUNCTION = "expand_image"
    CATEGORY = "image"

    def expand_image(self, image, feather, max_pixels, multiple, mask_opt=None):
        # 第一步：获取原始图像尺寸
        batch_size, orig_h, orig_w, channels = image.shape
        orig_w, orig_h = int(orig_w), int(orig_h)
        
        # 计算满足指定倍数的目标尺寸
        def round_to_multiple(x, mult):
            return ((x + mult - 1) // mult) * mult
            
        # 计算原始图像扩展后的尺寸 (使用新的 multiple 参数)
        W = round_to_multiple(orig_w, multiple)
        H = round_to_multiple(orig_h, multiple)
        
        # 初始化缩放标志和坐标
        was_resized = False
        x, y = 0, 0 # 初始化 x, y 坐标
        
        # 第二步：检查像素数是否超过限制
        if W * H > max_pixels:
            was_resized = True
            # 计算缩放比例
            scale_factor = math.sqrt(max_pixels / (W * H))
            # 计算缩放后的尺寸（保持宽高比）
            new_w = max(multiple, int(orig_w * scale_factor))
            new_h = max(multiple, int(orig_h * scale_factor))
            # 确保缩放后尺寸是指定倍数
            new_w = round_to_multiple(new_w, multiple)
            new_h = round_to_multiple(new_h, multiple)
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
        if not was_resized and (W > orig_w or H > orig_h):
            x = (W - orig_w) // 2
            y = (H - orig_h) // 2
            
        # 如果缩放了，则 x, y 保持为 0，因为图像直接适应目标尺寸
        
        # 第四步：创建新图像
        new_image = torch.zeros((batch_size, H, W, channels), dtype=image.dtype, device=image.device)
        
        # 第五步：将原始图像（或缩放后的图像）放置到新图像指定位置
        new_image[:, y:y+orig_h, x:x+orig_w, :] = image
        
        # 第六步：创建遮罩
        mask = torch.ones((batch_size, H, W), dtype=torch.float32, device=image.device)
        # 内部区域为0（原始图像区域）
        mask[:, y:y+orig_h, x:x+orig_w] = 0
        
        # 处理输入遮罩（如果有）
        processed_mask = torch.zeros((batch_size, H, W), dtype=torch.float32, device=image.device)
        if mask_opt is not None:
            # 确保遮罩维度正确
            if mask_opt.dim() == 2:
                mask_opt = mask_opt.unsqueeze(0)  # [1, H, W]
            elif mask_opt.dim() == 3:
                # 检查批次大小是否匹配
                if mask_opt.size(0) != batch_size:
                    # 如果批次不匹配，取前 batch_size 个或复制第一个（取决于具体情况，这里假设输入批次是1或匹配的）
                    if mask_opt.size(0) == 1:
                         mask_opt = mask_opt.repeat(batch_size, 1, 1)
                    else:
                         mask_opt = mask_opt[:batch_size] # 截取匹配的批次
            # 将遮罩放置到指定位置
            processed_mask[:, y:y+orig_h, x:x+orig_w] = mask_opt[:, :orig_h, :orig_w]
            
        # 应用羽化
        if feather > 0:
            # 创建羽化遮罩
            feathered_mask = torch.ones((H, W), dtype=torch.float32, device=image.device)
            # 顶部羽化
            if y > 0:
                top_feather_len = min(feather, y)
                if top_feather_len > 0:
                    top_feather = torch.linspace(1, 0, top_feather_len, device=feathered_mask.device).view(top_feather_len, 1)
                    top_feather = top_feather.repeat(1, W)
                    feathered_mask[y-top_feather_len:y, :] = top_feather
            # 底部羽化
            if y + orig_h < H:
                bottom_feather_len = min(feather, H - (y + orig_h))
                if bottom_feather_len > 0:
                    bottom_feather = torch.linspace(0, 1, bottom_feather_len, device=feathered_mask.device).view(bottom_feather_len, 1)
                    bottom_feather = bottom_feather.repeat(1, W)
                    feathered_mask[y+orig_h:y+orig_h+bottom_feather_len, :] = bottom_feather
            # 左侧羽化
            if x > 0:
                left_feather_len = min(feather, x)
                if left_feather_len > 0:
                    left_feather = torch.linspace(1, 0, left_feather_len, device=feathered_mask.device).view(1, left_feather_len)
                    left_feather = left_feather.repeat(H, 1)
                    feathered_mask[:, x-left_feather_len:x] = left_feather
            # 右侧羽化
            if x + orig_w < W:
                 right_feather_len = min(feather, W - (x + orig_w))
                 if right_feather_len > 0:
                    right_feather = torch.linspace(0, 1, right_feather_len, device=feathered_mask.device).view(1, right_feather_len)
                    right_feather = right_feather.repeat(H, 1)
                    feathered_mask[:, x+orig_w:x+orig_w+right_feather_len] = right_feather
            # 应用羽化到所有批次
            mask = mask * feathered_mask.unsqueeze(0) # [1, H, W] * [1, H, W] -> [1, H, W], 然后广播到 [B, H, W]
            
        # 返回新图像、遮罩、处理后的遮罩以及原始图像在新图像中的坐标 x, y
        return (new_image, mask, processed_mask, x, y)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "img8x": img8x
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "img8x": "img8x"
}