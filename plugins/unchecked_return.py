import re
from core.interface import BaseDetector

class UncheckedReturnDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-104"

    @property
    def description(self):
        return "检测到未检查返回值的低级调用 (Unchecked Return Value)"

    @property
    def severity(self):
        return "Medium"
    
    @property
    def title(self):
        return "Unchecked Low-Level Call Return Value"
    
    @property
    def swc_id(self):
        return "SWC-104"
    
    @property
    def confidence(self):
        return "High"
    
    @property
    def fix_suggestion(self):
        return "Check the return value of the call() or use transfer()/sendValue() (from OpenZeppelin) instead. Always verify the success of low-level calls before proceeding with state changes."

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        # 1. AST 分析策略
        if ast:
            def visit_node(node):
                # 寻找低级调用: .call(), .send(), .delegatecall()
                if node.get('nodeType') == 'MemberAccess':
                    member_name = node.get('memberName')
                    if member_name in ['call', 'send', 'delegatecall']:
                        # 检查这个调用的父节点是否使用了返回值
                        # 这需要向上回溯 AST，或者在遍历时维护父节点上下文
                        # 简化处理：我们假设如果它直接作为 ExpressionStatement 出现，就是未检查
                        pass 

            # 由于简单的 AST 遍历无法方便地获取父节点，我们结合 AST 和文本特征
            # 或者使用更高级的访问者模式
            pass

        # 2. 文本/正则策略 (更鲁棒)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 匹配 .call(...) 或 .call{...}(...) 或 .send(...)
            if re.search(r'\.(call|send|delegatecall)\s*\(', line) or re.search(r'\.call\s*\{.*\}\s*\(', line):
                # 排除注释
                if '//' in line: continue
                
                # 检查是否被使用
                is_checked = False
                if 'require(' in line or 'assert(' in line:
                    is_checked = True
                if 'if (' in line or 'if(' in line:
                    is_checked = True
                if '=' in line: # bool success = ...
                    is_checked = True
                
                if not is_checked:
                    issues.append({
                        "line": i + 1,
                        "msg": f"发现未检查返回值的低级调用: {line.strip()}"
                    })
        return issues

    def run(self, ctx):
        return self.check(ctx.content, ctx.filename, ast=ctx.ast)
