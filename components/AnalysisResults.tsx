import React, { useState } from 'react';
import { AnalysisReport, Severity } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { AlertTriangle, ShieldAlert, Bug, Code2, Network, Terminal, CheckCircle } from 'lucide-react';
import DependencyGraph from './DependencyGraph';
import { CICD_YAML } from '../constants';

interface Props {
  report: AnalysisReport;
}

const COLORS = {
  High: '#ef4444',   // Red-500
  Medium: '#f59e0b', // Amber-500
  Low: '#eab308',    // Yellow-500
  Info: '#3b82f6'    // Blue-500
};

const getSeverityLabel = (severity: string) => {
  switch (severity) {
    case 'High': return '高危';
    case 'Medium': return '中危';
    case 'Low': return '低危';
    case 'Info': return '提示';
    default: return severity;
  }
};

const AnalysisResults: React.FC<Props> = ({ report }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'ir' | 'graph' | 'cicd'>('overview');

  const pieData = [
    { name: 'High', value: report.stats.high },
    { name: 'Medium', value: report.stats.medium },
    { name: 'Low', value: report.stats.low },
  ].filter(d => d.value > 0);

  return (
    <div className="flex flex-col h-full bg-slate-900 text-slate-200">
      {/* Tabs */}
      <div className="flex border-b border-slate-700 bg-slate-950">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'overview' ? 'border-b-2 border-blue-500 text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <ShieldAlert className="w-4 h-4 mr-2" /> 漏洞概览
        </button>
        <button
          onClick={() => setActiveTab('ir')}
          className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'ir' ? 'border-b-2 border-blue-500 text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Code2 className="w-4 h-4 mr-2" /> IR 视图
        </button>
        <button
          onClick={() => setActiveTab('graph')}
          className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'graph' ? 'border-b-2 border-blue-500 text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Network className="w-4 h-4 mr-2" /> 依赖图谱
        </button>
        <button
          onClick={() => setActiveTab('cicd')}
          className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'cicd' ? 'border-b-2 border-blue-500 text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Terminal className="w-4 h-4 mr-2" /> CI/CD 集成
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Stats Cards */}
            <div className="col-span-1 space-y-6">
              <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                <h3 className="text-slate-400 text-xs uppercase font-bold tracking-wider mb-4">风险分布</h3>
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        innerRadius={40}
                        outerRadius={60}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem' }} 
                        itemStyle={{ color: '#f1f5f9' }}
                        formatter={(value, name) => [value, getSeverityLabel(name as string)]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-4 mt-2 text-xs">
                  {pieData.map(d => (
                    <div key={d.name} className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[d.name as keyof typeof COLORS] }}></span>
                      <span className="text-slate-300">{getSeverityLabel(d.name)}: {d.value}</span>
                    </div>
                  ))}
                </div>
              </div>

               <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-sm">
                <h3 className="text-slate-400 text-xs uppercase font-bold tracking-wider mb-2">代码指标</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-900 rounded-lg">
                     <p className="text-slate-500 text-xs">代码行数</p>
                     <p className="text-xl font-mono text-slate-200">{report.stats.linesOfCode}</p>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg">
                     <p className="text-slate-500 text-xs">函数数量</p>
                     <p className="text-xl font-mono text-slate-200">{report.stats.functions}</p>
                  </div>
                </div>
               </div>
            </div>

            {/* Vulnerability List */}
            <div className="col-span-1 lg:col-span-2 space-y-4">
               <h3 className="text-slate-200 font-semibold text-lg flex items-center">
                <Bug className="w-5 h-5 mr-2 text-red-400" /> 检测到的问题
               </h3>
               {report.vulnerabilities.length === 0 ? (
                 <div className="bg-green-900/20 border border-green-800 p-6 rounded-lg text-center">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                    <p className="text-green-400">未检测到漏洞。</p>
                 </div>
               ) : (
                 report.vulnerabilities.map(vuln => (
                   <div key={vuln.id} className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden group hover:border-blue-500/50 transition-colors">
                     <div className="p-4 flex items-start justify-between bg-slate-800">
                       <div className="flex items-start gap-3">
                         <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${vuln.severity === 'High' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]' : vuln.severity === 'Medium' ? 'bg-amber-500' : 'bg-yellow-500'}`} />
                         <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-slate-200">{vuln.detectorName}</h4>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase ${
                                vuln.severity === 'High' ? 'bg-red-900/30 text-red-400 border border-red-900/50' : 
                                vuln.severity === 'Medium' ? 'bg-amber-900/30 text-amber-400 border border-amber-900/50' :
                                'bg-yellow-900/30 text-yellow-400 border border-yellow-900/50'
                              }`}>
                                {getSeverityLabel(vuln.severity)}
                              </span>
                            </div>
                            <p className="text-sm text-slate-400 mt-1">{vuln.description}</p>
                         </div>
                       </div>
                       <div className="text-xs text-slate-500 font-mono">
                         {vuln.location.startLine} - {vuln.location.endLine} 行
                       </div>
                     </div>
                     <div className="px-4 py-3 bg-slate-900/50 border-t border-slate-700/50 text-sm">
                        <p className="text-blue-400 mb-1 text-xs uppercase font-bold">修复建议</p>
                        <p className="text-slate-300">{vuln.suggestion}</p>
                     </div>
                   </div>
                 ))
               )}
            </div>
          </div>
        )}

        {activeTab === 'ir' && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold mb-4 text-slate-200">中间表示 (IR) 预览</h3>
            <p className="text-slate-400 text-sm mb-4">关键执行路径的 SSA (SlithIR) 可视化。</p>
            <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm overflow-x-auto border border-slate-800">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-800">
                    <th className="py-2 px-4 w-16">行号</th>
                    <th className="py-2 px-4 w-32">类型</th>
                    <th className="py-2 px-4">指令</th>
                  </tr>
                </thead>
                <tbody>
                  {report.irPreview.map((ir, idx) => (
                    <tr key={ir.id} className="hover:bg-slate-900/50 transition-colors border-b border-slate-900/50 last:border-0">
                      <td className="py-2 px-4 text-slate-600">{ir.line}</td>
                      <td className="py-2 px-4">
                        <span className="text-purple-400 px-2 py-0.5 bg-purple-900/20 rounded text-xs border border-purple-900/30">
                          {ir.type}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-green-300">{ir.content}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'graph' && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-slate-200">依赖关系与调用图</h3>
              <div className="flex gap-4 text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                  <span className="text-slate-400">合约 (Contract)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <span className="text-slate-400">库/接口 (Lib/Interface)</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700">
              <DependencyGraph data={report} />
            </div>
          </div>
        )}

        {activeTab === 'cicd' && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-2">CI/CD 集成</h3>
            <p className="text-slate-400 text-sm mb-6">使用此配置将 Sentinels 集成到您的 GitHub Actions 工作流中。</p>
            
            <div className="relative group">
              <pre className="bg-slate-950 text-blue-300 p-6 rounded-lg font-mono text-sm overflow-x-auto border border-slate-800">
                {CICD_YAML}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults;