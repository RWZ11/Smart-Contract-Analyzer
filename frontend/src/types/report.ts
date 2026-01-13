// Slither 风格报告的类型定义

export interface AnalysisMetadata {
  timestamp: string;
  target: string;
  solidity_version?: string;
  analysis_duration_seconds: number;
  framework?: string;
}

export interface ContractInfo {
  name: string;
  source_file: string;
  source_lines: {
    start: number;
    end: number;
  };
  is_upgradeable: boolean;
}

export interface Location {
  file: string;
  start_line: number;
  end_line: number;
  source_mapping?: string;
}

export interface Vulnerability {
  id: string;
  detector: string;
  severity: 'High' | 'Medium' | 'Low';
  swc_id: string;
  title: string;
  description: string;
  contract: string;
  function: string | null;
  location: Location;
  code_snippet: string;
  fix_suggestion: string;
  confidence: 'High' | 'Medium' | 'Low';
}

export interface InformationalFinding {
  id: string;
  detector: string;
  severity: 'Informational';
  swc_id: string;
  title: string;
  description: string;
  contract: string;
  function: string | null;
  location: Location;
  code_snippet: string;
  fix_suggestion: string;
  confidence: 'High' | 'Medium' | 'Low';
}

export interface ReportSummary {
  total_vulnerabilities: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  informational: number;
  total_contracts_analyzed: number;
}

export interface AnalysisReport {
  sca_version: string;
  analysis_metadata: AnalysisMetadata;
  contracts_analyzed: ContractInfo[];
  vulnerabilities: Vulnerability[];
  informational_findings: InformationalFinding[];
  summary: ReportSummary;
}

export interface ApiResponse {
  status: string;
  report: AnalysisReport;
}

// 严重级别颜色映射
export const severityColors = {
  High: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/50',
    text: 'text-red-400',
    dot: 'bg-red-500',
  },
  Medium: {
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/50',
    text: 'text-yellow-400',
    dot: 'bg-yellow-500',
  },
  Low: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/50',
    text: 'text-blue-400',
    dot: 'bg-blue-500',
  },
  Informational: {
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/50',
    text: 'text-gray-400',
    dot: 'bg-gray-500',
  },
};
