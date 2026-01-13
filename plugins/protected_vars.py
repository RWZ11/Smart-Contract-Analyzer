from core.interface import BaseDetector
from core.context import AnalysisContext

class ProtectedVarsDetector(BaseDetector):
    @property
    def id(self):
        return "SLITHER-like-protected-vars"

    @property
    def description(self):
        return "关键状态写入缺少所有者保护"

    @property
    def severity(self):
        return "High"

    def run(self, ctx: AnalysisContext):
        issues = []
        if not ctx.ir:
            return issues

        protected_mods = {"onlyOwner", "ownerOnly", "onlyAdmin", "admin"}

        write_funcs = {}
        for fn in ctx.ir.get("functions") or []:
            w_lines = [ins.get("line") for ins in fn.get("instructions") or [] if ins.get("op") == "STATE_WRITE"]
            if w_lines:
                write_funcs[fn.get("name") or ""] = w_lines

        def has_owner_require(fn_node):
            def is_owner_check(cond):
                if cond.get("nodeType") != "BinaryOperation":
                    return False
                if cond.get("operator") != "==":
                    return False
                left = cond.get("leftExpression") or {}
                right = cond.get("rightExpression") or {}
                def is_msg_sender(x):
                    return x.get("nodeType") == "MemberAccess" and x.get("memberName") == "sender" and (x.get("expression") or {}).get("name") == "msg"
                def is_owner_ident(x):
                    return x.get("nodeType") == "Identifier" and x.get("name") == "owner"
                return (is_msg_sender(left) and is_owner_ident(right)) or (is_msg_sender(right) and is_owner_ident(left))
            body = fn_node.get("body") or {}
            def walk(n):
                if n.get("nodeType") == "FunctionCall" and (n.get("expression") or {}).get("name") == "require":
                    args = n.get("arguments") or []
                    if args and is_owner_check(args[0] or {}):
                        return True
                for k in n:
                    v = n[k]
                    if isinstance(v, dict):
                        if walk(v):
                            return True
                    elif isinstance(v, list):
                        for it in v:
                            if isinstance(it, dict) and walk(it):
                                return True
                return False
            return walk(body)

        for node in [n for n in (ctx.ast and [ctx.ast] or [])]:
            pass

        def walk(node):
            if node.get("nodeType") == "FunctionDefinition":
                name = node.get("name") or ""
                if name in write_funcs:
                    mods = {((m.get("modifierName") or {}).get("name") or "") for m in (node.get("modifiers") or [])}
                    if protected_mods & mods:
                        return
                    if has_owner_require(node):
                        return
                    line = (write_funcs[name] or [1])[0]
                    issues.append(self.report(line, f"函数 {name} 存在状态写入但缺少所有者保护"))
            for k in node:
                v = node[k]
                if isinstance(v, dict):
                    walk(v)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            walk(it)

        if ctx.ast:
            walk(ctx.ast)
        return issues

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        ctx = AnalysisContext(content=content, filename=filename, lines=content.split("\n"), ast=ast, ir=ir)
        return self.run(ctx)

