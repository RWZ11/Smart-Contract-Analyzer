import { ReportSummary as ReportSummaryType, AnalysisMetadata } from '@/types/report';
import { Clock, FileCode, Shield, AlertTriangle } from 'lucide-react';

interface ReportSummaryProps {
  summary: ReportSummaryType;
  metadata: AnalysisMetadata;
}

export default function ReportSummary({ summary, metadata }: ReportSummaryProps) {
  const formatDuration = (seconds: number) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="space-y-4">
      {/* 元数据卡片 */}
      <div className="bg-surface p-4 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <FileCode size={20} className="text-primary" />
          分析信息
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-400">目标文件</div>
            <div className="font-medium mt-1 truncate" title={metadata.target}>
              {metadata.target.split(/[/\\]/).pop()}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Solidity 版本</div>
            <div className="font-medium mt-1">{metadata.solidity_version || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-gray-400 flex items-center gap-1">
              <Clock size={14} />
              分析耗时
            </div>
            <div className="font-medium mt-1">{formatDuration(metadata.analysis_duration_seconds)}</div>
          </div>
          <div>
            <div className="text-gray-400">分析时间</div>
            <div className="font-medium mt-1 text-xs">{formatDate(metadata.timestamp)}</div>
          </div>
        </div>
      </div>

      {/* 漏洞汇总卡片 */}
      <div className="bg-surface p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield size={20} className="text-primary" />
          安全评分与漏洞统计
        </h3>
        
        {/* 总览数字 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="text-center p-4 bg-background/60 rounded-lg border border-gray-700">
            <div className="text-3xl font-bold text-white">{summary.total_vulnerabilities}</div>
            <div className="text-sm text-gray-400 mt-1">总漏洞数</div>
          </div>
          <div className="text-center p-4 bg-red-500/10 rounded-lg border border-red-500/30">
            <div className="text-3xl font-bold text-red-400">{summary.high_severity}</div>
            <div className="text-sm text-red-400 mt-1">高危</div>
          </div>
          <div className="text-center p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
            <div className="text-3xl font-bold text-yellow-400">{summary.medium_severity}</div>
            <div className="text-sm text-yellow-400 mt-1">中危</div>
          </div>
          <div className="text-center p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
            <div className="text-3xl font-bold text-blue-400">{summary.low_severity}</div>
            <div className="text-sm text-blue-400 mt-1">低危</div>
          </div>
          <div className="text-center p-4 bg-gray-500/10 rounded-lg border border-gray-500/30">
            <div className="text-3xl font-bold text-gray-400">{summary.informational}</div>
            <div className="text-sm text-gray-400 mt-1">信息性</div>
          </div>
        </div>

        {/* 风险等级提示 */}
        {summary.high_severity > 0 && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
            <AlertTriangle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-semibold text-red-400">发现高危漏洞</div>
              <div className="text-sm text-gray-300 mt-1">
                检测到 {summary.high_severity} 个高危安全问题，建议立即修复以避免潜在的资产损失或合约被攻击。
              </div>
            </div>
          </div>
        )}
        
        {summary.total_vulnerabilities === 0 && (
          <div className="text-center py-6 text-green-400">
            <Shield size={48} className="mx-auto mb-2 opacity-80" />
            <div className="font-semibold">未发现安全漏洞</div>
            <div className="text-sm text-gray-400 mt-1">合约通过了所有安全检测规则</div>
          </div>
        )}
      </div>
    </div>
  );
}
