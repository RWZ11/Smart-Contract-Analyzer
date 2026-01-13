
class DataFlowAnalyzer:
    """
    简易数据流分析器
    功能：追踪变量的定义(Def)和使用(Use)
    """
    def __init__(self, ast):
        self.ast = ast
        self.variables = {}  # 存储变量定义信息 {var_name: [locations]}
        self.assignments = {} # 存储赋值关系 {var_name: [values]}

    def analyze(self):
        if not self.ast:
            return
        
        # 第一次遍历：收集所有状态变量和局部变量定义
        self._collect_definitions(self.ast)
        
        # 第二次遍历：收集赋值和使用
        self._collect_usages(self.ast)

    def _collect_definitions(self, node):
        # 递归遍历辅助函数
        children = node.get('nodes') or node.get('children') or []
        
        node_type = node.get('nodeType') or node.get('name')
        
        # 捕获变量声明
        if node_type == 'VariableDeclaration':
            name = node.get('name')
            src = node.get('src')
            if name:
                self.variables[name] = {'defined_at': src, 'type': node.get('typeName')}

        for child in children:
            self._collect_definitions(child)
            
        # 处理 body/statements
        if 'body' in node and node['body']:
             self._collect_definitions(node['body'])
        if 'statements' in node and node['statements']:
            for stmt in node['statements']:
                self._collect_definitions(stmt)

    def _collect_usages(self, node):
        children = node.get('nodes') or node.get('children') or []
        node_type = node.get('nodeType') or node.get('name')

        # 捕获赋值操作
        if node_type == 'Assignment':
            left = node.get('leftHandSide')
            right = node.get('rightHandSide')
            
            # 简化处理：假设左边是变量名
            if left and (left.get('nodeType') == 'Identifier' or left.get('name') == 'Identifier'):
                var_name = left.get('value') or left.get('name') # 不同版本 AST 字段可能不同
                if not var_name and 'attributes' in left:
                     var_name = left['attributes'].get('value')
                
                if var_name:
                    if var_name not in self.assignments:
                        self.assignments[var_name] = []
                    self.assignments[var_name].append(right)
        
        for child in children:
            self._collect_usages(child)

        if 'body' in node and node['body']:
             self._collect_usages(node['body'])
        if 'statements' in node and node['statements']:
            for stmt in node['statements']:
                self._collect_usages(stmt)
        if 'expression' in node and node['expression']:
             self._collect_usages(node['expression'])

    def is_tainted(self, var_name, tainted_sources):
        """
        简单的污点分析：检查 var_name 是否受 tainted_sources 影响
        :param var_name: 目标变量名
        :param tainted_sources: 污染源列表 (如 'msg.sender', 'tx.origin')
        :return: Boolean
        """
        # 1. 直接检查是否就是污染源
        if var_name in tainted_sources:
            return True
            
        # 2. 检查赋值链
        if var_name in self.assignments:
            for source_node in self.assignments[var_name]:
                # 检查赋值来源是否包含污染源
                # 这里做非常简单的字符串/类型检查
                # 实际需要递归追踪 source_node 的组成部分
                
                # 模拟：如果右值包含 tx.origin
                # 在真实 AST 中，需要深入 source_node 结构查找 Identifier
                source_code = str(source_node) 
                # 注意：这里我们没有源码映射，只能盲猜或者依赖更复杂的 AST 解析
                # 为了教学，我们假设如果 source_node 里有特定的操作符或成员访问
                
                # 临时方案：如果右侧表达式里包含特定的成员访问
                if self._check_node_for_taint(source_node, tainted_sources):
                    return True
                    
        return False

    def _check_node_for_taint(self, node, tainted_sources):
        # 递归检查节点是否包含污染源
        node_type = node.get('nodeType')
        
        if node_type == 'MemberAccess':
            member_name = node.get('memberName')
            expression = node.get('expression')
            if expression:
                base_name = expression.get('name') or (expression.get('attributes') or {}).get('value')
                full_name = f"{base_name}.{member_name}"
                if full_name in tainted_sources:
                    return True
        
        # 检查子节点
        # ... (省略复杂的递归逻辑，保持教学简单性)
        return False
