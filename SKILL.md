---
name: onchain-fork-auditor
description: Autonomous EVM smart contract bytecode security auditor and zero-cost swap simulation engine. Analyzes token bytecodes, detects honeypot traps, blacklists, hidden mints, and calculates real buy/sell taxes across Ethereum, BSC, Base, and Arbitrum.
---

# On-Chain Fork & Contract Auditor

**On-Chain Fork & Contract Auditor** is an autonomous smart contract security and honeypot detection engine. It performs real-time bytecode analysis and swap simulations to identify predatory taxes, hidden mints, proxy traps, and non-sellable honeypot tokens before executing on-chain swaps or investments.

---

## 🛠 Features

1. **Bytecode & Opcode Disassembly (`bytecode_inspector.py`)**:
   - Analyzes runtime bytecode and function dispatcher selectors.
   - Identifies malicious patterns: blacklist functions, hidden owner mints, trading pause switches, dynamic tax modification, and `DELEGATECALL`/`SELFDESTRUCT` opcodes.
   - Generates a **Bytecode Risk Score** (0 to 100).

2. **DEX Swap & Tax Simulation (`swap_simulator.py`)**:
   - Queries DEX router reserves (Uniswap V2 / PancakeSwap V2 / Aerodrome).
   - Simulates roundtrip Buy and Sell paths without spending gas.
   - Detects non-sellable honeypot tokens and calculates exact **Buy Tax %** and **Sell Tax %**.

3. **Liquidity Pool Integrity (`lp_checker.py`)**:
   - Identifies primary DEX pair contract.
   - Checks LP token burn status (Dead address `0x...dead`) and lock status.

---

## 🚀 Quick Usage

### 1. Audit Any Token on BSC, ETH, Base, or Arbitrum
```bash
# BSC Token Audit
python C:\Users\habib\.gemini\config\skills\onchain-fork-auditor\auditor.py --token "0x55d398326f99059fF775485246999027B3197955" --chain bsc

# Base Token Audit
python C:\Users\habib\.gemini\config\skills\onchain-fork-auditor\auditor.py --token "0x532f27101965dd16442E59d40670FaF5eBB142E4" --chain base

# Ethereum Token Audit
python C:\Users\habib\.gemini\config\skills\onchain-fork-auditor\auditor.py --token "0xdAC17F958D2ee523a2206206994597C13D831ec7" --chain eth
```

### 2. JSON Output Mode (for Agents & Pipelines)
```bash
python C:\Users\habib\.gemini\config\skills\onchain-fork-auditor\auditor.py --token "0x..." --chain bsc --json
```

---

## 📋 Security Verdicts

- `SAFE`: Clean bytecode, normal taxes (< 10%), verified sellability.
- `ELEVATED_TAX`: Taxes exceed 15%.
- `HIGH_RISK_TRAP`: Contract contains blacklist or freeze functions that owner can trigger.
- `HONEYPOT_DETECTED`: Token cannot be sold or incurs 50%+ predatory sell taxes.
