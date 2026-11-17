import requests
import json
from typing import Dict, Any, List, Optional

SOLANA_DEFAULT_RPCS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana"
]

TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

# Known Solana DEX Program IDs
METEORA_DLMM_PROGRAM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
METEORA_DYNAMIC_PROGRAM = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
RAYDIUM_V4_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
ORCA_WHIRLPOOL_PROGRAM = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
PUMPFUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

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

def fetch_solana_dex_liquidity(mint_address: str) -> Dict[str, Any]:
    """
    Fetches and segregates on-chain liquidity pools across Meteora (DLMM & Dynamic),
    Raydium, Orca, and Pump.fun.
    """
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    result = {
        "has_dex": False,
        "total_liquidity_usd": 0.0,
        "primary_dex": "NONE",
        "token_name": "Solana Token",
        "token_symbol": "UNKNOWN",
        "price_usd": 0.0,
        "meteora": {
            "has_pool": False,
            "pool_count": 0,
            "total_liquidity_usd": 0.0,
            "top_pair_address": None,
            "pool_type": None,
            "quote_symbol": None,
            "volume_24h": 0.0,
            "price_usd": 0.0,
            "url": None
        },
        "raydium": {
            "has_pool": False,
            "pool_count": 0,
            "total_liquidity_usd": 0.0,
            "top_pair_address": None
        },
        "orca": {
            "has_pool": False,
            "pool_count": 0,
            "total_liquidity_usd": 0.0,
            "top_pair_address": None
        },
        "pumpfun": {
            "has_pool": False,
            "total_liquidity_usd": 0.0,
            "is_graduated": False
        }
    }

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code != 200:
            return result

        data = resp.json()
        pairs = data.get("pairs", [])
        if not pairs:
            return result

        result["has_dex"] = True
        
        # Meta info from the most liquid pair
        sorted_all = sorted(pairs, key=lambda x: (x.get("liquidity", {}) or {}).get("usd", 0), reverse=True)
        top_overall = sorted_all[0]
        result["token_name"] = top_overall.get("baseToken", {}).get("name", "Solana Token")
        result["token_symbol"] = top_overall.get("baseToken", {}).get("symbol", "UNKNOWN")
        result["price_usd"] = float(top_overall.get("priceUsd", 0.0) or 0.0)

        # Categorize by DEX
        meteora_pairs = [p for p in pairs if "meteora" in p.get("dexId", "").lower()]
        raydium_pairs = [p for p in pairs if "raydium" in p.get("dexId", "").lower()]
        orca_pairs = [p for p in pairs if "orca" in p.get("dexId", "").lower()]
        pump_pairs = [p for p in pairs if "pump" in p.get("dexId", "").lower()]

        # 1. Meteora Pools Analysis (DLMM & Dynamic Pools)
        if meteora_pairs:
            m_sorted = sorted(meteora_pairs, key=lambda x: (x.get("liquidity", {}) or {}).get("usd", 0), reverse=True)
            top_m = m_sorted[0]
            m_total_liq = sum(float((p.get("liquidity", {}) or {}).get("usd", 0.0)) for p in meteora_pairs)
            m_labels = top_m.get("labels", [])
            m_type = "DLMM" if any("DLMM" in str(lbl).upper() for lbl in m_labels) else "Dynamic AMM"

            result["meteora"] = {
                "has_pool": True,
                "pool_count": len(meteora_pairs),
                "total_liquidity_usd": m_total_liq,
                "top_pair_address": top_m.get("pairAddress"),
                "pool_type": m_type,
                "quote_symbol": top_m.get("quoteToken", {}).get("symbol", "SOL"),
                "volume_24h": float((top_m.get("volume", {}) or {}).get("h24", 0.0)),
                "price_usd": float(top_m.get("priceUsd", 0.0) or 0.0),
                "url": top_m.get("url")
            }

        # 2. Raydium Pools Analysis
        if raydium_pairs:
            r_sorted = sorted(raydium_pairs, key=lambda x: (x.get("liquidity", {}) or {}).get("usd", 0), reverse=True)
            r_total_liq = sum(float((p.get("liquidity", {}) or {}).get("usd", 0.0)) for p in raydium_pairs)
            result["raydium"] = {
                "has_pool": True,
                "pool_count": len(raydium_pairs),
                "total_liquidity_usd": r_total_liq,
                "top_pair_address": r_sorted[0].get("pairAddress")
            }

        # 3. Orca Pools Analysis
        if orca_pairs:
            o_sorted = sorted(orca_pairs, key=lambda x: (x.get("liquidity", {}) or {}).get("usd", 0), reverse=True)
            o_total_liq = sum(float((p.get("liquidity", {}) or {}).get("usd", 0.0)) for p in orca_pairs)
            result["orca"] = {
                "has_pool": True,
                "pool_count": len(orca_pairs),
                "total_liquidity_usd": o_total_liq,
                "top_pair_address": o_sorted[0].get("pairAddress")
            }

        # 4. Pump.fun Pools Analysis
        if pump_pairs:
            p_total_liq = sum(float((p.get("liquidity", {}) or {}).get("usd", 0.0)) for p in pump_pairs)
            result["pumpfun"] = {
                "has_pool": True,
                "total_liquidity_usd": p_total_liq,
                "is_graduated": len(raydium_pairs) > 0 or len(meteora_pairs) > 0
            }

        # Totals
        result["total_liquidity_usd"] = (
            result["meteora"]["total_liquidity_usd"] +
            result["raydium"]["total_liquidity_usd"] +
            result["orca"]["total_liquidity_usd"] +
            result["pumpfun"]["total_liquidity_usd"]
        )

        # Primary DEX
        venues = [
            ("Meteora", result["meteora"]["total_liquidity_usd"]),
            ("Raydium", result["raydium"]["total_liquidity_usd"]),
            ("Orca", result["orca"]["total_liquidity_usd"]),
            ("Pump.fun", result["pumpfun"]["total_liquidity_usd"])
        ]
        top_venue = max(venues, key=lambda x: x[1])
        result["primary_dex"] = top_venue[0].upper() if top_venue[1] > 0 else "NONE"

    except Exception:
        pass

    return result

