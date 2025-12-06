# 保存为: ComfyUI/custom_nodes/img8txtsaver.py
import os
import time
from datetime import datetime

class Img8TxtSaver:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True, "default": ""}),
                "image_path": ("STRING", {"forceInput": True, "default": ""}),
                "add_timestamp": (["disabled", "enabled"], {"default": "disabled"}),
            },
        }
    
    RETURN_TYPES = ()
    FUNCTION = "save_text"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    def save_text(self, text, image_path, add_timestamp="disabled"):
        # 验证输入
        if not text or not text.strip():
            print("⚠️ 警告：文本内容为空，不保存文件")
            return ()
        
        if not image_path or not os.path.exists(image_path):
            print(f"⚠️ 警告：图片路径不存在或为空 '{image_path}'")
            return ()
        
        # 获取原文件信息
        dir_path = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # 构建文件名
        if add_timestamp == "enabled":
            # 生成时间戳：格式为 _YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
            txt_filename = f"{base_name}{timestamp}.txt"
        else:
            txt_filename = f"{base_name}.txt"
        
        # 完整的保存路径
        txt_path = os.path.join(dir_path, txt_filename)
        
        try:
            # 确保目录存在
            os.makedirs(dir_path, exist_ok=True)
            
            # 写入文件
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text.strip())
            
            print(f"✅ 文本已保存到: {txt_path}")
            
            # 如果启用了时间戳，也打印原始文件名用于参考
            if add_timestamp == "enabled":
                print(f"📝 原始文件名: {base_name}")
                
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return ()

# 注册节点
NODE_CLASS_MAPPINGS = {
    "img8txtsaver": Img8TxtSaver
}

# 显示名映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "img8txtsaver": "📝 img8txtsaver：save the text to file"
}