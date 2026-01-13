import re
from core.interface import BaseDetector
from core.data_flow import DataFlowAnalyzer

class UnprotectedWithdrawDetector(BaseDetector):
    @property
    def id(self):
        return "SWC-105"

    @property
    def description(self):
        return "检测到未受保护的资金提取 (Unprotected Ether Withdrawal)"

    @property
    def severity(self):
        return "High"

    def check(self, content: str, filename: str, ast: dict = None) -> list:
        issues = []
        
        # 增强版：同时检查 selfdestruct
        if 'selfdestruct' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'selfdestruct' in line and '//' not in line:
                    if 'owner' not in line and 'msg.sender' not in line and 'require' not in line:
                         issues.append({
                            "line": i + 1,
                            "msg": "发现自毁函数 (selfdestruct) 且未见明显权限控制"
                        })

        # 如果有 AST，使用数据流分析
        if ast:
            analyzer = DataFlowAnalyzer(ast)
            analyzer.analyze()
            
            # 定义我们关心的敏感操作 (Sinks)
            # 在 Solidity 中，transfer/send/call.value 都是转账操作
            # 这里我们尝试寻找 transfer 的调用者
            
            def visit_node(node):
                # 寻找 .transfer(...)
                if node.get('nodeType') == 'MemberAccess' and node.get('memberName') == 'transfer':
                    # 找到一个转账操作
                    # 检查转账的目标地址是谁
                    expression = node.get('expression')
                    # 简单的污点分析：如果转账目标是 msg.sender，且没有 require(msg.sender == owner)
                    # 这是一个非常简化的逻辑
                    
                    # 在真实场景中，我们需要控制流图 (CFG) 来判断是否有 require 保护
                    # 这里我们用一个简化的启发式规则：
                    # 如果函数内有转账给 msg.sender，但函数内没有 "owner" 关键字，就报警
                    
                    # 找到当前函数定义
                    # (由于递归无法直接获取父节点，我们简化处理，假设在 analyze 过程中能获取上下文)
                    pass

            # 启发式扫描 (结合 AST 和文本)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '.transfer(' in line:
                    # 简单的污点源追踪演示
                    # 假设我们发现某一行代码把钱转给了 msg.sender
                    if 'msg.sender.transfer' in line:
                        # 检查函数内是否有权限控制
                        # 这是一个非常粗糙的实现，仅用于演示思路
                        if 'require' not in line and 'owner' not in line and 'onlyOwner' not in line:
                             issues.append({
                                "line": i + 1,
                                "msg": "发现向 msg.sender 转账且未见明显的权限控制 (High Risk)"
                            })
        
        return issues
