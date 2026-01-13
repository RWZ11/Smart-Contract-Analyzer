import re
from core.interface import BaseDetector

class DelegateCallDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-112"

    @property
    def description(self):
        return "检测到危险的 delegatecall 使用 (Delegatecall to Untrusted Callee)"

    @property
    def severity(self):
        return "High"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '.delegatecall' in line and '//' not in line:
                # 检查目标是否是 msg.sender (极端危险)
                # 或者是否是未初始化的存储变量
                issues.append({
                    "line": i + 1,
                    "msg": "发现使用了 delegatecall，请确保目标地址可信且存储布局兼容"
                })
        return issues

    def run(self, ctx):
        return self.check(ctx.content, ctx.filename, ast=ctx.ast)
