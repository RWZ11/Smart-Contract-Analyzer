import json
import xml.etree.ElementTree as ET
from datetime import datetime

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
