import sys
import argparse
import json
from web3 import Web3

from scripts.bytecode_inspector import analyze_bytecode
from scripts.swap_simulator import simulate_token_swap
from scripts.lp_checker import check_liquidity_pool
from scripts.solana_auditor import audit_solana_token

DEFAULT_RPCS = {
    "bsc": [
        "https://bsc-dataseed.binance.org",
        "https://bsc-dataseed1.binance.org",
        "https://1rpc.io/bnb",
        "https://binance.llamarpc.com"
    ],
    "eth": [
        "https://cloudflare-eth.com",
        "https://eth.llamarpc.com",
        "https://1rpc.io/eth",
        "https://rpc.ankr.com/eth"
    ],
    "base": [
        "https://mainnet.base.org",
        "https://base.llamarpc.com",
        "https://1rpc.io/base"
    ],
    "arbitrum": [
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.llamarpc.com",
        "https://1rpc.io/arb"
    ],
    "robinhood": [
        "https://rpc.mainnet.chain.robinhood.com/"
    ],
    "elysium": [
        "https://rpc.elysiumchain.tech"
    ],
    "solana": [
        "https://api.mainnet-beta.solana.com",
        "https://solana-rpc.publicnode.com",
        "https://rpc.ankr.com/solana"
    ]
}

def get_web3_instance(chain: str, custom_rpc: str = None) -> Web3:
    rpc_urls = [custom_rpc] if custom_rpc else DEFAULT_RPCS.get(chain.lower(), DEFAULT_RPCS["bsc"])
    for rpc in rpc_urls:
        if not rpc:
            continue
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                return w3
        except Exception:
            continue
    raise ConnectionError(f"Failed to connect to any RPC for chain: {chain}")

def audit_token(token_address: str, chain: str = "bsc", custom_rpc: str = None, json_output: bool = False):
    norm_chain = chain.lower().strip()

    # Route Solana SPL tokens to dedicated Solana auditor
    if norm_chain in ["sol", "solana"]:
        return audit_solana_token(token_address, custom_rpc=custom_rpc, json_output=json_output)

    w3 = get_web3_instance(norm_chain, custom_rpc)
    clean_address = Web3.to_checksum_address(token_address)

    # 1. Bytecode & Opcode Analysis
    bytecode_res = analyze_bytecode(w3, clean_address)
    if not bytecode_res.get("is_contract"):
        print(f"[-] Error: {clean_address} is not a valid smart contract or has no on-chain runtime code.")
        return

    # 2. Swap Simulation (Taxes, Honeypot detection)
    swap_res = simulate_token_swap(w3, norm_chain, clean_address)

    # 3. Liquidity & Pair Status
    lp_res = check_liquidity_pool(w3, norm_chain, clean_address)

    # 4. Final Verdict Calculation
    verdict = "SAFE"
    severity = "LOW"
    critical_issues = []

    if swap_res.get("is_honeypot"):
        verdict = "HONEYPOT_DETECTED"
        severity = "CRITICAL"
        critical_issues.append(swap_res.get("honeypot_reason", "Token cannot be sold."))
    elif bytecode_res.get("risk_score", 0) >= 60:
        verdict = "HIGH_RISK_TRAP"
        severity = "HIGH"
    elif swap_res.get("sell_tax_percent", 0) > 15.0 or swap_res.get("buy_tax_percent", 0) > 15.0:
        verdict = "ELEVATED_TAX"
        severity = "MEDIUM"

    full_report = {
        "token_address": clean_address,
        "chain": norm_chain.upper(),
        "symbol": swap_res.get("symbol", "UNKNOWN"),
        "verdict": verdict,
        "severity": severity,
        "critical_issues": critical_issues,
        "taxes": {
            "buy_tax_pct": swap_res.get("buy_tax_percent", 0.0),
            "sell_tax_pct": swap_res.get("sell_tax_percent", 0.0),
            "can_buy": swap_res.get("can_buy", False),
            "can_sell": swap_res.get("can_sell", False),
        },
        "bytecode_audit": bytecode_res,
        "liquidity": lp_res
    }

    if json_output:
        print(json.dumps(full_report, indent=2))
        return full_report

    # Formatted Terminal Output
    print("\n" + "=" * 70)
    print(f" 🛡️  ON-CHAIN FORK & CONTRACT AUDITOR — {full_report['symbol']} ({norm_chain.upper()})")
    print("=" * 70)
    print(f"  Token Address    : {clean_address}")
    print(f"  Security Verdict : {verdict} ({severity})")
    print(f"  Bytecode Score   : {bytecode_res['risk_score']}/100")
    print("-" * 70)
    print("  📊 SWAP & TAX SIMULATION:")
    print(f"     • Can Buy     : {'✅ Yes' if swap_res['can_buy'] else '❌ No'}")
    print(f"     • Can Sell    : {'✅ Yes' if swap_res['can_sell'] else '❌ No (HONEYPOT)'}")
    print(f"     • Buy Tax     : ~{swap_res['buy_tax_percent']}%")
    print(f"     • Sell Tax    : ~{swap_res['sell_tax_percent']}%")

    print("-" * 70)
    print("  💧 LIQUIDITY STATUS:")
    if lp_res.get("has_pair"):
        print(f"     • Pair Address: {lp_res['pair_address']}")
        print(f"     • LP Burned   : {lp_res['lp_burned_percent']}% {'(🔥 Burned/Safe)' if lp_res['is_lp_burned'] else '(⚠️ Not Burned)'}")
    else:
        note = lp_res.get("note") or "No primary DEX pair detected."
        print(f"     • Pair Status : {note}")

    print("-" * 70)
    print("  🚨 DETECTED BYTECODE RISKS & CAPABILITIES:")
    if bytecode_res["flagged_features"]:
        for feat in bytecode_res["flagged_features"]:
            print(f"     • {feat}")
    else:
        print("     • Clean bytecode: No blacklist, hidden mint, or pause traps detected.")

    if critical_issues:
        print("\n  ❌ CRITICAL FAILURE REASONS:")
        for iss in critical_issues:
            print(f"     • {iss}")

    print("=" * 70 + "\n")
    return full_report

def main():
    parser = argparse.ArgumentParser(description="On-Chain Fork & Smart Contract Auditor (EVM + Solana)")
    parser.add_argument("--token", required=True, help="Target Token Contract Address (0x... or Solana Mint Base58)")
    parser.add_argument("--chain", default="bsc", choices=["bsc", "eth", "base", "arbitrum", "robinhood", "elysium", "sol", "solana"], help="Target Blockchain network")
    parser.add_argument("--rpc", default=None, help="Custom RPC endpoint URL")
    parser.add_argument("--amount", type=float, default=0.1, help="Simulation swap test amount in native currency")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")

    args = parser.parse_args()

    try:
        audit_token(args.token, chain=args.chain, custom_rpc=args.rpc, json_output=args.json)
    except Exception as e:
        print(f"[-] Execution Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
