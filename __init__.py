# ComfyUI/custom_nodes/img8/__init__.py
import os
import importlib.util
import sys

# ANSI 颜色代码
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_RESET = '\033[0m'

# 收集所有节点的映射
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 记录成功和失败的模块
successful_modules = []
failed_modules = []

# 自动导入当前目录下的所有.py文件
current_dir = os.path.dirname(os.path.abspath(__file__))

print(f"{COLOR_BLUE}[img8]{COLOR_RESET} 开始加载自定义节点...")

# 按文件名排序，确保加载顺序一致
for filename in sorted(os.listdir(current_dir)):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]  # 去掉.py后缀
        module_path = os.path.join(current_dir, filename)
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                error_msg = f"无法创建模块规范"
                print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {module_name}: {error_msg}{COLOR_RESET}")
                failed_modules.append((module_name, error_msg))
                continue
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"img8.{module_name}"] = module
            
            # 执行模块
            spec.loader.exec_module(module)
            
            # 收集节点映射
            node_count = 0
            if hasattr(module, 'NODE_CLASS_MAPPINGS'):
                node_count = len(module.NODE_CLASS_MAPPINGS)
                NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                
            if hasattr(module, 'NODE_DISPLAY_NAME_MAPPINGS'):
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            
            if node_count > 0:
                # 静默成功，不打印信息
                successful_modules.append((module_name, node_count))
            else:
                error_msg = "未发现节点映射"
                print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {module_name}: {error_msg}{COLOR_RESET}")
                failed_modules.append((module_name, error_msg))
                
        except SyntaxError as e:
            error_msg = f"语法错误: {e.msg} (第{e.lineno}行)"
            print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {module_name}: {error_msg}{COLOR_RESET}")
            failed_modules.append((module_name, error_msg))
        except ImportError as e:
            error_msg = f"导入错误: {str(e)}"
            print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {module_name}: {error_msg}{COLOR_RESET}")
            failed_modules.append((module_name, error_msg))
        except Exception as e:
            error_msg = str(e)
            print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {module_name}: {error_msg}{COLOR_RESET}")
            failed_modules.append((module_name, error_msg))

# 统计输出
print(f"\n{COLOR_BLUE}[img8]{COLOR_RESET} {'='*50}")

# 成功统计（只显示总数）
total_nodes = len(NODE_CLASS_MAPPINGS)
print(f"{COLOR_BLUE}[img8]{COLOR_GREEN} ✅ 成功加载 {len(successful_modules)}/{len(successful_modules)+len(failed_modules)} 个模块，共计 {total_nodes} 个节点{COLOR_RESET}")

# 失败统计（详细显示）
if failed_modules:
    print(f"{COLOR_BLUE}[img8]{COLOR_RED} ❌ {len(failed_modules)} 个模块加载失败:{COLOR_RESET}")
    for module_name, error_msg in failed_modules:
        print(f"    {COLOR_RED}• {module_name}: {error_msg}{COLOR_RESET}")

print(f"{COLOR_BLUE}[img8]{COLOR_RESET} {'='*50}")

# 可选：如果全部成功，显示庆祝信息
if not failed_modules and successful_modules:
    print(f"{COLOR_BLUE}[img8]{COLOR_GREEN} 🎉 所有节点加载成功！{COLOR_RESET}")