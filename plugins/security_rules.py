import re
from core.interface import BaseDetector

class TxOriginDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-115"

    @property
    def description(self):
        return "检测到使用了 tx.origin，可能导致钓鱼攻击 (Phishing Vulnerability)"

    @property
    def severity(self):
        return "High"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        
        # 策略 1: 基于 AST 的精确检测 (如果 AST 可用)
        if ast:
            # 遍历 AST 寻找 tx.origin 的 MemberAccess
            def visit_node(node):
                if node.get('nodeType') == 'MemberAccess':
                    if node.get('memberName') == 'origin':
                        expr = node.get('expression')
                        if expr and (expr.get('name') == 'tx' or (expr.get('attributes') or {}).get('value') == 'tx'):
                            # 找到 tx.origin，计算行号
                            src = node.get('src')
                            if src:
                                offset = int(src.split(':')[0])
                                line_num = content[:offset].count('\n') + 1
                                issues.append({
                                    "line": line_num,
                                    "msg": "通过 AST 分析发现使用了 tx.origin"
                                })
            
            # 简单的 AST 遍历辅助函数
            def walk(node):
                visit_node(node)
                for key in ['nodes', 'children', 'statements', 'body', 'expression', 'components']:
                     val = node.get(key)
                     if isinstance(val, list):
                         for v in val: walk(v)
                     elif isinstance(val, dict):
                         walk(val)

            walk(ast)
            
            # 如果 AST 分析有结果，直接返回，避免和正则重复
            if issues:
                return issues

        # 策略 2: 降级回退到正则匹配 (当 AST 解析失败时)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 简单的字符串匹配，实际应使用 AST 分析
            if 'tx.origin' in line and '//' not in line:
                issues.append({
                    "line": i + 1,
                    "msg": "发现使用了 tx.origin，建议使用 msg.sender 替代"
                })
        return issues

class ReentrancyDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-107"

    @property
    def description(self):
        return "检测到低级调用 call.value，可能存在重入漏洞 (Reentrancy)"

    @property
    def severity(self):
        return "High"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        # 增强策略：使用 AST 识别 call.value
        if ast:
            def visit_node(node):
                if node.get('nodeType') == 'MemberAccess':
                    # 识别 .call
                    if node.get('memberName') == 'call':
                         # 检查是否有 value 选项 (AST 结构可能不同，简化处理)
                         # 这里我们假设低级调用本身就值得警告，特别是如果它涉及 value
                         # 更好的方式是检查 FunctionCall 的 options
                         pass
            # (此处略去复杂的 AST 状态检查实现，保持教学简洁)

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 简单的正则匹配 .call.value(...)
            if re.search(r'\.call\.value\s*\(', line) and '//' not in line:
                issues.append({
                    "line": i + 1,
                    "msg": "发现使用了 .call.value()，请确保使用了 Check-Effects-Interactions 模式或重入锁"
                })
            # 新增：检测 .call{value: ...} (新版 Solidity 写法)
            if re.search(r'\.call\s*\{.*value:', line) and '//' not in line:
                issues.append({
                     "line": i + 1,
                     "msg": "发现使用了 .call{value:...}，存在重入风险"
                })
        return issues

class PragmaVersionDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-103"

    @property
    def description(self):
        return "检测 Solidity 编译器版本是否过旧"

    @property
    def severity(self):
        return "Low"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'pragma solidity' in line:
                # 简单检查是否小于 0.8.0
                if '^0.4' in line or '^0.5' in line or '^0.6' in line or '^0.7' in line:
                     issues.append({
                        "line": i + 1,
                        "msg": "使用了旧版本的 Solidity，建议升级到 0.8.0 以上"
                    })
        return issues
