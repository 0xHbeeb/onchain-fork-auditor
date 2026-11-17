---
name: onchain-fork-auditor
description: Autonomous multi-chain smart contract security auditor and zero-cost swap simulation engine for EVM (Ethereum, BSC, Base, Arbitrum, Robinhood, Elysium) and Solana (SPL & Token-2022). Analyzes bytecode, detects honeypot traps, blacklists, hidden mints, freeze authorities, and calculates real taxes.
---

# On-Chain Fork & Contract Auditor

**On-Chain Fork & Contract Auditor** is an autonomous security inspection engine for smart contracts and tokens across **EVM blockchains** (Ethereum, BSC, Base, Arbitrum, Robinhood Chain, Elysium) and **Solana** (SPL & Token-2022). It performs real-time bytecode analysis, authority inspection, and swap simulations to identify predatory taxes, hidden mints, proxy traps, freeze authorities, and non-sellable honeypot tokens before executing on-chain swaps.

---

## 🛠 Features

1. **Solana SPL & Token-2022 Deep Audit (`solana_auditor.py`)**:
   - Inspects `mintAuthority` (detects infinite mint/supply dilution risks).
   - Inspects `freezeAuthority` (detects honeypot vectors that can freeze user token accounts).
   - Scans Token-2022 extensions (`transferHook`, `permanentDelegate`, `defaultAccountState`).
   - Integrates Raydium, Orca, and Pump.fun liquidity metrics via DexScreener.

2. **Bytecode & Opcode Disassembly (`bytecode_inspector.py`)**:
   - Analyzes runtime bytecode and function dispatcher selectors.
   - Identifies malicious patterns: blacklist functions, hidden owner mints, trading pause switches, dynamic tax modification, and `DELEGATECALL`/`SELFDESTRUCT` opcodes.
   - Generates a **Bytecode Risk Score** (0 to 100).

3. **DEX Swap & Tax Simulation (`swap_simulator.py`)**:
   - Queries DEX router reserves (Uniswap V2 / PancakeSwap V2 / Aerodrome).
   - Simulates roundtrip Buy and Sell paths without spending gas.
   - Detects non-sellable honeypot tokens and calculates exact **Buy Tax %** and **Sell Tax %**.

4. **Liquidity Pool Integrity (`lp_checker.py`)**:
   - Identifies primary DEX pair contract.
   - Checks LP token burn status (Dead address `0x...dead`) and lock status.

---

## 🚀 Quick Usage

### 1. Audit Solana Tokens (SPL & Token-2022)
```bash
python auditor.py --token "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" --chain sol
```

### 2. Audit EVM Chains (Robinhood, Elysium, BSC, Base, ETH, Arbitrum)
```bash
# Robinhood Chain
python auditor.py --token "0x..." --chain robinhood

# Elysium Chain (Vulcan Forged)
python auditor.py --token "0xa801b1A7846156d4C81bD188F96bfcb621517611" --chain elysium

# BSC Token
python auditor.py --token "0x55d398326f99059fF775485246999027B3197955" --chain bsc

# Base Token
python auditor.py --token "0x532f27101965dd16442E59d40670FaF5eBB142E4" --chain base
```

### 3. JSON Output Mode (for Agents & Bots)
```bash
python auditor.py --token "<TOKEN_ADDRESS>" --chain sol --json
```

---

## 📋 Security Verdicts

- `SAFE`: Clean bytecode / revoked authorities, verified sellability, normal taxes (< 10%).
- `ELEVATED_TAX` / `ELEVATED_RISK`: Taxes exceed 15%, Token-2022 extensions present, or low liquidity pool.
- `HIGH_RISK_TRAP`: Contract contains blacklist, retained mint authority, or pause functions.
- `HONEYPOT_CONFIRMED`: Token cannot be sold, retained freeze authority on Solana, or predatory sell taxes.
