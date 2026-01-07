import { AnalysisReport, Severity, Vulnerability, ContractNode, IRInstruction } from "../types";

/**
 * 本地静态分析引擎 (Sentinels Local Engine)
 * 不依赖外部 API，使用正则匹配和启发式规则进行离线分析。
 */
export const analyzeContractCode = async (code: string): Promise<AnalysisReport> => {
  // 模拟分析引擎启动和处理时间 (提升用户体验真实感)
  await new Promise(resolve => setTimeout(resolve, 1000));

  const lines = code.split('\n');
  const vulnerabilities: Vulnerability[] = [];
  const contracts: ContractNode[] = [];
  const dependencies: any[] = [];
  const irPreview: IRInstruction[] = [];

  let functionCount = 0;
  let currentFunction: string | null = null;
  let irCounter = 0;
  let solidityVersion = "0.8.0"; // 默认假设

  // 1. 预处理与版本检测
  const pragmaLine = lines.find(l => l.trim().startsWith('pragma solidity'));
  if (pragmaLine) {
      const vMatch = pragmaLine.match(/(\d+\.\d+\.\d+)/);
      if (vMatch) solidityVersion = vMatch[1];
  }
  const isOldVersion = parseInt(solidityVersion.split('.')[1]) < 8;

  // 2. 逐行扫描分析
  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    const lineNum = idx + 1;
    
    // 忽略注释
    if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) return;

    // --- 结构解析 ---

    // 识别合约/接口/库
    const contractMatch = trimmed.match(/^(contract|interface|library)\s+(\w+)/);
    if (contractMatch) {
      contracts.push({
        id: contractMatch[2],
        name: contractMatch[2],
        type: contractMatch[1] === 'library' ? 'Library' : contractMatch[1] === 'interface' ? 'Interface' : 'Contract'
      });
      // 识别继承关系
      if (trimmed.includes(' is ')) {
         const parts = trimmed.split(' is ');
         if (parts[1]) {
             const parents = parts[1].split('{')[0].split(',').map(p => p.trim());
             parents.forEach(p => dependencies.push({ source: contractMatch[2], target: p.split(' ')[0] }));
         }
      }
    }

    // 识别函数
    if (trimmed.startsWith('function ')) {
        functionCount++;
        const funcMatch = trimmed.match(/function\s+(\w+)/);
        currentFunction = funcMatch ? funcMatch[1] : 'fallback/receive';
    } else if (trimmed === '}') {
        currentFunction = null;
    }

    // --- IR 生成 (模拟 SlithIR) ---
    // 为非空行且在函数内的代码生成 IR 指令
    if (currentFunction && trimmed.length > 2 && !trimmed.startsWith('function')) {
        let irType: IRInstruction['type'] | null = null;
        let content = "";

        if (trimmed.includes(' = ')) {
            irType = 'Assignment';
            const parts = trimmed.split(' = ');
            content = `${parts[0].trim()} := ${parts[1].replace(';', '').trim()}`;
        } else if (trimmed.includes('require(')) {
            irType = 'CallOperation';
            content = `INTERNAL_CALL require(...)`;
        } else if (trimmed.includes('.call') || trimmed.includes('.delegatecall')) {
            irType = 'CallOperation';
            content = `LOW_LEVEL_CALL ${trimmed.replace(';', '')}`;
        } else if (trimmed.includes('length')) {
            irType = 'LengthOperation';
            content = `SLOAD length_of_array`;
        } else if (trimmed.includes('if (')) {
            irType = 'PhiOperation';
            content = `CONDITION ${trimmed.replace('{', '')}`;
        }

        if (irType && irCounter < 15) { // 限制预览数量
            irPreview.push({
                id: `ir-${irCounter++}`,
                type: irType,
                content: content,
                line: lineNum
            });
        }
    }

    // --- 漏洞检测规则 (Heuristics) ---

    // 规则 1: 重入攻击 (Reentrancy)
    // 检测带有 value 的低级调用
    if (trimmed.match(/\.call\s*\{.*value:/)) {
        vulnerabilities.push({
            id: `vuln-reentrancy-${lineNum}`,
            detectorName: "重入攻击风险 (Reentrancy)",
            severity: Severity.HIGH,
            confidence: "High",
            description: "检测到发送 ETH 的低级 `call`。如果在此调用之后修改了状态变量，可能会导致重入攻击。",
            location: { startLine: lineNum, endLine: lineNum },
            suggestion: "遵循 Checks-Effects-Interactions 模式，或使用 OpenZeppelin 的 ReentrancyGuard。"
        });
    }

    // 规则 2: 整数溢出 (Integer Overflow) - 仅在旧版本 Solidity 中检测
    if (isOldVersion && trimmed.match(/[\+\-\*]=?/) && !trimmed.includes('unchecked')) {
        // 避免重复报告，简单去重
        const hasOverflow = vulnerabilities.some(v => v.detectorName === "整数溢出风险");
        if (!hasOverflow) {
            vulnerabilities.push({
                id: `vuln-overflow-${lineNum}`,
                detectorName: "整数溢出风险",
                severity: Severity.HIGH,
                confidence: "Medium",
                description: `当前 Solidity 版本 (${solidityVersion}) < 0.8.0，算术运算不会自动检查溢出。`,
                location: { startLine: lineNum, endLine: lineNum },
                suggestion: "请使用 SafeMath 库进行算术运算，或升级到 Solidity 0.8.0+。"
            });
        }
    }

    // 规则 3: 使用 tx.origin
    if (trimmed.includes('tx.origin')) {
        vulnerabilities.push({
            id: `vuln-txorigin-${lineNum}`,
            detectorName: "使用 tx.origin 鉴权",
            severity: Severity.MEDIUM,
            confidence: "High",
            description: "使用 `tx.origin` 进行身份验证容易受到网络钓鱼攻击。",
            location: { startLine: lineNum, endLine: lineNum },
            suggestion: "建议使用 `msg.sender` 替代 `tx.origin`。"
        });
    }

    // 规则 4: 未检查的低级调用返回值
    // 简单检测：只有 .call 但没有在同一行赋值给 bool 或在 require 中使用
    if ((trimmed.includes('.call') || trimmed.includes('.delegatecall')) && 
        !trimmed.includes('require') && 
        !trimmed.includes('bool ') && 
        !trimmed.includes('success')) {
         vulnerabilities.push({
            id: `vuln-unchecked-${lineNum}`,
            detectorName: "未检查的返回值",
            severity: Severity.LOW,
            confidence: "Medium",
            description: "低级调用的返回值未被检查。如果调用失败，交易将继续执行。",
            location: { startLine: lineNum, endLine: lineNum },
            suggestion: "始终检查低级调用的返回值：`(bool success, ) = ...; require(success);`"
        });
    }
  });

  // 3. 构建报告
  return {
    contracts,
    dependencies,
    vulnerabilities,
    irPreview,
    stats: {
      high: vulnerabilities.filter(v => v.severity === Severity.HIGH).length,
      medium: vulnerabilities.filter(v => v.severity === Severity.MEDIUM).length,
      low: vulnerabilities.filter(v => v.severity === Severity.LOW || v.severity === Severity.INFO).length,
      linesOfCode: lines.length,
      functions: functionCount
    }
  };
};