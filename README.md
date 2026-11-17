# On-Chain Fork & Contract Auditor

[![EVM & Solana](https://img.shields.io/badge/Chains-EVM%20%26%20Solana-blue)](https://ethereum.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Web3.py](https://img.shields.io/badge/Web3.py-8.0-orange)](https://github.com/ethereum/web3.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An autonomous smart contract security auditor and zero-cost swap simulation engine supporting both **EVM blockchains** (Ethereum, BSC, Base, Arbitrum, Robinhood Chain, Elysium) and **Solana** (SPL & Token-2022). 

Engineered for security researchers, memecoin traders, and autonomous AI agents to audit token contracts, detect honeypot traps, identify hidden mints, inspect retained authorities, and calculate real buy/sell taxes without spending gas.

---

## Key Highlights

- **Multi-Ecosystem Coverage**:
  - **EVM Networks**: Ethereum, BNB Smart Chain, Base, Arbitrum One, **Robinhood Chain (Arbitrum Orbit L2)**, and **Elysium Chain (Vulcan Forged)**.
  - **Solana Ecosystem**: Native inspection for Standard SPL and **Token-2022** tokens.
- **Solana SPL & Token-2022 Deep Audit**:
  - **Mint Authority**: Confirms whether mint authority is revoked or retained (preventing infinite mint/supply dilution).
  - **Freeze Authority (Honeypot)**: Flags retained freeze authority capable of freezing holder token accounts.
  - **Token-2022 Extensions**: Detects `transferHook` (malicious transfer vetoes/tax traps), `permanentDelegate` (token confiscation), and default account state anomalies.
  - **Meteora DLMM & Dynamic AMM Tracking**: Dedicated detection for Meteora liquidity pools, distinguishing between DLMM bins and Dynamic Pools, tracking TVL, pool count, 24h volume, and top pool addresses.
  - **Multi-DEX Aggregation**: Real-time cross-venue TVL aggregation across **Meteora**, **Raydium**, **Orca**, and **Pump.fun**.
- **EVM Bytecode & Selector Decompilation**: 
  - Scans raw runtime bytecode directly from RPC nodes. Extracts 4-byte function selectors and cross-references them against an offensive signatures database (blacklists, trading toggles, balance overrides, hidden mints, fee setters).
  - Traces dangerous opcodes: `DELEGATECALL` (proxy logic hijacking) and `SELFDESTRUCT` (contract annihilation).
- **Zero-Cost Swap Simulation (`eth_call`)**: 
  - Simulates roundtrip buy and sell swaps against Uniswap V2 and PancakeSwap V2 routers via state overrides. Computes exact buy tax and sell tax percentages, detecting non-sellable honeypots before any real transaction is broadcasted.
- **Liquidity Pool & AMM Inspection**: 
  - Queries factory contracts to locate liquidity pairs, calculates reserve ratios, and checks whether LP tokens are burned (`0x...dead`) or locked.
- **Multi-Chain Resilience**: 
  - Automatic multi-RPC failover with low latency timeout management across all supported networks.
- **AI Agent Native**: 
  - Built as a plug-and-play skill for Google Antigravity, Claude Code, and autonomous hunting pipelines with clean CLI flags and JSON output.

---

## Supported Blockchains & Ecosystems

| Network / Chain | Architecture | Default DEX / Liquidity | Native Currency | Default Public RPC |
| :--- | :--- | :--- | :--- | :--- |
| **Solana (`sol`)** | SVM / SPL & Token-2022 | Meteora (DLMM & AMM) / Raydium / Orca / Pump.fun | `SOL` | `api.mainnet-beta.solana.com` |
| **Robinhood Chain (`robinhood`)** | EVM (Arbitrum Orbit L2) | DEX / Bridge | `ETH` | `rpc.mainnet.chain.robinhood.com` |
| **Elysium Chain (`elysium`)** | EVM (Vulcan Forged L1) | Elysium DEX | `LAVA` / `PYR` | `rpc.elysiumchain.tech` |
| **BNB Smart Chain (`bsc`)** | EVM | PancakeSwap V2 | `BNB` | `bsc-dataseed.binance.org` |
| **Base (`base`)** | EVM | Uniswap V2 / Aerodrome | `ETH` | `mainnet.base.org` |
| **Ethereum Mainnet (`eth`)** | EVM | Uniswap V2 | `ETH` | `cloudflare-eth.com` |
| **Arbitrum One (`arbitrum`)** | EVM | Uniswap V2 / SushiSwap | `ETH` | `arb1.arbitrum.io/rpc` |

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Setup
```bash
git clone https://github.com/0xHbeeb/onchain-fork-auditor.git
cd onchain-fork-auditor
pip install -r requirements.txt
```

---

## Usage Guide

### 1. Solana Token Audit (SPL & Token-2022)
Audit any Solana token mint address:

```bash
# Audit Bonk
python auditor.py --token "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" --chain sol

# Audit dogwifhat ($WIF)
python auditor.py --token "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm" --chain sol
```

### 2. Robinhood Chain & Elysium Audits
```bash
# Audit a token or contract on Robinhood Chain
python auditor.py --token "0x..." --chain robinhood

# Audit PYR or gaming token on Elysium Chain
python auditor.py --token "0xa801b1A7846156d4C81bD188F96bfcb621517611" --chain elysium
```

### 3. EVM Memecoin & DeFi Audits (BSC, Base, Ethereum)
```bash
# Audit a BSC token
python auditor.py --token "0x55d398326f99059fF775485246999027B3197955" --chain bsc

# Audit a Base token
python auditor.py --token "0x532f27101965dd16442E59d40670FaF5eBB142E4" --chain base
```

### 4. Machine-Readable JSON Output
Output structured JSON for bots, trading algorithms, or AI agents:

```bash
python auditor.py --token "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" --chain sol --json
```

Sample Solana JSON Output:
```json
{
  "token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
  "chain": "solana",
  "symbol": "Bonk",
  "name": "Bonk",
  "program": "Standard SPL",
  "decimals": 5,
  "total_supply": 87994293321576.95,
  "mint_authority": null,
  "freeze_authority": null,
  "is_mint_revoked": true,
  "is_freeze_revoked": true,
  "score": 100,
  "verdict": "SAFE",
  "severity": "LOW",
  "liquidity": {
    "has_dex": true,
    "total_liquidity_usd": 4350511.05,
    "primary_dex": "METEORA",
    "token_name": "Jupiter",
    "token_symbol": "JUP",
    "price_usd": 0.2519,
    "meteora": {
      "has_pool": true,
      "pool_count": 18,
      "total_liquidity_usd": 3716975.41,
      "top_pair_address": "C8Gr6AUuq9hEdSYJzoEpNcdjpojPZwqG5MtQbeouNNwg",
      "pool_type": "DLMM",
      "quote_symbol": "SOL",
      "volume_24h": 1458397.38
    },
    "raydium": {
      "has_pool": true,
      "pool_count": 5,
      "total_liquidity_usd": 77889.76
    },
    "orca": {
      "has_pool": true,
      "pool_count": 6,
      "total_liquidity_usd": 555645.88
    },
    "pumpfun": {
      "has_pool": false,
      "total_liquidity_usd": 0.0
    }
  },
  "flags": [
    "MINT_AUTHORITY_REVOKED: Immutable supply confirmed",
    "FREEZE_AUTHORITY_REVOKED: Accounts cannot be frozen",
    "METEORA_LP_VERIFIED: 18 active Meteora DLMM pool(s) found ($3,716,975.41 TVL)"
  ]
}
```

---

## Risk Classifications & Verdicts

| Verdict | Risk Level | Description |
| :--- | :--- | :--- |
| `SAFE` | Low | Clean bytecode, revoked authorities, verified sellability, normal taxes (< 10%), locked LP. |
| `ELEVATED_TAX` / `ELEVATED_RISK` | Medium | Buy/sell tax between 10%–25%, Token-2022 custom extensions, or low liquidity pool. |
| `HIGH_RISK_TRAP` | High | Retained mint authority (unlimited supply), selective blacklists, or bot trap functions. |
| `HONEYPOT_CONFIRMED` | Critical | Retained freeze authority (Solana), malicious transfer hook, or reverted sell swap simulation. |

---

## Antigravity Agent Skill Integration

To use this toolkit as an agent skill inside Google Antigravity or custom LLM frameworks:

1. Copy the skill directory:
   ```bash
   cp -r onchain-fork-auditor ~/.gemini/config/skills/
   ```
2. The agent automatically activates `SKILL.md` whenever reviewing DeFi smart contracts, evaluating new token launches, or auditing blockchain transactions.

---

## Architecture

```
onchain-fork-auditor/
├── auditor.py                     # Unified multi-chain CLI entrypoint (EVM + Solana)
├── requirements.txt               # Dependencies (web3, requests)
├── SKILL.md                       # Antigravity skill specification
├── scripts/
│   ├── solana_auditor.py          # Solana SPL & Token-2022 authority & market inspector
│   ├── bytecode_inspector.py      # EVM disassembler & selector signature scanner
│   ├── swap_simulator.py          # Zero-gas eth_call swap & tax simulation engine
│   └── lp_checker.py              # DEX factory pair & liquidity burn checker
└── README.md
```

---

## Author & Community

Crafted with care by [@0xHbeeb](https://github.com/0xHbeeb).  
If this tool helped protect your capital or enhanced your security workflow, don't forget to **Star** the repository! ⭐
