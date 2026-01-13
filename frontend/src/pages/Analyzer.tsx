import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Upload, FileText, AlertTriangle, CheckCircle } from "lucide-react";
import axios from 'axios';

interface Vulnerability {
  line: number;
  msg: string;
  detector: string;
  severity: string;
}

export default function Analyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<Vulnerability[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResults(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 实际调用后端 API
      const response = await axios.post('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.issues) {
        setResults(response.data.issues);
      } else {
        setResults([]);
      }
    } catch (err) {
      console.error(err);
      setError("分析服务暂时不可用，请确保后端服务已启动。");
    } finally {
      setIsAnalyzing(false);
    }
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

      {results && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <CheckCircle className="text-green-500" />
            分析报告
          </h3>
          <div className="grid gap-4">
            {results.map((issue, idx) => (
              <div key={idx} className="bg-surface p-4 rounded-lg border border-gray-700 flex gap-4 items-start">
                <div className={`mt-1 w-2 h-2 rounded-full ${
                  issue.severity === 'High' ? 'bg-red-500' : 
                  issue.severity === 'Medium' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <div>
                  <h4 className="font-medium text-lg">{issue.msg}</h4>
                  <div className="text-sm text-gray-400 mt-1 flex gap-4">
                    <span>行号: {issue.line}</span>
                    <span>类型: {issue.detector}</span>
                    <span className={`${
                       issue.severity === 'High' ? 'text-red-400' : 
                       issue.severity === 'Medium' ? 'text-yellow-400' : 'text-blue-400'
                    }`}>严重程度: {issue.severity}</span>
                  </div>
                </div>
              </div>
            ))}
            {results.length === 0 && (
              <div className="text-center py-8 text-gray-400">未发现明显漏洞</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
