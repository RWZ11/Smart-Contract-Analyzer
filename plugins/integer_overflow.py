import re
from core.interface import BaseDetector

class IntegerOverflowDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-101"

    @property
    def description(self):
        return "检测到潜在的整数溢出/下溢风险 (Integer Overflow/Underflow)"

    @property
    def severity(self):
        return "High"
    
    @property
    def title(self):
        return "Integer Overflow/Underflow Risk"
    
    @property
    def swc_id(self):
        return "SWC-101"
    
    @property
    def confidence(self):
        return "Medium"
    
    @property
    def fix_suggestion(self):
        return "For Solidity < 0.8.0: Use OpenZeppelin SafeMath library for all arithmetic operations. For Solidity >= 0.8.0: Avoid using unchecked blocks unless absolutely necessary and thoroughly audited."

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        
        # 检查 Solidity 版本
        # Solidity 0.8.0 之后内置了溢出检查，所以此规则主要针对 0.8.0 之前
        is_safe_version = False
        version_match = re.search(r'pragma solidity \^?(\d+\.\d+\.\d+);', content)
        if version_match:
            version = version_match.group(1)
            # 简单的版本比较: 0.8.0 及以上为安全
            major, minor, patch = map(int, version.split('.'))
            if major > 0 or (major == 0 and minor >= 8):
                is_safe_version = True

        if is_safe_version:
            # 如果是 0.8+，只检查 unchecked 块
            # 这里简化处理，暂时忽略 0.8+ 的 unchecked 块检测
            return []

        # 针对 0.8.0 以下版本
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 排除注释和 import
            if '//' in line or 'import' in line: continue

            # 简单的算术运算检测 +, -, *, +=, -=, *=
            # 且没有使用 SafeMath (简单的字符串检查)
            if re.search(r'(\+|\-|\*|\+=|\-=|\*=)', line):
                # 排除循环变量 i++ 等简单情况 (误报率控制)
                if 'for (' in line: continue
                
                # 检查是否使用了 .add, .sub, .mul (SafeMath 特征)
                if '.add(' in line or '.sub(' in line or '.mul(' in line:
                    continue
                
                issues.append({
                    "line": i + 1,
                    "msg": "发现算术运算且未使用 SafeMath (Solidity < 0.8.0 需注意溢出)"
                })
        return issues

    def run(self, ctx):
        return self.check(ctx.content, ctx.filename, ast=ctx.ast)
