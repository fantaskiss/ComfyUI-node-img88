import os
import gc
import json
import torch
import numpy as np
from PIL import Image, ImageDraw
import folder_paths
import comfy.model_management as mm

# 定义 AnyType 类（与 nodes.py 保持一致）
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")

# 定义 LLAMA_CPP_STORAGE 类（与 nodes.py 保持一致，但简化版本）
class LLAMA_CPP_STORAGE:
    llm = None
    chat_handler = None
    current_config = None
    
    @classmethod
    def clean(cls):
        """清理模型和资源"""
        try:
            if cls.llm:
                cls.llm.close()
        except Exception:
            pass
            
        try:
            if cls.chat_handler:
                cls.chat_handler._exit_stack.close()
        except Exception:
            pass
        
        cls.llm = None
        cls.chat_handler = None
        cls.current_config = None
        
        gc.collect()
        mm.soft_empty_cache()

# 主节点类
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
                    "placeholder": "Enter system prompt here (role setting, instructions, etc.)"
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
                    "step": 1,
                    "tooltip": "Random seed for reproducible generation"
                }),
                "force_offload": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Unload the model from GPU after inference"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat"
    CATEGORY = "llama-cpp-vlm"
    
    def chat(self, llama_model, parameters, system_prompt, user_message, seed, force_offload):
        """
        处理纯文本对话
        """
        # 检查模型是否已加载
        if not llama_model.llm:
            raise RuntimeError("The model has not been loaded or has been unloaded! Please load a model first.")
        
        # 检查参数字典格式
        if not isinstance(parameters, dict):
            raise ValueError(f"Parameters should be a dictionary, got {type(parameters)}")
        
        # 构建消息列表
        messages = []
        
        # 添加系统提示词（如果提供）
        system_content = system_prompt.strip()
        if system_content:
            messages.append({
                "role": "system",
                "content": system_content
            })
        
        # 添加用户消息
        user_content = user_message.strip()
        if not user_content:
            raise ValueError("User message cannot be empty!")
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # 调用模型生成回复
        try:
            print(f"[llama-cpp-chat] Generating response (seed: {seed})...")
            
            # 调用模型
            output = llama_model.llm.create_chat_completion(
                messages=messages,
                seed=seed,
                **parameters
            )
            
            # 提取回复文本
            if 'choices' not in output or not output['choices']:
                raise RuntimeError("Model returned no choices in output")
            
            response = output['choices'][0]['message']['content']
            
            # 清理常见的前缀格式（与原节点保持一致）
            response = response.strip()
            if response.startswith(": "):
                response = response[2:].lstrip()
            
            print(f"[llama-cpp-chat] Response generated ({len(response)} characters)")
            
        except Exception as e:
            error_msg = f"Model inference failed: {str(e)}"
            print(f"[llama-cpp-chat] ERROR: {error_msg}")
            raise RuntimeError(error_msg)
        
        # 如果设置了强制卸载，清理模型
        if force_offload:
            print("[llama-cpp-chat] Force offloading model...")
            llama_model.clean()
        
        return (response,)

# ComfyUI 节点注册
NODE_CLASS_MAPPINGS = {
    "llama_cpp_chat": llama_cpp_chat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "llama_cpp_chat": "llama-cpp-chat",
}

# 可选：如果这个文件单独运行，确保必要的文件夹路径已注册
if __name__ == "__main__":
    # 确保 LLM 文件夹路径已注册（与 nodes.py 一致）
    if "LLM" not in folder_paths.folder_names_and_paths:
        llm_extensions = ['.ckpt', '.pt', '.bin', '.pth', '.safetensors', '.gguf']
        folder_paths.folder_names_and_paths["LLM"] = (
            [os.path.join(folder_paths.models_dir, "LLM")], 
            llm_extensions
        )
    print("llama-cpp-chat node definitions loaded")