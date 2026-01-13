import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Upload, FileText, AlertTriangle, Download } from "lucide-react";
import axios from 'axios';
import { AnalysisReport, ApiResponse } from '@/types/report';
import ReportSummary from '@/components/ReportSummary';
import VulnerabilityList from '@/components/VulnerabilityList';

export default function Analyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setReport(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<ApiResponse>('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.status === 'success' && response.data.report) {
        setReport(response.data.report);
      } else {
        setError("分析失败，请重试。");
      }
    } catch (err) {
      console.error(err);
      setError("分析服务暂时不可用，请确保后端服务已启动。");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDownloadReport = () => {
    if (!report) return;
    
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sca_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-surface p-8 rounded-lg border border-gray-700 text-center space-y-6">
        <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto">
          <Upload className="text-gray-400" size={32} />
        </div>
        <div>
          <h2 className="text-2xl font-semibold mb-2">上传智能合约</h2>
          <p className="text-gray-400">支持 .sol 文件，单次最大 5MB</p>
        </div>
        
        <input 
          type="file" 
          accept=".sol" 
          onChange={handleFileChange} 
          className="hidden" 
          id="file-upload"
        />
        <label htmlFor="file-upload">
          <Button variant="outline" className="cursor-pointer" asChild>
            <span>选择文件</span>
          </Button>
        </label>
        
        {file && (
          <div className="flex items-center justify-center gap-2 text-primary">
            <FileText size={16} />
            <span>{file.name}</span>
          </div>
        )}

        {file && (
          <Button onClick={handleAnalyze} disabled={isAnalyzing} className="w-full max-w-xs">
            {isAnalyzing ? "正在分析..." : "开始审计"}
          </Button>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-md text-red-500 flex items-center gap-2">
          <AlertTriangle size={20} />
          {error}
        </div>
      )}

      {report && (
        <div className="space-y-6">
          {/* 下载报告按钮 */}
          <div className="flex justify-end">
            <Button
              onClick={handleDownloadReport}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download size={18} />
              下载报告 (JSON)
            </Button>
          </div>

          {/* 报告汇总 */}
          <ReportSummary 
            summary={report.summary} 
            metadata={report.analysis_metadata}
          />

          {/* 漏洞列表 */}
          <VulnerabilityList
            vulnerabilities={report.vulnerabilities}
            informationalFindings={report.informational_findings}
          />
        </div>
      )}
    </div>
  );
}
