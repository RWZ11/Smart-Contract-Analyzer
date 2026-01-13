from core.interface import BaseDetector
from core.context import AnalysisContext

class ControlledDelegatecallDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-controlled-delegatecall"

    @property
    def description(self):
        return "delegatecall 目标可能被外部控制"

    @property
    def severity(self):
        return "High"

    def run(self, ctx):
        issues = []
        if not ctx.ast:
            return issues
        def fn_params(node):
            res = set()
            for p in (node.get('parameters') or {}).get('parameters', []) or []:
                n = p.get('name')
                if n:
                    res.add(n)
            return res
        def walk(node, params=None):
            nt = node.get('nodeType')
            if nt == 'FunctionDefinition':
                params = fn_params(node)
            if nt == 'MemberAccess' and node.get('memberName') == 'delegatecall':
                expr = node.get('expression') or {}
                if expr.get('nodeType') == 'Identifier' and params and expr.get('name') in params:
                    src = node.get('src')
                    line = 1
                    if src:
                        try:
                            off = int(src.split(':')[0])
                            line = ctx.content[:off].count('\n') + 1
                        except Exception:
                            pass
                    issues.append(self.report(line, "delegatecall 目标来自函数参数，存在高风险"))
            for k in node:
                v = node[k]
                if isinstance(v, dict):
                    walk(v, params)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            walk(it, params)
        walk(ctx.ast)
        return issues

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        ctx = AnalysisContext(content=content, filename=filename, lines=content.split('\n'), ast=ast, ir=ir)
        return self.run(ctx)
