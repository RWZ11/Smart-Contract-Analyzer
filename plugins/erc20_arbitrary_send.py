from core.interface import BaseDetector
from core.context import AnalysisContext

class ERC20ArbitrarySendDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-arbitrary-send-erc20"

    @property
    def description(self):
        return "transferFrom 使用可控的 from 参数"

    @property
    def severity(self):
        return "High"

    def run(self, ctx: AnalysisContext):
        issues = []
        if not ctx.ast:
            return issues

        def fn_params(node):
            names = []
            params = (node.get('parameters') or {}).get('parameters', []) or []
            for p in params:
                n = p.get('name')
                if n:
                    names.append(n)
            return set(names)

        def line_from_src(src):
            if not src:
                return 1
            try:
                off = int(str(src).split(':')[0])
                return ctx.content[:off].count('\n') + 1
            except Exception:
                return 1

        def walk(node, params=None):
            nt = node.get('nodeType')
            if nt == 'FunctionDefinition':
                params = fn_params(node)
            if nt == 'FunctionCall':
                expr = node.get('expression') or {}
                if expr.get('nodeType') == 'MemberAccess' and expr.get('memberName') == 'transferFrom':
                    args = node.get('arguments') or []
                    if args:
                        a0 = args[0] or {}
                        if a0.get('nodeType') == 'Identifier' and params and a0.get('name') in params:
                            issues.append(self.report(line_from_src(node.get('src')), "transferFrom 的 from 参数来自函数参数，可能被外部控制"))
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

