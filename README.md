# On-Chain Fork & Contract Auditor

[![EVM Chains](https://img.shields.io/badge/Chains-ETH%20%7C%20BSC%20%7C%20Base%20%7C%20Arb-blue)](https://ethereum.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Web3.py](https://img.shields.io/badge/Web3.py-8.0-orange)](https://github.com/ethereum/web3.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An autonomous EVM smart contract security auditor and zero-cost swap simulation engine. Designed for security researchers, memecoin traders, and autonomous AI agents to audit token contracts, detect honeypot traps, identify hidden mints, and calculate real buy/sell taxes without paying a single wei of gas.

---

## Key Highlights

- **Bytecode & Selector Decompilation**: Scans raw runtime bytecode directly from RPC nodes. Extracts 4-byte function selectors and cross-references them against an offensive signatures database (blacklists, trading toggles, balance overrides, hidden mints, fee setters).
- **Dangerous Opcode Tracing**: Flags the presence of `DELEGATECALL` and `SELFDESTRUCT` opcodes that could allow logic hijacking or contract destruction.
- **Zero-Cost Swap Simulation (`eth_call`)**: Simulates roundtrip buy and sell swaps against Uniswap V2 and PancakeSwap V2 routers via state overrides. Computes exact buy tax and sell tax percentages, detecting non-sellable honeypots before any real transaction is broadcasted.
- **Liquidity Pool & AMM Inspection**: Queries factory contracts to locate liquidity pairs, calculates reserve ratios, and checks whether LP tokens are burned (`0x...dead`) or locked.
- **Multi-Chain Resilience**: Native support for Ethereum Mainnet, BNB Smart Chain, Base, and Arbitrum One with automatic multi-RPC failover.
- **AI Agent Native**: Built as a plug-and-play skill for Google Antigravity, Claude Code, and custom LLM agents with structured CLI flags and JSON output.

---

## Supported Blockchains & DEX Routers

| Chain | Default DEX | Native Currency | Fallback RPCs |
| :--- | :--- | :--- | :--- |
| **BNB Smart Chain (BSC)** | PancakeSwap V2 | `BNB` | `bsc-dataseed.binance.org` |
| **Base** | Uniswap V2 / Aerodrome | `ETH` | `mainnet.base.org` |
| **Ethereum Mainnet** | Uniswap V2 | `ETH` | `cloudflare-eth.com` |
| **Arbitrum One** | Uniswap V2 | `ETH` | `arb1.arbitrum.io/rpc` |

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

### 1. Basic Token Audit
Run a complete audit on any contract address across supported chains:

```bash
# Audit a BSC token
python auditor.py --token "0x55d398326f99059fF775485246999027B3197955" --chain bsc

# Audit a Base token
python auditor.py --token "0x532f27101965dd16442E59d40670FaF5eBB142E4" --chain base

# Audit an Ethereum token
python auditor.py --token "0x6B175474E89094C44Da98b954EedeAC495271d0F" --chain eth
```

### 2. Custom RPC & Slippage Simulation
Provide a private RPC endpoint (Alchemy, Infura, QuickNode) and adjust test swap amounts:

```bash
python auditor.py --token "0x..." --chain base --rpc "https://base-mainnet.g.alchemy.com/v2/YOUR_KEY" --amount 0.05
```

### 3. Machine-Readable JSON Output
Output raw structured JSON for pipelines, CI/CD, or feeding directly into an LLM context:

```bash
python auditor.py --token "0x55d398326f99059fF775485246999027B3197955" --chain bsc --json
```

Sample JSON Output:
```json
{
  "token": "0x55d398326f99059fF775485246999027B3197955",
  "chain": "bsc",
  "verdict": "SAFE",
  "flags": [
    "SELECTOR_MATCH: mint(address,uint256) [0x40c10f19]",
    "OPCODE: DELEGATECALL (proxy pattern)"
  ],
  "buy_tax_percent": 0.0,
  "sell_tax_percent": 0.0,
  "is_honeypot": false,
  "liquidity_status": {
    "pair_found": true,
    "pair_address": "0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE",
    "lp_burned": true
  }
}
```

---

## Risk Classifications & Verdicts

| Verdict | Risk Level | Description |
| :--- | :--- | :--- |
| `SAFE` | Low | Clean bytecode, verified sellability, normal taxes (< 10%), locked/burned LP. |
| `ELEVATED_TAX` | Medium | Buy or sell tax between 10% and 25%. High slippage impact. |
| `HIGH_RISK_TRAP` | High | Presence of bot traps, selective blacklists, or unverified minting authorities. |
| `HONEYPOT_CONFIRMED` | Critical | Sell transaction reverted during simulation. Token cannot be sold. |

---

## Antigravity Agent Skill Integration

To add this toolkit as a native skill to your Antigravity or AI agent environment:

1. Copy the folder to your skills directory:
   ```bash
   cp -r onchain-fork-auditor ~/.gemini/config/skills/
   ```
2. The agent will automatically detect `SKILL.md` and trigger on-chain audits whenever analyzing smart contracts, DeFi tokens, or suspicious transactions.

---

## Architecture

```
onchain-fork-auditor/
├── auditor.py                     # Unified multi-chain CLI entrypoint
├── requirements.txt               # Dependencies (web3, requests)
├── SKILL.md                       # Antigravity skill specification
├── scripts/
│   ├── bytecode_inspector.py      # EVM disassembler & selector signature scanner
│   ├── swap_simulator.py          # Zero-gas eth_call swap & tax simulation engine
│   └── lp_checker.py              # DEX factory pair & liquidity burn checker
└── README.md
```

---

## Author & Community

Crafted with care by [@0xHbeeb](https://github.com/0xHbeeb).  
If this tool helped protect your capital or enhanced your security workflow, don't forget to **Star** the repository!
