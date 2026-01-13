from core.interface import BaseDetector
from core.context import AnalysisContext

class IRArbitrarySendEthDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-arbitrary-send-eth"

    @property
    def description(self):
        return "检测向可能由外部控制的地址发送以太币"

    @property
    def severity(self):
        return "Medium"

    def run(self, ctx):
        issues = []
        if not ctx.ast:
            return issues
        params_by_func = {}
        def collect_params(fn):
            names = []
            for p in (fn.get('parameters') or {}).get('parameters', []) or []:
                n = p.get('name')
                if n:
                    names.append(n)
            return set(names)
        def walk(node, current_fn_params=None):
            nt = node.get('nodeType')
            if nt == 'FunctionDefinition':
                current_fn_params = collect_params(node)
            if nt == 'MemberAccess':
                mn = node.get('memberName')
                expr = node.get('expression') or {}
                if mn in ('transfer','send','call') and expr.get('nodeType') == 'Identifier':
                    name = expr.get('name')
                    if current_fn_params and name in current_fn_params:
                        src = node.get('src')
                        line = 1
                        if src:
                            try:
                                off = int(src.split(':')[0])
                                line = ctx.content[:off].count('\n') + 1
                            except Exception:
                                pass
                        issues.append(self.report(line, f"向函数参数地址执行 {mn}，可能为外部控制地址"))
            for k in node:
                v = node[k]
                if isinstance(v, dict):
                    walk(v, current_fn_params)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            walk(it, current_fn_params)
        walk(ctx.ast)
        return issues

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        ctx = AnalysisContext(content=content, filename=filename, lines=content.split('\n'), ast=ast, ir=ir)
        return self.run(ctx)
