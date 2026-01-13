from core.interface import BaseDetector

class IRReentrancyDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-107-IR"

    @property
    def description(self):
        return "基于 SCA-IR 的重入风险检测：外部调用先于状态更新"

    @property
    def severity(self):
        return "High"
    
    @property
    def title(self):
        return "Reentrancy Vulnerability"
    
    @property
    def swc_id(self):
        return "SWC-107"
    
    @property
    def confidence(self):
        return "High"
    
    @property
    def fix_suggestion(self):
        return "1. Add OpenZeppelin ReentrancyGuard modifier to the function; 2. Follow Check-Effects-Interactions pattern (update state before external calls); 3. Use pull payment pattern instead of push."

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        issues = []
        if not ir:
            return issues
        for fn in ir.get('functions') or []:
            modifiers = set(fn.get('modifiers') or [])
            if 'nonReentrant' in modifiers:
                continue
            seen_external = False
            first_external_line = 0
            for ins in fn.get('instructions') or []:
                op = ins.get('op')
                if op in ('EXTERNAL_CALL', 'SEND'):
                    if not seen_external:
                        seen_external = True
                        first_external_line = ins.get('line') or 0
                if op == 'STATE_WRITE' and seen_external:
                    issues.append({
                        'line': first_external_line or ins.get('line') or 1,
                        'msg': f"函数 {fn.get('name') or ''} 中外部调用先于状态更新，存在重入风险"
                    })
                    break
        return issues

