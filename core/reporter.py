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


class HTMLReportGenerator:
    """
    HTML 报告生成器，生成美观的可视化报告
    """
    
    @staticmethod
    def generate_html_report(
        report_data: Dict[str, Any],
        output_path: str = "sca_report.html"
    ) -> str:
        """
        生成 HTML 格式的可视化报告
        
        Args:
            report_data: Slither 风格的报告数据
            output_path: 输出文件路径
        
        Returns:
            生成的 HTML 内容
        """
        html_content = HTMLReportGenerator._generate_html_content(report_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[*] HTML 报告已生成: {output_path}")
        return html_content
    
    @staticmethod
    def _generate_html_content(report_data: Dict[str, Any]) -> str:
        """
        生成 HTML 内容
        """
        metadata = report_data.get('analysis_metadata', {})
        summary = report_data.get('summary', {})
        vulnerabilities = report_data.get('vulnerabilities', [])
        informational = report_data.get('informational_findings', [])
        contracts = report_data.get('contracts_analyzed', [])
        
        # 合并所有发现并排序
        all_findings = vulnerabilities + informational
        severity_order = {'High': 0, 'Medium': 1, 'Low': 2, 'Informational': 3}
        all_findings.sort(key=lambda x: severity_order.get(x.get('severity', 'Low'), 4))
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能合约安全审计报告 - {metadata.get('target', 'Unknown')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #e0e0e0;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(30, 30, 46, 0.95);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 40px;
            text-align: center;
            border-bottom: 3px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: white;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .header p {{
            font-size: 1.1em;
            color: rgba(255, 255, 255, 0.9);
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #8b5cf6;
            border-bottom: 2px solid rgba(139, 92, 246, 0.3);
            padding-bottom: 10px;
        }}
        
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metadata-card {{
            background: rgba(45, 45, 68, 0.8);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            padding: 20px;
        }}
        
        .metadata-label {{
            font-size: 0.9em;
            color: #9ca3af;
            margin-bottom: 8px;
        }}
        
        .metadata-value {{
            font-size: 1.2em;
            font-weight: 600;
            color: #e0e0e0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(45, 45, 68, 0.8);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            border: 2px solid transparent;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card.total {{
            border-color: rgba(139, 92, 246, 0.5);
        }}
        
        .stat-card.high {{
            border-color: rgba(239, 68, 68, 0.5);
            background: rgba(239, 68, 68, 0.1);
        }}
        
        .stat-card.medium {{
            border-color: rgba(251, 191, 36, 0.5);
            background: rgba(251, 191, 36, 0.1);
        }}
        
        .stat-card.low {{
            border-color: rgba(59, 130, 246, 0.5);
            background: rgba(59, 130, 246, 0.1);
        }}
        
        .stat-card.info {{
            border-color: rgba(107, 114, 128, 0.5);
            background: rgba(107, 114, 128, 0.1);
        }}
        
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-card.high .stat-number {{ color: #ef4444; }}
        .stat-card.medium .stat-number {{ color: #fbbf24; }}
        .stat-card.low .stat-number {{ color: #3b82f6; }}
        .stat-card.info .stat-number {{ color: #6b7280; }}
        .stat-card.total .stat-number {{ color: #8b5cf6; }}
        
        .stat-label {{
            font-size: 1em;
            color: #9ca3af;
        }}
        
        .vulnerability-card {{
            background: rgba(45, 45, 68, 0.8);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 4px solid;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .vulnerability-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        
        .vulnerability-card.high {{ border-left-color: #ef4444; }}
        .vulnerability-card.medium {{ border-left-color: #fbbf24; }}
        .vulnerability-card.low {{ border-left-color: #3b82f6; }}
        .vulnerability-card.informational {{ border-left-color: #6b7280; }}
        
        .vuln-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        
        .vuln-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 8px;
        }}
        
        .vuln-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 0.9em;
            color: #9ca3af;
            margin-bottom: 12px;
        }}
        
        .vuln-meta span {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .severity-badge.high {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }}
        
        .severity-badge.medium {{
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
            border: 1px solid #fbbf24;
        }}
        
        .severity-badge.low {{
            background: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
            border: 1px solid #3b82f6;
        }}
        
        .severity-badge.informational {{
            background: rgba(107, 114, 128, 0.2);
            color: #6b7280;
            border: 1px solid #6b7280;
        }}
        
        .vuln-description {{
            color: #d1d5db;
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        
        .code-block {{
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid rgba(75, 85, 99, 0.5);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
        }}
        
        .code-block code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #a5d6ff;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        
        .fix-suggestion {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }}
        
        .fix-title {{
            color: #10b981;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .fix-title::before {{
            content: "💡";
        }}
        
        .fix-content {{
            color: #d1d5db;
            line-height: 1.6;
        }}
        
        .swc-link {{
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .swc-link:hover {{
            text-decoration: underline;
        }}
        
        .no-issues {{
            text-align: center;
            padding: 60px 20px;
            background: rgba(16, 185, 129, 0.1);
            border: 2px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
        }}
        
        .no-issues-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        
        .no-issues-title {{
            font-size: 1.5em;
            color: #10b981;
            margin-bottom: 10px;
        }}
        
        .no-issues-text {{
            color: #9ca3af;
        }}
        
        .footer {{
            background: rgba(17, 24, 39, 0.8);
            padding: 20px;
            text-align: center;
            color: #6b7280;
            border-top: 1px solid rgba(75, 85, 99, 0.5);
        }}
        
        .chart-container {{
            background: rgba(45, 45, 68, 0.8);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #e0e0e0;
        }}
        
        .bar-chart {{
            display: flex;
            align-items: flex-end;
            height: 200px;
            gap: 20px;
            padding: 20px;
        }}
        
        .bar {{
            flex: 1;
            background: linear-gradient(to top, var(--bar-color) 0%, var(--bar-color-light) 100%);
            border-radius: 8px 8px 0 0;
            position: relative;
            transition: transform 0.3s ease;
            min-height: 10px;
        }}
        
        .bar:hover {{
            transform: translateY(-5px);
        }}
        
        .bar-label {{
            position: absolute;
            bottom: -35px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9em;
            color: #9ca3af;
            white-space: nowrap;
        }}
        
        .bar-value {{
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .metadata-grid {{
                grid-template-columns: 1fr;
            }}
            
            .vuln-header {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🛡️ 智能合约安全审计报告</h1>
            <p>Smart Contract Analyzer v{report_data.get('sca_version', '1.0.0')}</p>
        </div>
        
        <!-- Content -->
        <div class="content">
            <!-- 元数据 -->
            <div class="section">
                <h2 class="section-title">📋 分析信息</h2>
                <div class="metadata-grid">
                    <div class="metadata-card">
                        <div class="metadata-label">目标文件</div>
                        <div class="metadata-value">{metadata.get('target', 'N/A')}</div>
                    </div>
                    <div class="metadata-card">
                        <div class="metadata-label">Solidity 版本</div>
                        <div class="metadata-value">{metadata.get('solidity_version', 'Unknown')}</div>
                    </div>
                    <div class="metadata-card">
                        <div class="metadata-label">分析时间</div>
                        <div class="metadata-value">{HTMLReportGenerator._format_timestamp(metadata.get('timestamp', ''))}</div>
                    </div>
                    <div class="metadata-card">
                        <div class="metadata-label">分析耗时</div>
                        <div class="metadata-value">{metadata.get('analysis_duration_seconds', 0):.2f} 秒</div>
                    </div>
                </div>
            </div>
            
            <!-- 统计汇总 -->
            <div class="section">
                <h2 class="section-title">📊 漏洞统计</h2>
                <div class="stats-grid">
                    <div class="stat-card total">
                        <div class="stat-number">{summary.get('total_vulnerabilities', 0)}</div>
                        <div class="stat-label">总漏洞数</div>
                    </div>
                    <div class="stat-card high">
                        <div class="stat-number">{summary.get('high_severity', 0)}</div>
                        <div class="stat-label">高危</div>
                    </div>
                    <div class="stat-card medium">
                        <div class="stat-number">{summary.get('medium_severity', 0)}</div>
                        <div class="stat-label">中危</div>
                    </div>
                    <div class="stat-card low">
                        <div class="stat-number">{summary.get('low_severity', 0)}</div>
                        <div class="stat-label">低危</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-number">{summary.get('informational', 0)}</div>
                        <div class="stat-label">信息性</div>
                    </div>
                </div>
                
                <!-- 可视化图表 -->
                <div class="chart-container">
                    <div class="chart-title">漏洞分布</div>
                    <div class="bar-chart">
                        {HTMLReportGenerator._generate_bar_chart(summary)}
                    </div>
                </div>
            </div>
            
            <!-- 漏洞详情 -->
            <div class="section">
                <h2 class="section-title">🔍 漏洞详情</h2>
                {HTMLReportGenerator._generate_vulnerability_cards(all_findings) if all_findings else '<div class="no-issues"><div class="no-issues-icon">✅</div><div class="no-issues-title">未发现安全漏洞</div><div class="no-issues-text">该合约通过了所有安全检测规则</div></div>'}
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated by Smart Contract Analyzer | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """格式化时间戳"""
        if not timestamp:
            return 'N/A'
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    @staticmethod
    def _generate_bar_chart(summary: Dict[str, Any]) -> str:
        """生成柱状图 HTML"""
        high = summary.get('high_severity', 0)
        medium = summary.get('medium_severity', 0)
        low = summary.get('low_severity', 0)
        info = summary.get('informational', 0)
        
        max_val = max(high, medium, low, info, 1)
        
        bars = []
        data = [
            ('高危', high, '#ef4444', '#fca5a5'),
            ('中危', medium, '#fbbf24', '#fcd34d'),
            ('低危', low, '#3b82f6', '#93c5fd'),
            ('信息性', info, '#6b7280', '#9ca3af'),
        ]
        
        for label, value, color, color_light in data:
            height_percent = (value / max_val * 100) if max_val > 0 else 10
            bars.append(f'''
                <div class="bar" style="height: {height_percent}%; --bar-color: {color}; --bar-color-light: {color_light};">
                    <div class="bar-value" style="color: {color};">{value}</div>
                    <div class="bar-label">{label}</div>
                </div>
            ''')
        
        return ''.join(bars)
    
    @staticmethod
    def _generate_vulnerability_cards(findings: List[Dict[str, Any]]) -> str:
        """生成漏洞卡片 HTML"""
        cards = []
        
        for finding in findings:
            severity = finding.get('severity', 'Low').lower()
            title = finding.get('title', 'Security Issue')
            description = finding.get('description', '')
            swc_id = finding.get('swc_id', '')
            detector = finding.get('detector', '')
            location = finding.get('location', {})
            contract = finding.get('contract', '')
            function = finding.get('function', '')
            code_snippet = finding.get('code_snippet', '')
            fix_suggestion = finding.get('fix_suggestion', '')
            confidence = finding.get('confidence', 'High')
            vuln_id = finding.get('id', '')
            
            swc_link = ''
            if swc_id and swc_id.startswith('SWC-'):
                swc_link = f'<a href="https://swcregistry.io/docs/{swc_id}" target="_blank" class="swc-link">{swc_id}</a>'
            else:
                swc_link = swc_id
            
            card = f'''
                <div class="vulnerability-card {severity}">
                    <div class="vuln-header">
                        <div>
                            <div class="vuln-title">{title}</div>
                            <div class="vuln-meta">
                                <span><span class="severity-badge {severity}">{finding.get('severity', 'Low')}</span></span>
                                <span>🆔 {vuln_id}</span>
                                {f'<span>🔍 {detector}</span>' if detector else ''}
                                {f'<span>📄 {swc_link}</span>' if swc_id else ''}
                            </div>
                        </div>
                    </div>
                    
                    <div class="vuln-description">{description}</div>
                    
                    <div class="vuln-meta">
                        {f'<span>📦 合约: <strong>{contract}</strong></span>' if contract else ''}
                        {f'<span>⚙️ 函数: <strong>{function}</strong></span>' if function else ''}
                        {f'<span>📍 行 {location.get("start_line", 0)}-{location.get("end_line", 0)}</span>' if location else ''}
                        <span>🎯 置信度: <strong>{confidence}</strong></span>
                    </div>
                    
                    {f'<div class="code-block"><code>{HTMLReportGenerator._escape_html(code_snippet)}</code></div>' if code_snippet else ''}
                    
                    {f'<div class="fix-suggestion"><div class="fix-title">修复建议</div><div class="fix-content">{fix_suggestion}</div></div>' if fix_suggestion else ''}
                </div>
            '''
            
            cards.append(card)
        
        return ''.join(cards)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML 特殊字符"""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
