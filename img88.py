from PIL import Image
import torch
import numpy as np

class ImagePaddingProcessor:
    """
    ComfyUI自定义节点：智能图像处理
    功能：
    1. 自动缩放大图像（可配置）
    2. 边缘像素扩展（多种模式）
    3. 支持透明通道/遮罩处理
    4. 遮罩输入接口
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "edge_extend": (["repeat", "mirror", "black"], {"default": "repeat"}),
                "resize_large_image": ("BOOLEAN", {"default": True}),
                "max_pixels": ("INT", {"default": 786432, "min": 1, "max": 10**7, "step": 1})
            },
            "optional": {
                "mask": ("MASK",),  # 新增遮罩输入接口
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")  # 输出图像和遮罩
    RETURN_NAMES = ("padded_image", "padded_mask")
    FUNCTION = "process_image"
    CATEGORY = "image/processing"

    def process_image(self, image, edge_extend="repeat", resize_large_image=True, max_pixels=786432, mask=None):
        # 输入图像张量形状为 [batch, height, width, channels]
        # 我们处理批次中的第一张图像
        image_np = image[0].cpu().numpy()
        orig_channels = image_np.shape[2]
        
        # 处理遮罩
        if mask is not None:
            # 如果提供了外部遮罩，使用它（取批次中的第一张）
            mask_np = mask[0].cpu().numpy()
            if mask_np.ndim == 3 and mask_np.shape[0] == 1:
                mask_np = mask_np[0]  # 从(1,H,W)变为(H,W)
            elif mask_np.ndim == 3 and mask_np.shape[0] > 1:
                mask_np = mask_np[0]  # 取第一个通道
            elif mask_np.ndim == 2:
                pass  # 已经是(H,W)
            else:
                raise ValueError(f"遮罩的维度无效: {mask_np.shape}")
        elif orig_channels == 4:
            # 没有外部遮罩但图像有Alpha通道，使用Alpha作为遮罩
            mask_np = image_np[:, :, 3]
        else:
            # 没有遮罩输入也没有Alpha通道，创建全白遮罩
            mask_np = np.ones(image_np.shape[:2], dtype=np.float32)
        
        # 确保遮罩值在0-1范围内
        mask_np = np.clip(mask_np, 0.0, 1.0)
        
        # 处理RGB图像
        if orig_channels >= 3:
            rgb_np = image_np[:, :, :3] * 255.0
        else:
            # 单通道图像，复制为RGB
            rgb_np = np.stack([image_np[:, :, 0]]*3, axis=2) * 255.0
        
        # 转换为PIL图像
        pil_image = Image.fromarray(rgb_np.astype('uint8'), 'RGB')
        orig_width, orig_height = pil_image.size
        
        # 处理遮罩PIL图像
        mask_pil = Image.fromarray((mask_np * 255).astype('uint8'), 'L')
        
        # 缩放图像（如果开启且超过阈值）
        if resize_large_image and (orig_width * orig_height > max_pixels):
            # 计算缩放比例（以短边为基准）
            short_side = min(orig_width, orig_height)
            scale = min(1.0, np.sqrt(max_pixels / (orig_width * orig_height)))
            
            # 计算新尺寸
            new_width = int(round(orig_width * scale))
            new_height = int(round(orig_height * scale))
            
            # 高质量缩放
            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
            mask_pil = mask_pil.resize((new_width, new_height), Image.LANCZOS)  # 同时缩放遮罩
            print(f"图像已从({orig_width}x{orig_height})缩放至({new_width}x{new_height})")
            orig_width, orig_height = new_width, new_height
        
        # 计算需要添加的像素量（保证8的倍数）
        pad_w = (8 - (orig_width % 8)) % 8
        pad_h = (8 - (orig_height % 8)) % 8
        new_width = orig_width + pad_w
        new_height = orig_height + pad_h
        
        # 创建新图像（根据模式填充边缘）
        if edge_extend == "black":
            new_image = Image.new("RGB", (new_width, new_height), (0, 0, 0))
            # 对于遮罩，黑色填充表示透明区域
            new_mask = Image.new("L", (new_width, new_height), 0)
        else:
            # 临时扩展图像（比实际需要大2倍边缘）
            temp_img = Image.new("RGB", (orig_width + pad_w*2, orig_height + pad_h*2))
            temp_img.paste(pil_image, (pad_w, pad_h))
            
            # 临时扩展遮罩
            temp_mask = Image.new("L", (orig_width + pad_w*2, orig_height + pad_h*2), 0)
            temp_mask.paste(mask_pil, (pad_w, pad_h))
            
            # 获取边缘
            left = pil_image.crop((0, 0, 1, orig_height))
            right = pil_image.crop((orig_width-1, 0, orig_width, orig_height))
            top = pil_image.crop((0, 0, orig_width, 1))
            bottom = pil_image.crop((0, orig_height-1, orig_width, orig_height))
            
            # 获取遮罩边缘
            mask_left = mask_pil.crop((0, 0, 1, orig_height))
            mask_right = mask_pil.crop((orig_width-1, 0, orig_width, orig_height))
            mask_top = mask_pil.crop((0, 0, orig_width, 1))
            mask_bottom = mask_pil.crop((0, orig_height-1, orig_width, orig_height))
            
            # 根据模式填充边缘
            if edge_extend == "repeat":
                # 水平方向
                for x in range(pad_w):
                    # 左侧
                    temp_img.paste(left, (x, pad_h, x+1, pad_h+orig_height))
                    temp_mask.paste(mask_left, (x, pad_h, x+1, pad_h+orig_height))
                    # 右侧
                    temp_img.paste(right, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                    temp_mask.paste(mask_right, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                # 垂直方向
                for y in range(pad_h):
                    # 顶部
                    temp_img.paste(top, (pad_w, y, pad_w+orig_width, y+1))
                    temp_mask.paste(mask_top, (pad_w, y, pad_w+orig_width, y+1))
                    # 底部
                    temp_img.paste(bottom, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
                    temp_mask.paste(mask_bottom, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
            elif edge_extend == "mirror":
                # 水平镜像
                left_flip = left.transpose(Image.FLIP_LEFT_RIGHT)
                right_flip = right.transpose(Image.FLIP_LEFT_RIGHT)
                mask_left_flip = mask_left.transpose(Image.FLIP_LEFT_RIGHT)
                mask_right_flip = mask_right.transpose(Image.FLIP_LEFT_RIGHT)
                
                # 水平填充
                for x in range(pad_w):
                    # 左侧 - 交替镜像
                    if x % 2 == 0:
                        temp_img.paste(left, (x, pad_h, x+1, pad_h+orig_height))
                        temp_mask.paste(mask_left, (x, pad_h, x+1, pad_h+orig_height))
                    else:
                        temp_img.paste(left_flip, (x, pad_h, x+1, pad_h+orig_height))
                        temp_mask.paste(mask_left_flip, (x, pad_h, x+1, pad_h+orig_height))
                    
                    # 右侧 - 交替镜像
                    if x % 2 == 0:
                        temp_img.paste(right, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                        temp_mask.paste(mask_right, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                    else:
                        temp_img.paste(right_flip, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                        temp_mask.paste(mask_right_flip, (pad_w+orig_width+x, pad_h, pad_w+orig_width+x+1, pad_h+orig_height))
                
                # 垂直镜像
                top_flip = top.transpose(Image.FLIP_TOP_BOTTOM)
                bottom_flip = bottom.transpose(Image.FLIP_TOP_BOTTOM)
                mask_top_flip = mask_top.transpose(Image.FLIP_TOP_BOTTOM)
                mask_bottom_flip = mask_bottom.transpose(Image.FLIP_TOP_BOTTOM)
                
                # 垂直填充
                for y in range(pad_h):
                    # 顶部 - 交替镜像
                    if y % 2 == 0:
                        temp_img.paste(top, (pad_w, y, pad_w+orig_width, y+1))
                        temp_mask.paste(mask_top, (pad_w, y, pad_w+orig_width, y+1))
                    else:
                        temp_img.paste(top_flip, (pad_w, y, pad_w+orig_width, y+1))
                        temp_mask.paste(mask_top_flip, (pad_w, y, pad_w+orig_width, y+1))
                    
                    # 底部 - 交替镜像
                    if y % 2 == 0:
                        temp_img.paste(bottom, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
                        temp_mask.paste(mask_bottom, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
                    else:
                        temp_img.paste(bottom_flip, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
                        temp_mask.paste(mask_bottom_flip, (pad_w, pad_h+orig_height+y, pad_w+orig_width, pad_h+orig_height+y+1))
            
            # 裁剪出实际需要的区域
            new_image = temp_img.crop((pad_w, pad_h, pad_w + new_width, pad_h + new_height))
            new_mask = temp_mask.crop((pad_w, pad_h, pad_w + new_width, pad_h + new_height))
        
        # 居中放置原图和遮罩
        paste_x = (new_width - orig_width) // 2
        paste_y = (new_height - orig_height) // 2
        new_image.paste(pil_image, (paste_x, paste_y))
        new_mask.paste(mask_pil, (paste_x, paste_y))
        
        # 转换为张量
        image_tensor = torch.from_numpy(
            np.array(new_image).astype(np.float32) / 255.0
        ).unsqueeze(0)  # 添加批次维度
        
        mask_tensor = torch.from_numpy(
            np.array(new_mask).astype(np.float32) / 255.0
        ).unsqueeze(0)  # 添加批次维度

        return (image_tensor, mask_tensor)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImagePaddingProcessor": ImagePaddingProcessor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagePaddingProcessor": "img8🖼️"
}