// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract UncheckedTransfer {
    // 转账后未校验返回值，转账失败时合约逻辑仍继续执行
    function sendEther(address _to) external payable {
        // 错误：call 转账未检查 success 返回值
        _to.call{value: msg.value}(""); 
        // 错误：transfer 虽有内置校验，但 Solidity 0.8+ 仍建议显式处理
        payable(_to).transfer(1 ether);
    }
}