def audit_solana_token(mint_address: str, custom_rpc: Optional[str] = None, json_output: bool = False) -> Dict[str, Any]:
    # 1. Fetch Mint Account Info from Solana RPC
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

    # 2. Comprehensive Multi-DEX & Meteora LP Analysis
    dex_info = fetch_solana_dex_liquidity(mint_address)

    # 3. Analyze Vulnerability Flags & Score
    flags = []
    score = 100

    # Mint Authority check
    if mint_authority is not None:
        flags.append(f"MINT_AUTHORITY_RETAINED: Owner ({mint_authority[:8]}...{mint_authority[-4:]}) can mint unlimited supply")
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

    # Meteora LP Status Check
    if dex_info["meteora"]["has_pool"]:
        m_data = dex_info["meteora"]
        flags.append(f"METEORA_LP_VERIFIED: {m_data['pool_count']} active Meteora {m_data['pool_type']} pool(s) found (${m_data['total_liquidity_usd']:,.2f} TVL)")
    else:
        flags.append("METEORA_LP_ABSENT: No active Meteora DLMM / Dynamic pool detected")

    # Liquidity check
    total_liq = dex_info["total_liquidity_usd"]
    if dex_info["has_dex"]:
        if total_liq < 5000:
            flags.append(f"LOW_LIQUIDITY: Only ${total_liq:,.2f} USD liquidity across all Solana DEXes")
            score -= 20
    else:
        flags.append("NO_DEX_LIQUIDITY: No active DEX pool detected on Solana AMMs")
        score -= 25

    score = max(0, score)

    # Determine Verdict
    if freeze_authority is not None or any("TRANSFER_HOOK" in f or "PERMANENT_DELEGATE" in f for f in flags):
        verdict = "HONEYPOT_CONFIRMED"
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
        "symbol": dex_info.get("token_symbol", "SOL_TOKEN"),
        "name": dex_info.get("token_name", "Solana Token"),
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
        "liquidity": dex_info,
        "flags": flags
    }

    if json_output:
        print(json.dumps(report, indent=2))
        return report

    # Terminal Pretty Printing
    print("\n" + "=" * 72)
    print(f" 🛡️  ON-CHAIN FORK & CONTRACT AUDITOR — {report['name']} ({report['symbol']}) [SOLANA]")
    print("=" * 72)
    print(f"  Token Address    : {mint_address}")
    print(f"  Token Standard   : {report['program']}")
    print(f"  Decimals / Supply: {decimals} decimals | {supply:,.2f} {report['symbol']}")
    print(f"  Security Verdict : {verdict} ({severity})")
    print(f"  Safety Score     : {score}/100")
    print("-" * 72)
    print("  🔑 AUTHORITY ANALYSIS:")
    print(f"     • Mint Authority  : {'✅ Revoked (Immutable supply)' if mint_authority is None else f'🚨 RETAINED ({mint_authority})'}")
    print(f"     • Freeze Authority: {'✅ Revoked (Cannot freeze)' if freeze_authority is None else f'🚨 RETAINED ({freeze_authority}) [Honeypot Risk]'}")
    print("-" * 72)
    print("  💧 LIQUIDITY POOL (LP) DISTRIBUTION:")
    if dex_info["has_dex"]:
        print(f"     • Combined DEX TVL: ${dex_info['total_liquidity_usd']:,.2f} USD")
        print(f"     • Primary LP Venue: {dex_info['primary_dex']}")
        print(f"     • Token Price     : ${dex_info['price_usd']:.8f} USD")
        print("")
        print("     🪐 METEORA POOLS:")
        m = dex_info["meteora"]
        if m["has_pool"]:
            print(f"        • Status          : ✅ Active ({m['pool_count']} pool(s) found)")
            print(f"        • Architecture    : Meteora {m['pool_type']}")
            print(f"        • Top Pool Address: {m['top_pair_address']} ({report['symbol']}/{m['quote_symbol']})")
            print(f"        • Meteora TVL     : ${m['total_liquidity_usd']:,.2f} USD")
            print(f"        • 24h Volume      : ${m['volume_24h']:,.2f} USD")
        else:
            print("        • Status          : ⚠️ No Meteora pool found")

        print("")
        print("     ⚡ OTHER SOLANA VENUES:")
        r = dex_info["raydium"]
        o = dex_info["orca"]
        p = dex_info["pumpfun"]
        r_str = f"${r['total_liquidity_usd']:,.2f} USD ({r['pool_count']} pools)" if r["has_pool"] else "None"
        o_str = f"${o['total_liquidity_usd']:,.2f} USD ({o['pool_count']} pools)" if o["has_pool"] else "None"
        p_str = f"Active Liquidity (${p['total_liquidity_usd']:,.2f})" if p["has_pool"] else "Migrated / Direct AMM"
        print(f"        • Raydium Pools   : {r_str}")
        print(f"        • Orca Pools      : {o_str}")
        print(f"        • Pump.fun        : {p_str}")
    else:
        print("     • Status          : ⚠️ No active DEX liquidity detected on Solana")

    print("-" * 72)
    print("  🚨 SECURITY AUDIT LOG:")
    for f in flags:
        prefix = "• ⚠️ " if ("RETAINED" in f or "LOW" in f or "HOOK" in f or "DELEGATE" in f or "ABSENT" in f) else "• ✅ "
        print(f"     {prefix}{f}")
    print("=" * 72 + "\n")

    return report
