from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.engine import AnalyzerEngine
from core.reporter import SlitherReportGenerator, HTMLReportGenerator
from core.ast_parser import ASTParser
import shutil
import os
import uuid
import time
import json

app = FastAPI(title="Smart Contract Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        start_time = time.time()
        
        # 初始化引擎并分析
        engine = AnalyzerEngine()
        engine.load_plugins()
        results = engine.analyze_file(file_path)
        
        # 提取合约信息
        contracts_info = []
        solidity_version = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast_parser = ASTParser()
            ast = ast_parser.parse(content)
            if ast:
                contracts_info = SlitherReportGenerator.extract_contracts_info(
                    ast, file.filename, content
                )
                solidity_version = engine._extract_solidity_version(content)
        except Exception as e:
            print(f"[警告] 无法提取合约信息: {e}")
        
        analysis_duration = time.time() - start_time
        
        # 生成 Slither 风格报告
        analysis_metadata = SlitherReportGenerator.create_analysis_metadata(
            target=file.filename,
            solidity_version=solidity_version,
            analysis_duration=analysis_duration
        )
        
        # 为结果添加文件路径
        for result in results:
            result['file'] = file.filename
        
        # 生成报告数据（不写入文件）
        report_data = SlitherReportGenerator.generate_slither_report(
            results=results,
            contracts_info=contracts_info,
            analysis_metadata=analysis_metadata,
            output_path=os.path.join(UPLOAD_DIR, f"{file_id}_report.json")
        )
        
        # Cleanup
        os.remove(file_path)
        report_file = os.path.join(UPLOAD_DIR, f"{file_id}_report.json")
        if os.path.exists(report_file):
            os.remove(report_file)
        
        return {
            "status": "success",
            "report": report_data
        }
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/html")
async def analyze_contract_html(file: UploadFile = File(...)):
    """生成 HTML 格式的报告"""
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        start_time = time.time()
        
        # 初始化引擎并分析
        engine = AnalyzerEngine()
        engine.load_plugins()
        results = engine.analyze_file(file_path)
        
        # 提取合约信息
        contracts_info = []
        solidity_version = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast_parser = ASTParser()
            ast = ast_parser.parse(content)
            if ast:
                contracts_info = SlitherReportGenerator.extract_contracts_info(
                    ast, file.filename, content
                )
                solidity_version = engine._extract_solidity_version(content)
        except Exception as e:
            print(f"[警告] 无法提取合约信息: {e}")
        
        analysis_duration = time.time() - start_time
        
        # 生成 Slither 风格报告
        analysis_metadata = SlitherReportGenerator.create_analysis_metadata(
            target=file.filename,
            solidity_version=solidity_version,
            analysis_duration=analysis_duration
        )
        
        # 为结果添加文件路径
        for result in results:
            result['file'] = file.filename
        
        # 构建报告数据
        vulnerabilities = []
        informational_findings = []
        vuln_id_counter = 1
        info_id_counter = 1
        
        for result in results:
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
            "total_contracts_analyzed": len(contracts_info)
        }
        
        report_data = {
            "sca_version": "1.0.0",
            "analysis_metadata": analysis_metadata,
            "contracts_analyzed": contracts_info,
            "vulnerabilities": vulnerabilities,
            "informational_findings": informational_findings,
            "summary": summary
        }
        
        # 生成 HTML
        html_content = HTMLReportGenerator._generate_html_content(report_data)
        
        # Cleanup
        os.remove(file_path)
        
        return HTMLResponse(content=html_content, media_type="text/html")
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/import-report")
async def import_report(file: UploadFile = File(...)):
    """导入 JSON 报告文件"""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are supported")
    
    try:
        content = await file.read()
        report_data = json.loads(content.decode('utf-8'))
        
        # 验证报告格式
        if 'summary' not in report_data or 'vulnerabilities' not in report_data:
            raise HTTPException(status_code=400, detail="Invalid report format")
        
        return {
            "status": "success",
            "report": report_data
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
