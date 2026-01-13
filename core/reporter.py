import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
import os
import time

class ReportGenerator:
    @staticmethod
    def generate_json(results, output_path="report.json"):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"[*] JSON 报告已生成: {output_path}")

    @staticmethod
    def generate_junit(results, output_path="junit.xml"):
        testsuites = ET.Element("testsuites")
        testsuite = ET.SubElement(testsuites, "testsuite", name="SmartContractSecurityChecks", tests=str(len(results)))
        
        for issue in results:
            testcase = ET.SubElement(testsuite, "testcase", 
                                     classname=issue.get('detector', 'Unknown'), 
                                     name=f"{issue.get('desc')} at line {issue.get('line')}")
            failure = ET.SubElement(testcase, "failure", message=issue.get('msg'))
            failure.text = f"Severity: {issue.get('severity')}\nFile: {issue.get('file', 'unknown')}\nLine: {issue.get('line')}\nCode: {issue.get('code', '')}"

        tree = ET.ElementTree(testsuites)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"[*] JUnit 报告已生成: {output_path}")

    @staticmethod
    def generate_sarif(results, output_path="report.sarif"):
        # 简化的 SARIF 格式
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Smart-Contract-Analyzer",
                        "version": "1.0.0",
                        "rules": [] 
                    }
                },
                "results": []
            }]
        }
        
        for issue in results:
            sarif['runs'][0]['results'].append({
                "ruleId": issue.get('detector'),
                "level": "error" if issue.get('severity') == "High" else "warning",
                "message": {
                    "text": issue.get('msg')
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": issue.get('file', '').replace('\\', '/')
                        },
                        "region": {
                            "startLine": issue.get('line', 1)
                        }
                    }
                }]
            })
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif, f, indent=4)
        print(f"[*] SARIF 报告已生成: {output_path}")


class SlitherReportGenerator:
    """
    参考 Slither 的报告生成器，生成符合行业标准的结构化 JSON 报告
    """
    
    VERSION = "1.0.0"
    
    @staticmethod
    def generate_slither_report(
        results: List[Dict[str, Any]],
        contracts_info: List[Dict[str, Any]],
        analysis_metadata: Dict[str, Any],
        output_path: str = "sca_report.json"
    ) -> Dict[str, Any]:
        """
        生成符合 Slither 风格的完整 JSON 报告
        
        Args:
            results: 检测器返回的漏洞列表
            contracts_info: 分析的合约信息列表
            analysis_metadata: 分析元信息（目标、版本、耗时等）
            output_path: 输出文件路径
        
        Returns:
            完整的报告字典
        """
        # 分类漏洞和信息性发现
        vulnerabilities = []
        informational_findings = []
        
        vuln_id_counter = 1
        info_id_counter = 1
        
        for result in results:
            severity = result.get('severity', 'Low')
            
            # 提取代码片段
            code_snippet = result.get('code', '')
            if not code_snippet and result.get('line'):
                # 如果没有代码片段，尝试从原始内容提取
                code_snippet = result.get('msg', '')[:200]  # 限制长度
            
            # 构建位置信息
            location = {
                "file": result.get('file', ''),
                "start_line": result.get('line', 0),
                "end_line": result.get('end_line', result.get('line', 0))
            }
            
            # 添加 source_mapping（如果可用）
            if result.get('source_mapping'):
                location['source_mapping'] = result['source_mapping']
            
            # 构建漏洞/发现项
            item = {
                "detector": result.get('detector', 'unknown'),
                "severity": severity,
                "swc_id": result.get('swc_id', result.get('detector', '')),
                "title": result.get('title', result.get('desc', 'Security Issue')),
                "description": result.get('desc', result.get('msg', '')),
                "contract": result.get('contract', ''),
                "function": result.get('function', None),
                "location": location,
                "code_snippet": code_snippet,
                "fix_suggestion": result.get('fix_suggestion', 'Please review the code and apply security best practices.'),
                "confidence": result.get('confidence', 'High')
            }
            
            # 根据严重级别分类
            if severity in ['High', 'Medium', 'Low']:
                item['id'] = f"VULN-{vuln_id_counter:03d}"
                vuln_id_counter += 1
                vulnerabilities.append(item)
            else:  # Informational, Info 等
                item['id'] = f"INFO-{info_id_counter:03d}"
                info_id_counter += 1
                informational_findings.append(item)
        
        # 生成汇总统计
        summary = {
            "total_vulnerabilities": len(vulnerabilities),
            "high_severity": sum(1 for v in vulnerabilities if v['severity'] == 'High'),
            "medium_severity": sum(1 for v in vulnerabilities if v['severity'] == 'Medium'),
            "low_severity": sum(1 for v in vulnerabilities if v['severity'] == 'Low'),
            "informational": len(informational_findings),
            "total_contracts_analyzed": len(contracts_info)
        }
        
        # 构建完整报告
        report = {
            "sca_version": SlitherReportGenerator.VERSION,
            "analysis_metadata": analysis_metadata,
            "contracts_analyzed": contracts_info,
            "vulnerabilities": vulnerabilities,
            "informational_findings": informational_findings,
            "summary": summary
        }
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[*] Slither 风格 JSON 报告已生成: {output_path}")
        print(f"    - 总漏洞数: {summary['total_vulnerabilities']}")
        print(f"    - 高危: {summary['high_severity']}, 中危: {summary['medium_severity']}, 低危: {summary['low_severity']}")
        print(f"    - 信息性发现: {summary['informational']}")
        
        return report
    
    @staticmethod
    def create_analysis_metadata(
        target: str,
        solidity_version: str = None,
        analysis_duration: float = 0.0,
        framework: str = None
    ) -> Dict[str, Any]:
        """
        创建分析元信息
        
        Args:
            target: 分析目标路径
            solidity_version: Solidity 版本
            analysis_duration: 分析耗时（秒）
            framework: 使用的框架（hardhat/foundry/brownie）
        
        Returns:
            分析元信息字典
        """
        metadata = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "target": target,
            "analysis_duration_seconds": round(analysis_duration, 2)
        }
        
        if solidity_version:
            metadata["solidity_version"] = solidity_version
        
        if framework:
            metadata["framework"] = framework
        
        return metadata
    
    @staticmethod
    def extract_contracts_info(ast: Dict[str, Any], filename: str, content: str) -> List[Dict[str, Any]]:
        """
        从 AST 中提取合约信息
        
        Args:
            ast: 抽象语法树
            filename: 源文件名
            content: 源代码内容
        
        Returns:
            合约信息列表
        """
        contracts = []
        
        if not ast:
            return contracts
        
        def visit_node(node):
            if node.get('nodeType') == 'ContractDefinition':
                contract_name = node.get('name', 'Unknown')
                
                # 获取行号范围
                src = node.get('src', '0:0:0')
                parts = src.split(':')
                if len(parts) >= 2:
                    offset = int(parts[0])
                    length = int(parts[1])
                    start_line = content[:offset].count('\n') + 1
                    end_line = content[:offset + length].count('\n') + 1
                else:
                    start_line = 1
                    end_line = 1
                
                # 检查是否为可升级合约
                is_upgradeable = False
                for base_contract in node.get('baseContracts', []):
                    base_name = base_contract.get('baseName', {}).get('name', '')
                    if 'Upgradeable' in base_name or 'Proxy' in base_name:
                        is_upgradeable = True
                        break
                
                contracts.append({
                    "name": contract_name,
                    "source_file": filename,
                    "source_lines": {
                        "start": start_line,
                        "end": end_line
                    },
                    "is_upgradeable": is_upgradeable
                })
        
        def walk(node):
            if not isinstance(node, dict):
                return
            visit_node(node)
            for key in ['nodes', 'children']:
                children = node.get(key, [])
                if isinstance(children, list):
                    for child in children:
                        walk(child)
        
        walk(ast)
        return contracts
