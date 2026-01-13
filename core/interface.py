from abc import ABC, abstractmethod

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
        """风险等级: High, Medium, Low"""
        pass

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
