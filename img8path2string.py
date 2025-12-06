# 保存为: ComfyUI/custom_nodes/img8path2string.py
import os

class Img8Path2String:
    """将PATH类型转换为STRING类型"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path_input": ("PATH", {"forceInput": True}),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("path_string", "filename")
    FUNCTION = "convert"
    CATEGORY = "utils"

    def convert(self, path_input):
        if not path_input:
            return ("", "")
        
        # 确保路径是字符串
        path_str = str(path_input)
        
        # 提取文件名（不含扩展名）
        filename = os.path.splitext(os.path.basename(path_str))[0]
        
        return (path_str, filename)

# 注册节点 - 使用img8path2string作为注册名
NODE_CLASS_MAPPINGS = {
    "img8path2string": Img8Path2String
}

# 显示名映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "img8path2string": "🔤 PATH to STRING (img8path2string)"
}