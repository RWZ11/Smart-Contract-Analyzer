from core.interface import BaseDetector
from core.context import AnalysisContext

class MsgValueLoopDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-msg-value-loop"

    @property
    def description(self):
        return "循环中使用 msg.value"

    @property
    def severity(self):
        return "Medium"

    def run(self, ctx):
        issues = []
        if not ctx.ast:
            return issues
        def walk(node, in_loop=False):
            nt = node.get('nodeType')
            if nt in ('ForStatement','WhileStatement','DoWhileStatement'):
                in_loop = True
            if node.get('nodeType') == 'MemberAccess' and node.get('memberName') == 'value':
                expr = node.get('expression') or {}
                if expr.get('nodeType') == 'Identifier' and expr.get('name') == 'msg' and in_loop:
                    src = node.get('src')
                    line = 1
                    if src:
                        try:
                            off = int(src.split(':')[0])
                            line = ctx.content[:off].count('\n') + 1
                        except Exception:
                            pass
                    issues.append(self.report(line, "循环中使用 msg.value 可能带来逻辑与安全风险"))
            for k in node:
                v = node[k]
                if isinstance(v, dict):
                    walk(v, in_loop)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            walk(it, in_loop)
        walk(ctx.ast)
        return issues

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        ctx = AnalysisContext(content=content, filename=filename, lines=content.split('\n'), ast=ast, ir=ir)
        return self.run(ctx)
