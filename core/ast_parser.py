import solcx
from solcx import compile_source, install_solc
import re

class ASTParser:
    def __init__(self):
        # 尝试安装一个通用的 solc 版本，或者在运行时动态检查
        try:
            # 自动跳过下载，假设用户可能没网或者网络很慢，我们先不强制安装
            # 在实际生产中应该有更好的错误处理
            pass
        except Exception as e:
            print(f"[警告] Solc 初始化失败: {e}")

    def parse(self, content):
        """
        编译源代码并返回 AST
        """
        try:
            # 简单的版本探测
            version_match = re.search(r'pragma solidity \^?(\d+\.\d+\.\d+);', content)
            if version_match:
                version = version_match.group(1)
                installed_versions = [str(v) for v in solcx.get_installed_solc_versions()]
                
                if version not in installed_versions:
                    print(f"[*] 检测到合约需要 solc {version}，正在尝试安装...")
                    try:
                        install_solc(version)
                    except Exception as e:
                        print(f"[错误] 无法安装 solc {version}: {e}")
                        print("[提示] 请检查网络连接或手动安装 solc")
                        return None
                        
                solcx.set_solc_version(version)

            compiled = compile_source(content)
            # 获取第一个合约的 AST
            contract_id = list(compiled.keys())[0]
            return compiled[contract_id]['ast']
        except Exception as e:
            print(f"[错误] AST 解析失败: {e}")
            return None

    def walk(self, node, callback):
        """
        深度优先遍历 AST
        """
        if not node:
            return
        
        # 执行回调
        callback(node)

        # 遍历子节点 (不同版本的 Solidity AST 结构可能不同，这里做简单兼容)
        children = node.get('nodes') or node.get('children') or []
        for child in children:
            self.walk(child, callback)
        
        # 处理 body (FunctionDefinition 等)
        if 'body' in node and node['body']:
             self.walk(node['body'], callback)
        
        # 处理 statements (Block 等)
        if 'statements' in node and node['statements']:
            for stmt in node['statements']:
                self.walk(stmt, callback)

        # 处理 expression (ExpressionStatement 等)
        if 'expression' in node and node['expression']:
             self.walk(node['expression'], callback)

        # 处理 components (TupleExpression 等)
        if 'components' in node and node['components']:
            for comp in node['components']:
                 self.walk(comp, callback)
