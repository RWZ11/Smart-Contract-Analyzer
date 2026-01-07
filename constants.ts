export const DEFAULT_CONTRACT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // 漏洞: 重入攻击 (Reentrancy)
    function withdraw() public {
        uint bal = balances[msg.sender];
        require(bal > 0);

        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent, "Failed to send Ether");

        balances[msg.sender] = 0;
    }
    
    // 漏洞: 整数溢出 (如果版本 < 0.8.0, 虽然这里用于演示)
    function batchTransfer(address[] memory _receivers, uint256 _value) public {
        uint256 total = _receivers.length * _value;
        require(balances[msg.sender] >= total);
        
        balances[msg.sender] -= total;
        for (uint i = 0; i < _receivers.length; i++) {
            balances[_receivers[i]] += _value;
        }
    }
}`;

export const CICD_YAML = `# GitHub Action 配置
name: Sentinels Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 安装分析器
        run: pip install sentinels-analyzer
      - name: 运行分析
        run: sentinels . --output sarif --output-file results.sarif
      - name: 上传 SARIF 报告
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif`;