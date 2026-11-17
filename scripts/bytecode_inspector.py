import re
from typing import Dict, Any, List
from web3 import Web3

# Known 4-byte selector signatures for malicious / risky token functions
KNOWN_SELECTORS = {
    # Blacklist & Bot traps
    "0xa04e8d38": "isBlacklisted(address)",
    "0xec442f05": "blacklist(address)",
    "0x892e8549": "addBlacklist(address)",
    "0x572b6c05": "setBlacklist(address,bool)",
    "0x054659b9": "setBot(address,bool)",
    "0xb838b935": "isBot(address)",
    
    # Hidden Mint / Supply Inflation
    "0x40c10f19": "mint(address,uint256)",
    "0xa0712d68": "mint(uint256)",
    "0x02877a5e": "ownerMint(uint256)",
    "0x7565538e": "mintTo(address,uint256)",

    # Tax & Fee traps
    "0x91b7f5ed": "setTax(uint256)",
    "0x2914101b": "setFee(uint256)",
    "0x7856b3e0": "setBuyFee(uint256)",
    "0x68551a37": "setSellFee(uint256)",
    "0x8a920671": "setFees(uint256,uint256,uint256)",
    
    # Trading Pausable / Traps
    "0x025e3299": "setTrading(bool)",
    "0xc9567bf9": "openTrading()",
    "0x8456cb59": "pause()",
    "0x3f4ba83a": "unpause()",
    "0x4bf20008": "enableTrading()",
    
    # Max Wallet / Max Tx Traps
    "0x658d533d": "setMaxTxPercent(uint256)",
    "0x5ce98e0c": "setMaxWalletPercent(uint256)",
    "0x559e2f89": "setMaxTxAmount(uint256)",

    # Ownership
    "0x715018a6": "renounceOwnership()",
    "0xf2fde38b": "transferOwnership(address)",
    "0x8da5cb5b": "owner()",
}

def extract_selectors_from_bytecode(bytecode_hex: str) -> List[str]:
    """
    Extracts PUSH4 / function dispatcher selectors from raw runtime bytecode.
    Standard EVM pattern: PUSH4 (0x63) followed by 4 bytes.
    """
    if bytecode_hex.startswith("0x"):
        bytecode_hex = bytecode_hex[2:]

    selectors = set()
    matches = re.findall(r'63([0-9a-fA-F]{8})', bytecode_hex)
    for m in matches:
        selectors.add(f"0x{m.lower()}")
    return sorted(list(selectors))

def analyze_bytecode(w3: Web3, token_address: str) -> Dict[str, Any]:
    address = Web3.to_checksum_address(token_address)
    bytecode = w3.eth.get_code(address).hex()

    if not bytecode or bytecode == "0x":
        return {
            "is_contract": False,
            "error": "Address is not a contract or has no code deployed."
        }

    raw_code = bytecode.lower()
    selectors = extract_selectors_from_bytecode(raw_code)

    has_delegatecall = "f4" in raw_code # DELEGATECALL opcode
    has_selfdestruct = "ff" in raw_code # SELFDESTRUCT opcode

    flagged_features = []
    risk_score = 0

    # 1. Match selectors against known risky patterns
    matched_functions = []
    has_blacklist = False
    has_hidden_mint = False
    has_fee_manipulation = False
    has_trading_toggle = False

    for sel in selectors:
        if sel in KNOWN_SELECTORS:
            func_name = KNOWN_SELECTORS[sel]
            matched_functions.append({"selector": sel, "function": func_name})
            
            if "blacklist" in func_name.lower() or "bot" in func_name.lower():
                has_blacklist = True
            elif "mint" in func_name.lower():
                has_hidden_mint = True
            elif "fee" in func_name.lower() or "tax" in func_name.lower():
                has_fee_manipulation = True
            elif "trading" in func_name.lower() or "pause" in func_name.lower():
                has_trading_toggle = True

    # 2. Risk scoring heuristics
    if has_blacklist:
        flagged_features.append("🚨 Blacklist / Bot-Trap functions detected (owner can freeze wallets)")
        risk_score += 35

    if has_hidden_mint:
        flagged_features.append("⚠️ Mint function detected (potential supply dilution / infinite mint)")
        risk_score += 25

    if has_fee_manipulation:
        flagged_features.append("⚠️ Dynamic fee setter detected (owner can increase sell tax after launch)")
        risk_score += 20

    if has_trading_toggle:
        flagged_features.append("⚠️ Trading pause/enable switch detected (owner can disable sells)")
        risk_score += 20

    if has_delegatecall:
        flagged_features.append("🔍 DELEGATECALL opcode found (Proxy contract or external logic delegation)")
        risk_score += 15

    if has_selfdestruct:
        flagged_features.append("🚨 SELFDESTRUCT opcode found (contract can be erased from state)")
        risk_score += 40

    risk_score = min(100, risk_score)

    return {
        "is_contract": True,
        "bytecode_size_bytes": len(bytecode) // 2,
        "risk_score": risk_score,
        "has_blacklist": has_blacklist,
        "has_hidden_mint": has_hidden_mint,
        "has_fee_manipulation": has_fee_manipulation,
        "has_trading_toggle": has_trading_toggle,
        "has_delegatecall": has_delegatecall,
        "has_selfdestruct": has_selfdestruct,
        "flagged_features": flagged_features,
        "matched_selectors": matched_functions,
        "total_selectors_found": len(selectors)
    }
