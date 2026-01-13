import os
import importlib
import inspect
from .interface import BaseDetector
from .ast_parser import ASTParser

class AnalyzerEngine:
    def __init__(self):
        self.detectors = []
        self.ast_parser = ASTParser()

    def load_plugins(self, plugin_dir="plugins"):
        """动态加载插件目录下所有的检测规则"""
        # 获取绝对路径
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_path = os.path.join(base_path, plugin_dir)
        
        # 遍历插件目录
        for filename in os.listdir(plugin_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{plugin_dir}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # 查找该模块中所有继承自 BaseDetector 的类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseDetector) and 
                            obj is not BaseDetector):
                            self.detectors.append(obj())
                            print(f"[系统] 已加载检测规则: {name}")
                except Exception as e:
                    print(f"[错误] 加载插件 {module_name} 失败: {e}")

    def analyze_file(self, file_path):
        """分析单个文件"""
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 1. 生成 AST
            print(f"[DEBUG] 正在生成 AST: {file_path}")
            ast = self.ast_parser.parse(content)
                
            for detector in self.detectors:
                # 2. 运行每个插件的检测逻辑 (传入 content 和 ast)
                # 注意：为了兼容旧插件，我们需要检查插件是否接受 ast 参数
                # 但为了简单起见，我们假设所有插件都将升级支持 ast，或者我们在 BaseDetector 里做处理
                # 这里我们扩展 check 方法的定义，暂时通过 kwargs 传递
                issues = detector.check(content, file_path, ast=ast)
                for issue in issues:
                    # 补充元数据
                    issue['detector'] = detector.id
                    issue['severity'] = detector.severity
                    issue['desc'] = detector.description
                    # 获取出错行的具体代码
                    if 'line' in issue and 0 <= issue['line'] - 1 < len(lines):
                        issue['code'] = lines[issue['line'] - 1].strip()
                    results.append(issue)
                    
        except Exception as e:
            print(f"[错误] 无法分析文件 {file_path}: {e}")
            
        return results
