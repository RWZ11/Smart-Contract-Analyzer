from core.interface import BaseDetector

class IRUncheckedReturnDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-104-IR"

    @property
    def description(self):
        return "基于 SCA-IR 的未检查转账/调用返回值检测"

    @property
    def severity(self):
        return "Medium"

    def check(self, content: str, filename: str, ast: dict = None, ir: dict = None) -> list:
        issues = []
        if not ir:
            return issues

        for fn in ir.get('functions') or []:
            for ins in fn.get('instructions') or []:
                op = ins.get('op')
                method = ins.get('method')
                checked = ins.get('checked', False)
                # 仅对 call/send 检查返回值使用情况；transfer 失败会回滚，不作为未检查返回值
                if op in ('EXTERNAL_CALL', 'SEND'):
                    if method == 'transfer':
                        continue
                    if not checked:
                        issues.append({
                            'line': ins.get('line') or 1,
                            'msg': f"函数 {fn.get('name') or ''} 中 {method} 返回值未检查，可能导致异常未被处理"
                        })
        return issues

