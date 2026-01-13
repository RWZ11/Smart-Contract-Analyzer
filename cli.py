import argparse
import os
import sys
import time
from core.engine import AnalyzerEngine
from core.reporter import ReportGenerator, SlitherReportGenerator
from core.ast_parser import ASTParser

def main():
    parser = argparse.ArgumentParser(description="Mini-Slither: 智能合约静态分析工具教学版")
    parser.add_argument("path", help="要分析的 .sol 文件或目录路径")
    parser.add_argument("--format", choices=["text", "json", "junit", "sarif", "slither"], default="text", help="输出格式")
    parser.add_argument("--output", "-o", help="报告输出路径")
    
    args = parser.parse_args()
    
    print(f"[*] 正在初始化分析引擎...")
    engine = AnalyzerEngine()
    engine.load_plugins()
    
    target_path = args.path
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
        SlitherReportGenerator.generate_slither_report(
            results=all_results,
            contracts_info=all_contracts,
            analysis_metadata=analysis_metadata,
            output_path=output_path
        )

if __name__ == "__main__":
    main()
