import argparse
import os
import sys
import time
import json
from core.engine import AnalyzerEngine
from core.reporter import ReportGenerator, SlitherReportGenerator, HTMLReportGenerator
from core.ast_parser import ASTParser

def main():
    parser = argparse.ArgumentParser(description="Mini-Slither: 智能合约静态分析工具教学版")
    parser.add_argument("path", nargs='?', help="要分析的 .sol 文件或目录路径")
    parser.add_argument("--format", choices=["text", "json", "junit", "sarif", "slither", "html"], default="text", help="输出格式")
    parser.add_argument("--output", "-o", help="报告输出路径")
    parser.add_argument("--import-report", help="导入已存在的 JSON 报告文件")
    
    args = parser.parse_args()
    
    # 导入报告功能
    if args.import_report:
        try:
            with open(args.import_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            print(f"[*] 已导入报告: {args.import_report}")
            
            # 如果指定了输出格式，转换报告
            if args.format == "html":
                output_path = args.output or "imported_report.html"
                HTMLReportGenerator.generate_html_report(report_data, output_path)
            elif args.format == "json":
                output_path = args.output or "imported_report.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                print(f"[*] JSON 报告已保存: {output_path}")
            else:
                # 显示报告摘要
                summary = report_data.get('summary', {})
                print(f"\n报告摘要:")
                print(f"  总漏洞数: {summary.get('total_vulnerabilities', 0)}")
                print(f"  高危: {summary.get('high_severity', 0)}")
                print(f"  中危: {summary.get('medium_severity', 0)}")
                print(f"  低危: {summary.get('low_severity', 0)}")
                print(f"  信息性: {summary.get('informational', 0)}")
            
            return
        except Exception as e:
            print(f"[错误] 导入报告失败: {e}")
            sys.exit(1)
    
    # 检查是否提供了 path 参数
    if not args.path:
        print("[错误] 请提供要分析的文件路径，或使用 --import-report 导入报告")
        sys.exit(1)
    
    target_path = args.path
    
    print(f"[*] 正在初始化分析引擎...")
    if not os.path.exists(target_path):
        print(f"[错误] 路径不存在: {target_path}")
        sys.exit(1)

    files_to_analyze = []
    if os.path.isfile(target_path):
        files_to_analyze.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.endswith(".sol"):
                    files_to_analyze.append(os.path.join(root, file))
    
    print(f"[*] 找到 {len(files_to_analyze)} 个合约文件，开始分析...")
    print("-" * 60)

    total_issues = 0
    all_results = []
    all_contracts = []
    start_time = time.time()
    solidity_version = None

    for file_path in files_to_analyze:
        print(f"正在分析: {os.path.basename(file_path)}")
        results = engine.analyze_file(file_path)
        
        # 提取合约信息（用于 Slither 报告）
        if args.format == "slither":
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast_parser = ASTParser()
                ast = ast_parser.parse(content)
                if ast:
                    contracts = SlitherReportGenerator.extract_contracts_info(ast, file_path, content)
                    all_contracts.extend(contracts)
                    
                    # 提取 Solidity 版本
                    if not solidity_version:
                        solidity_version = engine._extract_solidity_version(content)
            except Exception as e:
                print(f"  [警告] 无法提取合约信息: {e}")
        
        if results:
            for issue in results:
                total_issues += 1
                issue['file'] = file_path  # 补充文件路径用于报告
                all_results.append(issue)
                
                # 仅在 text 模式下实时打印
                if args.format == "text":
                    print(f"  [!] 发现漏洞: {issue['desc']}")
                    print(f"      类型: {issue['detector']} | 严重程度: {issue['severity']}")
                    print(f"      位置: 第 {issue['line']} 行")
                    if 'code' in issue:
                        print(f"      代码: {issue['code'][:100]}...")  # 限制长度
                    print("")
        else:
            if args.format == "text":
                print("  [OK] 未发现已知漏洞")
        if args.format == "text":
            print("-" * 60)

    analysis_duration = time.time() - start_time
    print(f"[*] 分析完成。共发现 {total_issues} 个问题。耗时: {analysis_duration:.2f}秒")
    
    # 生成报告
    if args.format == "json":
        output_path = args.output or "report.json"
        ReportGenerator.generate_json(all_results, output_path)
    elif args.format == "junit":
        output_path = args.output or "junit.xml"
        ReportGenerator.generate_junit(all_results, output_path)
    elif args.format == "sarif":
        output_path = args.output or "report.sarif"
        ReportGenerator.generate_sarif(all_results, output_path)
    elif args.format == "slither":
        output_path = args.output or "sca_report.json"
        # 创建分析元信息
        analysis_metadata = SlitherReportGenerator.create_analysis_metadata(
            target=target_path,
            solidity_version=solidity_version,
            analysis_duration=analysis_duration,
            framework=None  # 可以通过参数传入
        )
        
        # 生成 Slither 风格报告
        report_data = SlitherReportGenerator.generate_slither_report(
            results=all_results,
            contracts_info=all_contracts,
            analysis_metadata=analysis_metadata,
            output_path=output_path
        )
    elif args.format == "html":
        # 先生成 Slither 报告数据
        analysis_metadata = SlitherReportGenerator.create_analysis_metadata(
            target=target_path,
            solidity_version=solidity_version,
            analysis_duration=analysis_duration,
            framework=None
        )
        
        # 构建报告数据（不写入文件）
        vulnerabilities = []
        informational_findings = []
        vuln_id_counter = 1
        info_id_counter = 1
        
        for result in all_results:
            severity = result.get('severity', 'Low')
            item = {
                "detector": result.get('detector', 'unknown'),
                "severity": severity,
                "swc_id": result.get('swc_id', result.get('detector', '')),
                "title": result.get('title', result.get('desc', 'Security Issue')),
                "description": result.get('desc', result.get('msg', '')),
                "contract": result.get('contract', ''),
                "function": result.get('function', None),
                "location": {
                    "file": result.get('file', ''),
                    "start_line": result.get('line', 0),
                    "end_line": result.get('end_line', result.get('line', 0))
                },
                "code_snippet": result.get('code', ''),
                "fix_suggestion": result.get('fix_suggestion', 'Please review the code and apply security best practices.'),
                "confidence": result.get('confidence', 'High')
            }
            
            if severity in ['High', 'Medium', 'Low']:
                item['id'] = f"VULN-{vuln_id_counter:03d}"
                vuln_id_counter += 1
                vulnerabilities.append(item)
            else:
                item['id'] = f"INFO-{info_id_counter:03d}"
                info_id_counter += 1
                informational_findings.append(item)
        
        summary = {
            "total_vulnerabilities": len(vulnerabilities),
            "high_severity": sum(1 for v in vulnerabilities if v['severity'] == 'High'),
            "medium_severity": sum(1 for v in vulnerabilities if v['severity'] == 'Medium'),
            "low_severity": sum(1 for v in vulnerabilities if v['severity'] == 'Low'),
            "informational": len(informational_findings),
            "total_contracts_analyzed": len(all_contracts)
        }
        
        report_data = {
            "sca_version": "1.0.0",
            "analysis_metadata": analysis_metadata,
            "contracts_analyzed": all_contracts,
            "vulnerabilities": vulnerabilities,
            "informational_findings": informational_findings,
            "summary": summary
        }
        
        output_path = args.output or "sca_report.html"
        HTMLReportGenerator.generate_html_report(report_data, output_path)

if __name__ == "__main__":
    main()
