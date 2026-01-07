import React from 'react';

export enum Severity {
  HIGH = "High",
  MEDIUM = "Medium",
  LOW = "Low",
  INFO = "Info"
}

export interface IRInstruction {
  id: string;
  type: "Assignment" | "MemberAccess" | "BinaryOperation" | "CallOperation" | "LengthOperation" | "PhiOperation";
  content: string;
  line: number;
}

export interface Vulnerability {
  id: string;
  detectorName: string;
  severity: Severity;
  confidence: "High" | "Medium" | "Low";
  description: string;
  location: {
    startLine: number;
    endLine: number;
  };
  suggestion: string;
}

export interface ContractNode {
  id: string;
  name: string;
  type: "Contract" | "Library" | "Interface";
}

export interface DependencyLink {
  source: string;
  target: string;
}

export interface AnalysisReport {
  contracts: ContractNode[];
  dependencies: DependencyLink[];
  vulnerabilities: Vulnerability[];
  irPreview: IRInstruction[];
  stats: {
    high: number;
    medium: number;
    low: number;
    linesOfCode: number;
    functions: number;
  };
}

export interface TabOption {
  id: string;
  label: string;
  icon: React.ReactNode;
}