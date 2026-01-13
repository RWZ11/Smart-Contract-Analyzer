from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .context import AnalysisContext

class BaseDetector(ABC):
    """
    所有漏洞检测插件的基类 (Abstract Base Class)
    """
    
    @property
    @abstractmethod
    def id(self):
        """规则唯一ID"""
        pass

    @property
    @abstractmethod
    def description(self):
        """规则描述"""
        pass

    @property
    @abstractmethod
    def severity(self):
        """风险等级: High, Medium, Low, Informational"""
        pass

    @property
    def title(self):
        """漏洞标题（可选）"""
        return self.description

    @property
    def swc_id(self):
        """SWC Registry 漏洞编号（可选）"""
        return self.id if self.id.startswith('SWC-') else None

    @property
    def confidence(self):
        """置信度: High, Medium, Low（可选，默认 High）"""
        return "High"

    @property
    def fix_suggestion(self):
        """修复建议（可选）"""
        return "Please review the code and apply security best practices."

    @abstractmethod
    def check(self, content: str, filename: str, ast: dict = None) -> list:
        """
        执行检测逻辑
        :param content: 合约源代码内容
        :param filename: 文件名
        :param ast: 抽象语法树 (字典结构)
        :return: 发现的问题列表 [{"line": 1, "msg": "..."}]
        """
        pass

    # 标准化接口：新增 run(ctx)，统一由引擎调用
    # 旧插件无需改动：默认使用 check 适配
    def run(self, ctx: AnalysisContext) -> List[Dict[str, Any]]:
        try:
            return self.check(ctx.content, ctx.filename, ast=ctx.ast)
        except TypeError:
            # 部分新插件可能接受 ir 参数
            try:
                return self.check(ctx.content, ctx.filename, ast=ctx.ast, ir=ctx.ir)  # type: ignore
            except Exception:
                return []

    # 统一问题输出的帮助方法
    def report(self, line: int, msg: str) -> Dict[str, Any]:
        return {"line": line, "msg": msg}
