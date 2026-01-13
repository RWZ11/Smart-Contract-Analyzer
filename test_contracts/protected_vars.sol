// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract Config {
    address public owner;
    uint256 public rate;

    constructor() {
        owner = msg.sender;
    }

    function setRate(uint256 r) external {
        rate = r;
    }
}

