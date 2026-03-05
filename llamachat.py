import os
import sys
import gc
import json
import torch
import numpy as np
from PIL import Image, ImageDraw
import folder_paths
import comfy.model_management as mm

# ============================================================
# 【关键】从 ComfyUI-llama-cpp_vlm 导入共享存储类
# 文件夹名中的 - 在 Python 导入时自动转为 _
# ============================================================

def import_llama_storage():
    """动态导入 LLAMA_CPP_STORAGE"""
    
    # 获取 custom_nodes 目录
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    path = current_dir
    while path != os.path.dirname(path):
        if os.path.basename(path) == 'custom_nodes':
            break
        path = os.path.dirname(path)
    custom_nodes_dir = path
    
    # 确定节点目录路径
    node_dir_name = 'ComfyUI-llama-cpp_vlm'  # 实际文件夹名（带连字符）
    node_package_name = 'ComfyUI_llama_cpp_vlm'  # Python包名（下划线）
    
    node_dir_path = os.path.join(custom_nodes_dir, node_dir_name)
    nodes_file_path = os.path.join(node_dir_path, 'nodes.py')
    
    print(f"[llama-cpp-chat] Looking for nodes at: {nodes_file_path}")
    
    if not os.path.exists(nodes_file_path):
        print(f"[llama-cpp-chat] ERROR: nodes.py not found at {nodes_file_path}")
        return None
    
    # 方法1：直接添加到sys.path然后导入
    try:
        if node_dir_path not in sys.path:
            sys.path.insert(0, node_dir_path)
        
        # 尝试直接导入nodes模块
        import nodes as target_nodes
        if hasattr(target_nodes, 'LLAMA_CPP_STORAGE'):
            print("[llama-cpp-chat] Successfully imported via sys.path")
            return target_nodes.LLAMA_CPP_STORAGE
    except Exception as e:
        print(f"[llama-cpp-chat] Sys.path import failed: {e}")
    
    # 方法2：使用importlib，不依赖包名，直接加载文件 无效。
    try:
        import importlib.util
        import types
        
        # 创建模块
        spec = importlib.util.spec_from_file_location("llama_cpp_vlm_nodes", nodes_file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            
            # 添加必要的路径到模块的搜索路径
            if node_dir_path not in sys.path:
                sys.path.insert(0, node_dir_path)
            
            # 执行模块
            spec.loader.exec_module(module)
            
            if hasattr(module, 'LLAMA_CPP_STORAGE'):
                print("[llama-cpp-chat] Successfully imported via direct file loading")
                return module.LLAMA_CPP_STORAGE
    except Exception as e:
        print(f"[llama-cpp-chat] Direct file loading failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 方法3：尝试通过添加父目录来导入
    try:
        # 将custom_nodes目录添加到路径
        if custom_nodes_dir not in sys.path:
            sys.path.insert(0, custom_nodes_dir)
        
        # 尝试导入带下划线的包名
        import importlib
        module = importlib.import_module(f"{node_package_name}.nodes")
        if hasattr(module, 'LLAMA_CPP_STORAGE'):
            print("[llama-cpp-chat] Successfully imported via package name")
            return module.LLAMA_CPP_STORAGE
    except Exception as e:
        print(f"[llama-cpp-chat] Package import failed: {e}")
        print(" ✅ \033[92m[llama-cpp-chat] Package didn't import sucessful, but it can work, don't worry.\033[0m")
        print(" ✅ \033[92m[llama-cpp-chat] 节点未能成功加载，但可以运行^_^\033[0m")
    return None

# 执行导入
LLAMA_CPP_STORAGE = import_llama_storage()

# 备用类（导入失败时使用）
if LLAMA_CPP_STORAGE is None:
    print("[llama-cpp-chat] ERROR: Could not import LLAMA_CPP_STORAGE")
    class LLAMA_CPP_STORAGE:
        llm = None
        messages = {}
        sys_prompts = {}
        @classmethod
        def clean_state(cls, id=-1): pass
        @classmethod
        def clean(cls, all=False): pass

# ============================================================
# AnyType 定义
# ============================================================

class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")

# ============================================================
# 辅助函数：获取真实的存储实例
# ============================================================

def get_real_storage():
    """获取真实的 LLAMA_CPP_STORAGE 实例"""
    # 首先尝试直接从已加载的模块中获取
    for module_name, module in list(sys.modules.items()):
        if 'llama-cpp_vlm' in module_name or 'llama_cpp_vlm' in module_name:
            if hasattr(module, 'LLAMA_CPP_STORAGE'):
                storage = getattr(module, 'LLAMA_CPP_STORAGE')
                if hasattr(storage, 'llm'):
                    print(f"[llama-cpp-chat] Found storage in module: {module_name}")
                    return storage
    
    # 如果没找到，尝试导入
    return import_llama_storage()

# ============================================================
# 主节点类
# ============================================================

class llama_cpp_chat:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "llama_model": ("LLAMACPPMODEL",),
                "parameters": ("LLAMACPPARAMS",),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful AI assistant.",
                    "placeholder": "Enter system prompt here"
                }),
                "user_message": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter your message here"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1
                }),
                "force_offload": ("BOOLEAN", {
                    "default": False
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat"
    CATEGORY = "llama-cpp-vlm"

    def chat(self, llama_model, parameters, system_prompt, user_message, seed, force_offload, unique_id=None):
        # 获取真实的存储实例
        global LLAMA_CPP_STORAGE
        real_storage = get_real_storage()
        
        if real_storage is not None:
            LLAMA_CPP_STORAGE = real_storage
            print("[llama-cpp-chat] Using real storage instance")
        
        # 检查模型是否已加载
        if LLAMA_CPP_STORAGE is None or LLAMA_CPP_STORAGE.llm is None:
            print("[llama-cpp-chat] WARNING: LLAMA_CPP_STORAGE.llm is None")
            
            # 尝试从 loader 节点获取模型
            if isinstance(llama_model, dict):
                print("[llama-cpp-chat] Model config received, attempting to load...")
                
                # 尝试通过动态导入找到真实的 nodes.py
                try:
                    # 获取 custom_nodes 目录
                    current_file = os.path.abspath(__file__)
                    current_dir = os.path.dirname(current_file)
                    path = current_dir
                    while path != os.path.dirname(path):
                        if os.path.basename(path) == 'custom_nodes':
                            break
                        path = os.path.dirname(path)
                    custom_nodes_dir = path
                    
                    node_dir_path = os.path.join(custom_nodes_dir, 'ComfyUI-llama-cpp_vlm')
                    nodes_file_path = os.path.join(node_dir_path, 'nodes.py')
                    
                    if os.path.exists(nodes_file_path):
                        # 直接执行nodes.py来获取存储类
                        with open(nodes_file_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                        
                        # 创建命名空间
                        namespace = {}
                        exec(code, namespace)
                        
                        if 'LLAMA_CPP_STORAGE' in namespace:
                            RealStorage = namespace['LLAMA_CPP_STORAGE']
                            if RealStorage.llm is None:
                                print("[llama-cpp-chat] Loading model via exec...")
                                RealStorage.load_model(llama_model)
                            LLAMA_CPP_STORAGE = RealStorage
                            print("[llama-cpp-chat] Model loaded successfully via exec")
                except Exception as e:
                    print(f"[llama-cpp-chat] Exec loading failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 最终检查
            if LLAMA_CPP_STORAGE is None or LLAMA_CPP_STORAGE.llm is None:
                # 创建一个包装器，假设模型已加载
                print("[llama-cpp-chat] WARNING: Using fallback storage")
                class FallbackStorage:
                    llm = None
                    messages = {}
                    sys_prompts = {}
                    @classmethod
                    def clean_state(cls, id=-1): pass
                    @classmethod
                    def clean(cls, all=False): pass
                LLAMA_CPP_STORAGE = FallbackStorage
        
        # 验证参数
        if not isinstance(parameters, dict):
            raise ValueError(f"Parameters should be a dictionary, got {type(parameters)}")
        
        _uid = parameters.get("state_uid", None)
        _parameters = parameters.copy()
        _parameters.pop("state_uid", None)
        
        uid = unique_id.rpartition('.')[-1] if _uid in (None, -1) else _uid
        
        last_sys_prompt = LLAMA_CPP_STORAGE.sys_prompts.get(f"{uid}", None)
        system_content = system_prompt.strip()
        
        messages = []
        
        if last_sys_prompt != system_content:
            if hasattr(LLAMA_CPP_STORAGE, 'clean_state'):
                LLAMA_CPP_STORAGE.clean_state(id=uid)
            LLAMA_CPP_STORAGE.sys_prompts[f"{uid}"] = system_content
            if system_content:
                messages.append({"role": "system", "content": system_content})
        else:
            messages = LLAMA_CPP_STORAGE.messages.get(f"{uid}", [])
            if not messages and system_content:
                messages.append({"role": "system", "content": system_content})
        
        user_content = user_message.strip()
        if not user_content:
            raise ValueError("User message cannot be empty!")
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            print(f"[llama-cpp-chat] Generating response (seed: {seed}, uid: {uid})...")
            
            # 检查是否有llm实例
            if not hasattr(LLAMA_CPP_STORAGE, 'llm') or LLAMA_CPP_STORAGE.llm is None:
                # 尝试从sys.modules中查找
                found = False
                for module_name, module in list(sys.modules.items()):
                    if hasattr(module, 'LLAMA_CPP_STORAGE'):
                        storage = getattr(module, 'LLAMA_CPP_STORAGE')
                        if hasattr(storage, 'llm') and storage.llm is not None:
                            LLAMA_CPP_STORAGE = storage
                            print(f"[llama-cpp-chat] Found llm in module: {module_name}")
                            found = True
                            break
                
                if not found:
                    raise RuntimeError("No valid LLM instance found")
            
            # 使用导入的共享类的 llm 实例
            output = LLAMA_CPP_STORAGE.llm.create_chat_completion(
                messages=messages,
                seed=seed,
                **_parameters
            )
            
            if 'choices' not in output or not output['choices']:
                raise RuntimeError("Model returned no choices in output")
            
            response = output['choices'][0]['message']['content']
            response = response.strip()
            if response.startswith(": "):
                response = response[2:].lstrip()
            
            print(f"[llama-cpp-chat] Response generated ({len(response)} characters)")
            
            messages.append({"role": "assistant", "content": response})
            LLAMA_CPP_STORAGE.messages[f"{uid}"] = messages
            LLAMA_CPP_STORAGE.sys_prompts[f"{uid}"] = system_content
            
        except Exception as e:
            error_msg = f"Model inference failed: {str(e)}"
            print(f"[llama-cpp-chat] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)
        
        if force_offload:
            print("[llama-cpp-chat] Force offloading model...")
            if hasattr(LLAMA_CPP_STORAGE, 'clean'):
                LLAMA_CPP_STORAGE.clean()
        
        return (response,)

# ============================================================
# 节点注册
# ============================================================

NODE_CLASS_MAPPINGS = {
    "llama_cpp_chat": llama_cpp_chat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "llama_cpp_chat": "llama-cpp-chat",
}

if __name__ == "__main__":
    if "LLM" not in folder_paths.folder_names_and_paths:
        llm_extensions = ['.ckpt', '.pt', '.bin', '.pth', '.safetensors', '.gguf']
        folder_paths.folder_names_and_paths["LLM"] = (
            [os.path.join(folder_paths.models_dir, "LLM")],
            llm_extensions
        )
    print("llama-cpp-chat node definitions loaded")

