from core.interface import BaseDetector

class StorageVisibilityDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-108"

    @property
    def description(self):
        return "检测到显式设置为 public 的状态变量 (State Variable Visibility)"

    @property
    def severity(self):
        return "Info"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        if ast:
            def visit_node(node):
                if node.get('nodeType') == 'VariableDeclaration':
                    # 检查是否是状态变量 (stateVariable 为 true)
                    if node.get('stateVariable'):
                        # 检查可见性
                        visibility = node.get('visibility')
                        if visibility == 'public':
                            name = node.get('name')
                            # 获取行号
                            src = node.get('src')
                            line_num = 0
                            if src:
                                offset = int(src.split(':')[0])
                                line_num = content[:offset].count('\n') + 1
                            
                            issues.append({
                                "line": line_num,
                                "msg": f"状态变量 '{name}' 设置为 public，请确认是否包含敏感数据"
                            })

            def walk(node):
                visit_node(node)
                for key in ['nodes', 'children', 'statements', 'body', 'expression', 'components']:
                     val = node.get(key)
                     if isinstance(val, list):
                         for v in val: walk(v)
                     elif isinstance(val, dict):
                         walk(val)
            walk(ast)
        
        return issues
