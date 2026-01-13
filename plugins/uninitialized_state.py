from core.interface import BaseDetector
from core.context import AnalysisContext

class UninitializedStateDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-uninitialized-state"

    @property
    def description(self):
        return "未初始化的状态变量"

    @property
    def severity(self):
        return "Medium"

    def run(self, ctx):
        issues = []
        if not ctx.ast:
            return issues
        def walk(node):
            if node.get('nodeType') == 'VariableDeclaration' and node.get('stateVariable'):
                if node.get('value') is None:
                    src = node.get('src')
                    line = 1
                    if src:
                        try:
                            off = int(src.split(':')[0])
                            line = ctx.content[:off].count('\n') + 1
                        except Exception:
                            pass
                    name = node.get('name') or ''
                    issues.append(self.report(line, f"状态变量 {name} 未初始化"))
            for k in node:
                v = node[k]
                if isinstance(v, dict):
                    walk(v)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            walk(it)
        walk(ctx.ast)
        return issues

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        ctx = AnalysisContext(content=content, filename=filename, lines=content.split('\n'), ast=ast, ir=ir)
        return self.run(ctx)
