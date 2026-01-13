import argparse
import os
import sys
from core.engine import AnalyzerEngine
from core.reporter import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Mini-Slither: 智能合约静态分析工具教学版")
    parser.add_argument("path", help="要分析的 .sol 文件或目录路径")
    parser.add_argument("--format", choices=["text", "json", "junit", "sarif"], default="text", help="输出格式")
    
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

    for file_path in files_to_analyze:
        print(f"正在分析: {os.path.basename(file_path)}")
        results = engine.analyze_file(file_path)
        
        if results:
            for issue in results:
                total_issues += 1
                issue['file'] = file_path # 补充文件路径用于报告
                all_results.append(issue)
                
                # 仅在 text 模式下实时打印
                if args.format == "text":
                    print(f"  [!] 发现漏洞: {issue['desc']}")
                    print(f"      类型: {issue['detector']} | 严重程度: {issue['severity']}")
                    print(f"      位置: 第 {issue['line']} 行")
                    if 'code' in issue:
                        print(f"      代码: {issue['code']}")
                    print("")
        else:
            if args.format == "text":
                print("  [OK] 未发现已知漏洞")
        if args.format == "text":
            print("-" * 60)

    print(f"[*] 分析完成。共发现 {total_issues} 个问题。")
    
    # 生成报告
    if args.format == "json":
        ReportGenerator.generate_json(all_results)
    elif args.format == "junit":
        ReportGenerator.generate_junit(all_results)
    elif args.format == "sarif":
        ReportGenerator.generate_sarif(all_results)

if __name__ == "__main__":
    main()
