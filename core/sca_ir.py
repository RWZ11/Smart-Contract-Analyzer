from typing import List, Dict, Any

class SCAIRBuilder:
    def __init__(self):
        self.state_vars = set()

    def build(self, ast: Dict[str, Any], content: str) -> Dict[str, Any]:
        self.state_vars = set()
        self._collect_state_vars(ast)
        functions = []
        for node in self._iter_nodes(ast):
            if node.get('nodeType') == 'FunctionDefinition' and node.get('kind') in (None, 'function', 'constructor'):
                name = node.get('name') or ('constructor' if node.get('kind') == 'constructor' else '')
                modifiers = []
                for m in node.get('modifiers', []) or []:
                    mn = (m.get('modifierName') or {}).get('name')
                    if mn:
                        modifiers.append(mn)
                instr = []
                instr.append({'op': 'FUNC', 'name': name, 'line': self._line_from_src(content, node.get('src'))})
                body = node.get('body') or {}
                self._emit_instructions_from_block(body, content, instr)
                functions.append({'name': name, 'modifiers': modifiers, 'instructions': instr})
        return {'functions': functions}

    def build_from_text(self, content: str) -> Dict[str, Any]:
        # 轻量文本回退：按行扫描，生成一个伪函数的指令序列
        lines = content.split('\n')
        instr: List[Dict[str, Any]] = [{'op': 'FUNC', 'name': '', 'line': 1}]
        for i, line in enumerate(lines, start=1):
            l = line.strip()
            if 'require(' in l:
                instr.append({'op': 'REQUIRE', 'line': i})
            # 低级调用：.call{...}(...) 或 .call(...)
            if '.call{' in l or '.call(' in l:
                checked = '=' in l  # 简化：同一行若有赋值认为接收了返回值
                instr.append({'op': 'EXTERNAL_CALL', 'method': 'call', 'line': i, 'checked': checked})
            # 发送：send/transfer
            if '.send(' in l:
                checked = '=' in l
                instr.append({'op': 'SEND', 'method': 'send', 'line': i, 'checked': checked})
            if '.transfer(' in l or 'transfer(' in l:
                instr.append({'op': 'SEND', 'method': 'transfer', 'line': i, 'checked': True})
            # 状态写入（极简启发式）
            if '=' in l and ('balance' in l or 'owner' in l):
                instr.append({'op': 'STATE_WRITE', 'var': 'unknown', 'line': i})
        return {'functions': [{'name': '', 'modifiers': [], 'instructions': instr}]}

    def _collect_state_vars(self, ast: Dict[str, Any]):
        for node in self._iter_nodes(ast):
            if node.get('nodeType') == 'VariableDeclaration' and node.get('stateVariable'):
                n = node.get('name')
                if n:
                    self.state_vars.add(n)

    def _emit_instructions_from_block(self, block: Dict[str, Any], content: str, instr: List[Dict[str, Any]]):
        for st in (block.get('statements') or []):
            self._emit_from_statement(st, content, instr)

    def _emit_from_statement(self, st: Dict[str, Any], content: str, instr: List[Dict[str, Any]]):
        nt = st.get('nodeType')
        if nt == 'ExpressionStatement':
            expr = st.get('expression') or {}
            self._emit_from_expression(expr, content, instr)
        elif nt == 'IfStatement':
            instr.append({'op': 'IF', 'line': self._line_from_src(content, st.get('src'))})
            then = st.get('trueBody') or {}
            self._emit_instructions_from_block(then, content, instr)
            elseb = st.get('falseBody') or {}
            if elseb:
                self._emit_instructions_from_block(elseb, content, instr)
        elif nt == 'Return':
            instr.append({'op': 'RETURN', 'line': self._line_from_src(content, st.get('src'))})
        elif nt == 'VariableDeclarationStatement':
            decls = st.get('declarations') or []
            # 变量声明（可能带初始化）
            init = st.get('initialValue') or {}
            if init:
                # 检查是否是对低级调用返回值的接收
                if init.get('nodeType') == 'FunctionCall':
                    callee = init.get('expression') or {}
                    if callee.get('nodeType') == 'MemberAccess':
                        mn = callee.get('memberName')
                        if mn in ('call', 'send'):
                            op = 'EXTERNAL_CALL' if mn == 'call' else 'SEND'
                            instr.append({'op': op, 'method': mn, 'line': self._line_from_src(content, init.get('src')), 'checked': True})
            for d in decls:
                name = d.get('name')
                if name in self.state_vars:
                    instr.append({'op': 'STATE_DECL', 'var': name, 'line': self._line_from_src(content, st.get('src'))})
        elif nt == 'WhileStatement' or nt == 'ForStatement':
            instr.append({'op': 'LOOP', 'line': self._line_from_src(content, st.get('src'))})

    def _emit_from_expression(self, expr: Dict[str, Any], content: str, instr: List[Dict[str, Any]]):
        nt = expr.get('nodeType')
        if nt == 'FunctionCall':
            callee = expr.get('expression') or {}
            cname = callee.get('name')
            if cname == 'require':
                instr.append({'op': 'REQUIRE', 'line': self._line_from_src(content, expr.get('src'))})
                return
            if cname == 'selfdestruct':
                instr.append({'op': 'SELFDESTRUCT', 'line': self._line_from_src(content, expr.get('src'))})
                return
            if callee.get('nodeType') == 'MemberAccess':
                mn = callee.get('memberName')
                if mn in ('call', 'send', 'transfer', 'delegatecall'):
                    op = 'EXTERNAL_CALL' if mn in ('call', 'delegatecall') else 'SEND'
                    # 默认未检查（在赋值或声明初始化时会标记 checked=True）
                    instr.append({'op': op, 'method': mn, 'line': self._line_from_src(content, expr.get('src')), 'checked': False})
                    return
        elif nt == 'Assignment':
            lhs = expr.get('leftHandSide') or {}
            varname = lhs.get('name')
            if varname in self.state_vars:
                instr.append({'op': 'STATE_WRITE', 'var': varname, 'line': self._line_from_src(content, expr.get('src'))})
            # 如果右侧是低级调用，说明返回值被接收（checked=True）
            rhs = expr.get('rightHandSide') or {}
            if rhs.get('nodeType') == 'FunctionCall':
                callee = rhs.get('expression') or {}
                if callee.get('nodeType') == 'MemberAccess':
                    mn = callee.get('memberName')
                    if mn in ('call', 'send'):
                        op = 'EXTERNAL_CALL' if mn == 'call' else 'SEND'
                        instr.append({'op': op, 'method': mn, 'line': self._line_from_src(content, rhs.get('src')), 'checked': True})

    def _iter_nodes(self, node: Any):
        if isinstance(node, dict):
            yield node
            for k, v in node.items():
                if isinstance(v, dict):
                    for x in self._iter_nodes(v):
                        yield x
                elif isinstance(v, list):
                    for it in v:
                        for x in self._iter_nodes(it):
                            yield x

    def _line_from_src(self, content: str, src: str):
        try:
            if not src:
                return 0
            offset = int(str(src).split(':')[0])
            return content[:offset].count('\n') + 1
        except Exception:
            return 0
