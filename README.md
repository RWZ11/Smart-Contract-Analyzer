# Smart Contract Analyzer — 智能合约安全审计平台

![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue)
![Node](https://img.shields.io/badge/Node.js-18.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Build-Passing-brightgreen)

---

## 1. 项目标题
- 项目名称：Smart Contract Analyzer（智能合约安全审计平台）
- 项目徽章：包含 Python/Node 版本、许可证与构建状态徽章，便于快速识别项目状态

## 2. 项目描述
- 目的与功能：
  - 本项目提供面向 Solidity 智能合约的静态安全审计能力，支持重入攻击、未授权访问、整数溢出、未检查转账、危险的 delegatecall、状态变量可见性等高危问题的检测。
  - 支持三种使用方式：命令行（CLI）、Web API（FastAPI）、现代化前端界面（React）。
- 适用群体与场景：
  - Web3 团队、安全审计工程师、区块链开发者、教学与研究人员。
  - 适用于代码评审、CI/CD 安全门禁、教学演示与快速审计。
- 技术栈与依赖：
  - 后端：Python、FastAPI、Uvicorn、py-solc-x（AST 解析）
  - 分析引擎：插件化架构，AST/文本双模检测
  - 前端：React + Vite + TypeScript、Tailwind CSS、React Router、i18n

## 3. 安装指南
- 系统要求：
  - 操作系统：Windows / macOS / Linux
  - Python：≥ 3.10（建议 3.11/3.13 均可）
  - Node.js：18.x LTS（与当前前端依赖兼容）
- 后端依赖安装：
  ```bash
  # 进入项目根目录
  pip install fastapi uvicorn python-multipart py-solc-x
  ```
- 前端安装：
  ```bash
  cd frontend
  npm install
  ```
- 环境配置：
  - 前端代理已配置为指向后端 `127.0.0.1:8000`
    - 配置文件：frontend/vite.config.ts 中的 server.proxy，如 [vite.config.ts](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/frontend/vite.config.ts)

## 4. 使用说明
- 命令行（CLI）使用：
  ```bash
  # 分析单个合约文件，输出为文本
  python cli.py test_contracts/vulnerable.sol --format text

  # 生成 JSON 报告
  python cli.py test_contracts/vulnerable.sol --format json

  # 生成 JUnit 报告（用于 Jenkins 等 CI）
  python cli.py test_contracts/vulnerable.sol --format junit

  # 生成 SARIF 报告（用于 GitHub Security）
  python cli.py test_contracts/vulnerable.sol --format sarif
  ```
  - 核心引擎：参见 [engine.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/core/engine.py)
  - 插件接口：参见 [interface.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/core/interface.py)
  - 报告生成：参见 [reporter.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/core/reporter.py)

- Web API 使用：
  1) 启动后端服务：
  ```bash
  python api.py
  # 或热重载方式：
  uvicorn api:app --host 0.0.0.0 --port 8000 --reload
  ```
  2) 调用接口：
  ```bash
  # 上传 .sol 文件并获取检测结果
  curl -X POST \
    -F "file=@test_contracts/vulnerable.sol" \
    http://127.0.0.1:8000/api/analyze
  ```
  - API 入口：参见 [api.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/api.py)

- 前端使用：
  ```bash
  cd frontend
  npm run dev
  # 打开浏览器访问 http://localhost:5173
  ```
  - 在“合约审计”页面上传 `.sol` 文件，将调用后端 API 返回审计结果
  - 主布局与导航：参见 [MainLayout.tsx](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/frontend/src/layouts/MainLayout.tsx)

- 配置选项说明：
  - CLI `--format` 支持：`text | json | junit | sarif`
  - 前端代理：`/api -> http://127.0.0.1:8000`，位于 [vite.config.ts](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/frontend/vite.config.ts)

- 示例代码片段（前端调用 API）：
  ```ts
  // axios 请求示例
  const formData = new FormData();
  formData.append('file', file);
  const resp = await axios.post('/api/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  console.log(resp.data.issues);
  ```

## 5. 开发指南
- 项目结构：
  ```text
  Smart-Contract-Analyzer/
  ├─ core/                  # 引擎与通用能力
  │  ├─ engine.py           # 分析引擎，加载并运行所有检测插件
  │  ├─ interface.py        # 插件抽象基类定义
  │  ├─ ast_parser.py       # AST 解析器（solc + py-solc-x）
  │  └─ reporter.py         # 报告生成（JSON/JUnit/SARIF）
  ├─ plugins/               # 检测插件（规则库）
  │  ├─ security_rules.py   # ReentrancyDetector 等核心安全规则
  │  ├─ taint_analysis.py   # 未授权访问/资金流向等数据流分析
  │  ├─ unchecked_return.py # 未检查转账返回值
  │  ├─ integer_overflow.py # 整数溢出/下溢
  │  ├─ delegate_call.py    # 危险的 delegatecall 使用
  │  └─ storage_visibility.py # 状态变量可见性
  ├─ test_contracts/        # 测试与示例合约
  │  └─ vulnerable.sol
  ├─ frontend/              # 前端单页应用（React + Vite）
  │  ├─ src/
  │  │  ├─ layouts/MainLayout.tsx
  │  │  ├─ pages/Home.tsx
  │  │  ├─ pages/Analyzer.tsx
  │  │  ├─ router.tsx
  │  │  └─ i18n.ts
  │  └─ vite.config.ts
  └─ api.py                 # FastAPI Web 接口入口
  ```
- 开发环境设置：
  - Python：建议使用 venv 隔离依赖
  - Node：使用 18.x（避免部分包对 20+ 的引擎要求）
  - 前端 UI：Tailwind CSS（暗色主题）、少量 Shadcn 风格组件
- 构建与测试：
  - 前端构建：`cd frontend && npm run build`
  - 代码风格：建议遵循 PEP8（Python）与 TypeScript 最佳实践；可选集成 ruff/black/eslint（尚未强制）

## 6. 贡献指南
- 问题与功能请求：请创建 Issue，描述复现步骤、预期结果与环境信息
- 代码贡献流程：
  1) Fork 仓库并创建特性分支（如 `feature/detector-overflow`）
  2) 完成实现并编写必要的示例合约与用法说明
  3) 提交 Pull Request，说明变更动机与影响范围
- 编码规范要求：
  - Python：类型注解、模块化、避免在日志中输出敏感信息
  - 前端：组件化、状态不可变、尽量无副作用；遵循可访问性（WCAG）

## 7. 许可证信息
- 开源许可证：MIT
- 版权声明：Copyright © 2026 Smart Contract Analyzer Contributors

## 8. 联系方式
- 维护者：项目团队（可在 Issue 中联系）
- 社区支持：GitHub Issues / Discussions（建议附带日志与最小复现示例）

---

### 快速开始（TL;DR）
```bash
# 1) 后端
python api.py  # http://127.0.0.1:8000

# 2) 前端
cd frontend
npm run dev    # http://localhost:5173

# 3) CLI 分析
python cli.py test_contracts/vulnerable.sol --format sarif
```

如需查看关键源码：
- 引擎：[engine.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/core/engine.py)
- 插件接口：[interface.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/core/interface.py)
- API：[api.py](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/api.py)
- 前端代理：[vite.config.ts](file:///d:/桌面/网络应用开发综合项目实践/Smart-Contract-Analyzer/frontend/vite.config.ts)
