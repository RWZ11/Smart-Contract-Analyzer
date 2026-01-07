import React, { useState } from 'react';
import { Play, FileCode, AlertTriangle } from 'lucide-react';
import { analyzeContractCode } from './services/geminiService';
import { AnalysisReport } from './types';
import AnalysisResults from './components/AnalysisResults';
import { DEFAULT_CONTRACT } from './constants';

const App: React.FC = () => {
  const [code, setCode] = useState(DEFAULT_CONTRACT);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const result = await analyzeContractCode(code);
      setReport(result);
    } catch (err: any) {
      setError(err.message || "分析过程中发生意外错误。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200 font-sans overflow-hidden">
      {/* Sidebar */}
      <div className="w-16 lg:w-20 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-6 gap-6 z-20">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
          <ShieldIcon className="text-white" />
        </div>
        <div className="flex-1 flex flex-col gap-4 w-full items-center">
            <SidebarIcon icon={<FileCode className="w-5 h-5" />} active={true} />
        </div>
      </div>

      {/* Main Content Split */}
      <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden">
        
        {/* Editor Section */}
        <div className={`flex flex-col h-full border-r border-slate-800 transition-all duration-300 ${report ? 'w-full lg:w-5/12' : 'w-full'}`}>
          <div className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6">
            <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-slate-400">VulnerableBank.sol</span>
            </div>
            <button 
              onClick={handleAnalyze}
              disabled={loading}
              className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                loading 
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'
              }`}
            >
              {loading ? (
                <>分析中...</>
              ) : (
                <><Play className="w-4 h-4 fill-current" /> 开始分析</>
              )}
            </button>
          </div>
          
          <div className="flex-1 relative bg-slate-950">
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-full bg-slate-950 text-slate-300 font-mono text-sm p-6 resize-none focus:outline-none leading-relaxed"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Results Section */}
        {report && (
          <div className="w-full lg:w-7/12 h-full bg-slate-900 flex flex-col overflow-hidden animate-in fade-in slide-in-from-right-10 duration-500">
             <AnalysisResults report={report} />
          </div>
        )}

        {/* Empty State / Loading State Overlay (if no report yet and loading) */}
        {!report && (
            <div className={`hidden lg:flex w-7/12 items-center justify-center bg-slate-900 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
                <div className="text-center max-w-md p-8">
                    {loading ? (
                        <div className="flex flex-col items-center">
                            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                            <h2 className="text-2xl font-bold text-slate-200 mb-2">正在分析合约</h2>
                            <p className="text-slate-400">正在运行 SSA 转换、污点追踪和漏洞检测引擎...</p>
                        </div>
                    ) : (
                        <div>
                             <div className="w-20 h-20 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6 transform rotate-12 border border-slate-700">
                                <FileCode className="w-10 h-10 text-slate-500" />
                            </div>
                            <h2 className="text-2xl font-bold text-slate-200 mb-3">准备分析</h2>
                            <p className="text-slate-400 leading-relaxed">
                                请在左侧粘贴您的 Solidity 或 Vyper 代码，然后点击“开始分析”。
                                Sentinels 使用先进的基于 IR 的引擎来检测重入攻击、逻辑错误和安全缺陷。
                            </p>
                            {error && (
                                <div className="mt-6 p-4 bg-red-900/20 border border-red-900/50 rounded-lg flex items-center gap-3 text-left">
                                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                                    <p className="text-red-300 text-sm">{error}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        )}
      </div>
    </div>
  );
};

// Sub-components for Sidebar
const SidebarIcon: React.FC<{ icon: React.ReactNode, active?: boolean, onClick?: () => void }> = ({ icon, active, onClick }) => (
    <button 
        onClick={onClick}
        className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            active 
            ? 'bg-slate-800 text-blue-400 border border-slate-700' 
            : 'text-slate-500 hover:bg-slate-800 hover:text-slate-300'
        }`}
    >
        {icon}
    </button>
);

const ShieldIcon = ({ className }: { className?: string }) => (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={`w-6 h-6 ${className}`}
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
);

export default App;