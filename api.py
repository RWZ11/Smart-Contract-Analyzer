from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.engine import AnalyzerEngine
from core.reporter import SlitherReportGenerator
from core.ast_parser import ASTParser
import shutil
import os
import uuid
import time

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
