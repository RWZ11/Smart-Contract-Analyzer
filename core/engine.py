import os
import importlib
import inspect
import re
import time
from typing import Dict, List, Any, Tuple
from .interface import BaseDetector
from .ast_parser import ASTParser
from .sca_ir import SCAIRBuilder
from .context import AnalysisContext

class AnalyzerEngine:
    def __init__(self):
        self.detectors = []
        self.ast_parser = ASTParser()
        self.ir_builder = SCAIRBuilder()

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
        """分析单个文件，返回增强的结果信息"""
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 1. 生成 AST
            print(f"[DEBUG] 正在生成 AST: {file_path}")
            ast = self.ast_parser.parse(content)
            ir = None
            try:
                ir = self.ir_builder.build(ast, content) if ast else self.ir_builder.build_from_text(content)
            except Exception:
                try:
                    ir = self.ir_builder.build_from_text(content)
                except Exception:
                    ir = None
            
            # 2. 提取 Solidity 版本
            solidity_version = self._extract_solidity_version(content)
            
            # 3. 提取合约和函数信息
            contracts_map = self._extract_contracts_and_functions(ast, content) if ast else {}
                
            for detector in self.detectors:
                # 4. 运行每个插件的检测逻辑
                ctx = AnalysisContext(
                    content=content,
                    filename=file_path,
                    lines=lines,
                    ast=ast,
                    ir=ir,
                )
                issues = detector.run(ctx)
                for issue in issues:
                    # 5. 补充元数据
                    issue['detector'] = detector.id
                    issue['severity'] = detector.severity
                    issue['desc'] = detector.description
                    issue['title'] = detector.title
                    issue['swc_id'] = detector.swc_id or detector.id
                    issue['confidence'] = detector.confidence
                    issue['fix_suggestion'] = detector.fix_suggestion
                    
                    # 6. 获取出错行的具体代码
                    line_num = issue.get('line', 0)
                    if line_num and 0 < line_num <= len(lines):
                        # 提取代码片段（包括上下文）
                        start_line = max(0, line_num - 2)
                        end_line = min(len(lines), line_num + 2)
                        code_snippet = '\n'.join(lines[start_line:end_line])
                        issue['code'] = code_snippet
                        issue['end_line'] = end_line
                    
                    # 7. 尝试匹配到合约和函数
                    contract_name, function_name = self._find_contract_and_function(
                        line_num, contracts_map
                    )
                    if contract_name:
                        issue['contract'] = contract_name
                    if function_name:
                        issue['function'] = function_name
                    
                    results.append(issue)
                    
        except Exception as e:
            print(f"[错误] 无法分析文件 {file_path}: {e}")
            import traceback
            traceback.print_exc()
            
        return results
    
    def _extract_solidity_version(self, content: str) -> str:
        """从源代码中提取 Solidity 版本"""
        version_match = re.search(r'pragma solidity \^?(\d+\.\d+\.\d+);', content)
        if version_match:
            return version_match.group(1)
        # 尝试匹配范围版本
        version_match = re.search(r'pragma solidity \^?(\d+\.\d+)', content)
        if version_match:
            return version_match.group(1) + ".0"
        return "unknown"
    
    def _extract_contracts_and_functions(self, ast: Dict, content: str) -> Dict[str, Any]:
        """
        从 AST 中提取合约和函数的行号范围
        返回: {contract_name: {'range': (start, end), 'functions': {func_name: (start, end)}}}
        """
        contracts = {}
        
        def get_line_number(offset: int) -> int:
            return content[:offset].count('\n') + 1
        
        def visit_node(node):
            if node.get('nodeType') == 'ContractDefinition':
                contract_name = node.get('name', 'Unknown')
                src = node.get('src', '0:0:0')
                parts = src.split(':')
                if len(parts) >= 2:
                    offset = int(parts[0])
                    length = int(parts[1])
                    start_line = get_line_number(offset)
                    end_line = get_line_number(offset + length)
                else:
                    start_line = end_line = 1
                
                contracts[contract_name] = {
                    'range': (start_line, end_line),
                    'functions': {}
                }
                
                # 提取函数
                for node_item in node.get('nodes', []):
                    if node_item.get('nodeType') == 'FunctionDefinition':
                        func_name = node_item.get('name', '')
                        if not func_name:
                            func_name = node_item.get('kind', 'unknown')
                        func_src = node_item.get('src', '0:0:0')
                        func_parts = func_src.split(':')
                        if len(func_parts) >= 2:
                            func_offset = int(func_parts[0])
                            func_length = int(func_parts[1])
                            func_start = get_line_number(func_offset)
                            func_end = get_line_number(func_offset + func_length)
                            contracts[contract_name]['functions'][func_name] = (func_start, func_end)
        
        def walk(node):
            if not isinstance(node, dict):
                return
            visit_node(node)
            for key in ['nodes', 'children']:
                children = node.get(key, [])
                if isinstance(children, list):
                    for child in children:
                        walk(child)
        
        if ast:
            walk(ast)
        return contracts
    
    def _find_contract_and_function(self, line_num: int, contracts_map: Dict) -> Tuple[str, str]:
        """根据行号查找所属的合约和函数"""
        contract_name = ''
        function_name = ''
        
        for contract, info in contracts_map.items():
            start, end = info['range']
            if start <= line_num <= end:
                contract_name = contract
                # 查找函数
                for func, (func_start, func_end) in info['functions'].items():
                    if func_start <= line_num <= func_end:
                        function_name = func
                        break
                break
        
        return contract_name, function_name
