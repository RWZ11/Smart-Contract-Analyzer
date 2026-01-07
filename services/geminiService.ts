import { GoogleGenAI, Type } from "@google/genai";
import { AnalysisReport, Severity } from "../types";

const SYSTEM_INSTRUCTION = `
你是一个名为 "Sentinels" 的高级智能合约静态分析引擎。
你的架构包括：
1. 编译/AST 解析 (Solidity 0.4.x - 0.8.x)。
2. IR 生成 (SlithIR 风格: Assignment, MemberAccess, CallOperation 等)。
3. 检测器分析 (重入攻击, 未经检查的低级调用, 访问控制等)。
4. 数据流分析 (污点追踪)。

你的任务：
分析提供的 Solidity 代码。
模拟内部流程并返回包含以下内容的 JSON 响应：
1. 识别出的漏洞 (High/Medium/Low)。**请注意：Description（描述）和 Suggestion（建议）字段必须使用中文。** 所有的 detectorName（检测器名称）也请尽量使用中文或行业通用的中文术语。
2. 针对最关键函数的生成 IR (中间表示) 预览。
3. 依赖图结构 (节点和链接)。
4. 统计数据。

请精确分析。如果代码存在重入漏洞，请明确指出。
注意：JSON 结构中的枚举值（如 Severity 的 "High", "Medium", "Low" 和 Type 的 "Contract", "Assignment" 等）请保持英文，以便前端程序正确处理。
`;

export const analyzeContractCode = async (code: string): Promise<AnalysisReport> => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    throw new Error("API Key 未配置。请检查环境变量。");
  }

  const ai = new GoogleGenAI({ apiKey });

  // Schema definition for strict JSON output
  const responseSchema = {
    type: Type.OBJECT,
    properties: {
      stats: {
        type: Type.OBJECT,
        properties: {
          high: { type: Type.NUMBER },
          medium: { type: Type.NUMBER },
          low: { type: Type.NUMBER },
          linesOfCode: { type: Type.NUMBER },
          functions: { type: Type.NUMBER },
        },
        required: ["high", "medium", "low", "linesOfCode", "functions"]
      },
      contracts: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            name: { type: Type.STRING },
            type: { type: Type.STRING, enum: ["Contract", "Library", "Interface"] }
          }
        }
      },
      dependencies: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            source: { type: Type.STRING },
            target: { type: Type.STRING }
          }
        }
      },
      vulnerabilities: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            detectorName: { type: Type.STRING },
            severity: { type: Type.STRING, enum: ["High", "Medium", "Low", "Info"] },
            confidence: { type: Type.STRING, enum: ["High", "Medium", "Low"] },
            description: { type: Type.STRING },
            location: {
              type: Type.OBJECT,
              properties: {
                startLine: { type: Type.NUMBER },
                endLine: { type: Type.NUMBER }
              }
            },
            suggestion: { type: Type.STRING }
          }
        }
      },
      irPreview: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            type: { type: Type.STRING, enum: ["Assignment", "MemberAccess", "BinaryOperation", "CallOperation", "LengthOperation", "PhiOperation"] },
            content: { type: Type.STRING },
            line: { type: Type.NUMBER }
          }
        }
      }
    },
    required: ["stats", "contracts", "vulnerabilities", "irPreview"]
  };

  try {
    // Timeout promise (30 seconds)
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error("分析请求超时 (30秒)。请重试或检查网络连接。")), 30000);
    });

    const apiPromise = ai.models.generateContent({
      model: "gemini-3-flash-preview", // Switched to Flash for faster response
      contents: `分析这段 Solidity 代码:\n\n${code}`,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json",
        responseSchema: responseSchema,
        temperature: 0.1 // Low temperature for deterministic analysis
      }
    });

    // Race between API call and timeout
    const response: any = await Promise.race([apiPromise, timeoutPromise]);

    const text = response.text;
    if (!text) throw new Error("AI 未返回有效响应");
    
    return JSON.parse(text) as AnalysisReport;

  } catch (error: any) {
    console.error("Analysis failed:", error);
    // Enhance error message for better user feedback
    let errorMessage = error.message;
    if (errorMessage.includes("400")) errorMessage = "请求无效 (400)。请检查代码格式。";
    if (errorMessage.includes("401") || errorMessage.includes("403")) errorMessage = "API Key 无效或无权限。";
    if (errorMessage.includes("503")) errorMessage = "服务暂时不可用，请稍后重试。";
    
    throw new Error(errorMessage);
  }
};