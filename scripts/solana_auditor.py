import requests
import json
from typing import Dict, Any, List, Optional

SOLANA_DEFAULT_RPCS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana"
]

TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

def query_solana_rpc(method: str, params: list, custom_rpc: Optional[str] = None) -> Dict[str, Any]:
    rpcs = [custom_rpc] if custom_rpc else SOLANA_DEFAULT_RPCS
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    for rpc in rpcs:
        if not rpc:
            continue
        try:
            resp = requests.post(rpc, json=payload, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if "error" not in data:
                    return data
        except Exception:
            continue
    raise ConnectionError(f"Failed to query Solana RPC across endpoints: {rpcs}")

def fetch_dexscreener_info(mint_address: str) -> Dict[str, Any]:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            pairs = data.get("pairs", [])
            if pairs:
                # Prioritize pair with highest liquidity
                pairs_sorted = sorted(pairs, key=lambda x: (x.get("liquidity", {}) or {}).get("usd", 0), reverse=True)
                top = pairs_sorted[0]
                return {
                    "has_dex": True,
                    "dex": top.get("dexId", "unknown"),
                    "pair_address": top.get("pairAddress"),
                    "liquidity_usd": float((top.get("liquidity", {}) or {}).get("usd", 0.0)),
                    "price_usd": float(top.get("priceUsd", 0.0) or 0.0),
                    "volume_24h": float((top.get("volume", {}) or {}).get("h24", 0.0)),
                    "base_token": top.get("baseToken", {}).get("name", "Unknown"),
                    "symbol": top.get("baseToken", {}).get("symbol", "UNKNOWN")
                }
    except Exception:
        pass
    return {
        "has_dex": False,
        "dex": None,
        "pair_address": None,
        "liquidity_usd": 0.0,
        "price_usd": 0.0,
        "volume_24h": 0.0,
        "base_token": "Unknown",
        "symbol": "UNKNOWN"
    }

def audit_solana_token(mint_address: str, custom_rpc: Optional[str] = None, json_output: bool = False) -> Dict[str, Any]:
    # 1. Fetch Mint Account Info
    rpc_res = query_solana_rpc("getAccountInfo", [mint_address, {"encoding": "jsonParsed"}], custom_rpc)
    val = (rpc_res.get("result") or {}).get("value")

    if not val:
        raise ValueError(f"Solana token mint account '{mint_address}' not found or has no on-chain state.")

    owner_program = val.get("owner", "")
    is_token_2022 = (owner_program == TOKEN_2022_PROGRAM_ID)

    data_field = val.get("data", {})
    if isinstance(data_field, dict) and "parsed" in data_field:
        parsed_info = data_field["parsed"].get("info", {})
    else:
        parsed_info = {}

    decimals = parsed_info.get("decimals", 0)
    supply_raw = int(parsed_info.get("supply", 0) or 0)
    supply = supply_raw / (10 ** decimals) if decimals else supply_raw

    mint_authority = parsed_info.get("mintAuthority")
    freeze_authority = parsed_info.get("freezeAuthority")
    extensions = parsed_info.get("extensions", []) or []

    # 2. DexScreener Liquidity & Market Data
    market_info = fetch_dexscreener_info(mint_address)

    # 3. Analyze Vulnerability Flags & Score
    flags = []
    score = 100

    # Mint Authority check
    if mint_authority is not None:
        flags.append(f"MINT_AUTHORITY_RETAINED: Owner ({mint_authority[:8]}...{mint_authority[-4:]}) can mint unlimited tokens")
        score -= 30
    else:
        flags.append("MINT_AUTHORITY_REVOKED: Immutable supply confirmed")

    # Freeze Authority check (Honeypot risk)
    if freeze_authority is not None:
        flags.append(f"FREEZE_AUTHORITY_RETAINED: Owner ({freeze_authority[:8]}...{freeze_authority[-4:]}) can freeze user accounts (Honeypot risk)")
        score -= 40
    else:
        flags.append("FREEZE_AUTHORITY_REVOKED: Accounts cannot be frozen")

    # Token-2022 Extensions
    if is_token_2022:
        flags.append("TOKEN_2022_PROGRAM: Token uses SPL Token-2022 standard")
        for ext in extensions:
            ext_type = ext.get("extension", "")
            if ext_type == "transferHook":
                flags.append("EXTENSION_TRANSFER_HOOK: Custom transfer hook logic active (potential honeypot/fee trap)")
                score -= 35
            elif ext_type == "permanentDelegate":
                flags.append("EXTENSION_PERMANENT_DELEGATE: Permanent delegate active (can confiscate or burn user tokens)")
                score -= 40
            elif ext_type == "defaultAccountState":
                flags.append(f"EXTENSION_DEFAULT_STATE: Default account state set to {ext.get('state')}")
                score -= 20
            elif ext_type == "confidentialTransferMint":
                flags.append("EXTENSION_CONFIDENTIAL_TRANSFER: Confidential transfers enabled")
            else:
                flags.append(f"EXTENSION_DETECTED: {ext_type}")

    # Liquidity check
    if market_info["has_dex"]:
        if market_info["liquidity_usd"] < 5000:
            flags.append(f"LOW_LIQUIDITY: Only ${market_info['liquidity_usd']:,.2f} liquidity in DEX pool")
            score -= 20
    else:
        flags.append("NO_DEX_LIQUIDITY: No active DEX pool detected on Raydium/Orca/Pump.fun")
        score -= 25

    score = max(0, score)

    # Determine Verdict
    if freeze_authority is not None or any("TRANSFER_HOOK" in f or "PERMANENT_DELEGATE" in f for f in flags):
        verdict = "HIGH_RISK_TRAP" if freeze_authority is None else "HONEYPOT_CONFIRMED"
        severity = "CRITICAL"
    elif mint_authority is not None or score < 60:
        verdict = "HIGH_RISK_TRAP"
        severity = "HIGH"
    elif score < 80:
        verdict = "ELEVATED_RISK"
        severity = "MEDIUM"
    else:
        verdict = "SAFE"
        severity = "LOW"

    report = {
        "token": mint_address,
        "chain": "solana",
        "symbol": market_info.get("symbol", "SOL_TOKEN"),
        "name": market_info.get("base_token", "Solana Token"),
        "program": "Token-2022" if is_token_2022 else "Standard SPL",
        "decimals": decimals,
        "total_supply": supply,
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "is_mint_revoked": mint_authority is None,
        "is_freeze_revoked": freeze_authority is None,
        "score": score,
        "verdict": verdict,
        "severity": severity,
        "market": market_info,
        "flags": flags
    }

    if json_output:
        print(json.dumps(report, indent=2))
        return report

    # Terminal Pretty Printing
    print("\n" + "=" * 70)
    print(f" 🛡️  ON-CHAIN FORK & CONTRACT AUDITOR — {report['name']} ({report['symbol']}) [SOLANA]")
    print("=" * 70)
    print(f"  Token Address    : {mint_address}")
    print(f"  Token Standard   : {report['program']}")
    print(f"  Decimals / Supply: {decimals} decimals | {supply:,.2f} {report['symbol']}")
    print(f"  Security Verdict : {verdict} ({severity})")
    print(f"  Safety Score     : {score}/100")
    print("-" * 70)
    print("  🔑 AUTHORITY ANALYSIS:")
    print(f"     • Mint Authority  : {'✅ Revoked (Immutable supply)' if mint_authority is None else f'🚨 RETAINED ({mint_authority})'}")
    print(f"     • Freeze Authority: {'✅ Revoked (Cannot freeze)' if freeze_authority is None else f'🚨 RETAINED ({freeze_authority}) [Honeypot Risk]'}")
    print("-" * 70)
    print("  💧 DEX LIQUIDITY & MARKET:")
    if market_info["has_dex"]:
        print(f"     • DEX Protocol : {market_info['dex'].upper()}")
        print(f"     • Pair Address : {market_info['pair_address']}")
        print(f"     • Liquidity USD: ${market_info['liquidity_usd']:,.2f}")
        print(f"     • Token Price  : ${market_info['price_usd']:.8f}")
    else:
        print("     • Status       : ⚠️ No DEX pool found yet")
    print("-" * 70)
    print("  🚨 SECURITY AUDIT LOG:")
    for f in flags:
        prefix = "• ⚠️ " if ("RETAINED" in f or "LOW" in f or "HOOK" in f or "DELEGATE" in f) else "• ✅ "
        print(f"     {prefix}{f}")
    print("=" * 70 + "\n")

    return report
