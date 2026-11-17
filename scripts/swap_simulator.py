import time
from typing import Dict, Any
from web3 import Web3

# Standard Router & WETH configurations
CHAIN_CONFIGS = {
    "bsc": {
        "router": "0x10ED43C718714eb63d5aA57B78B54704E256024E", # PancakeSwap V2
        "weth": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",   # WBNB
        "native_symbol": "BNB"
    },
    "eth": {
        "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", # Uniswap V2
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "native_symbol": "ETH"
    },
    "base": {
        "router": "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24", # Uniswap V2 on Base
        "weth": "0x4200000000000000000000000000000000000006",   # WETH
        "native_symbol": "ETH"
    }
}

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def simulate_token_swap(w3: Web3, chain: str, token_address: str, test_amount_eth: float = 0.1) -> Dict[str, Any]:
    chain_cfg = CHAIN_CONFIGS.get(chain.lower(), CHAIN_CONFIGS["bsc"])
    router_addr = Web3.to_checksum_address(chain_cfg["router"])
    weth_addr = Web3.to_checksum_address(chain_cfg["weth"])
    token_addr = Web3.to_checksum_address(token_address)

    router_contract = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
    token_contract = w3.eth.contract(address=token_addr, abi=ERC20_ABI)

    result = {
        "chain": chain,
        "token_address": token_addr,
        "is_honeypot": False,
        "honeypot_reason": None,
        "buy_tax_percent": 0.0,
        "sell_tax_percent": 0.0,
        "can_buy": False,
        "can_sell": False,
        "liquidity_detected": False,
        "symbol": "TOKEN",
        "decimals": 18
    }

    try:
        result["symbol"] = token_contract.functions.symbol().call()
        result["decimals"] = token_contract.functions.decimals().call()
    except Exception:
        pass

    # 1. Query Pair Liquidity via getAmountsOut
    amount_in_wei = Web3.to_wei(test_amount_eth, "ether")
    path_buy = [weth_addr, token_addr]

    try:
        amounts_out = router_contract.functions.getAmountsOut(amount_in_wei, path_buy).call()
        expected_tokens_out = amounts_out[1]
        if expected_tokens_out > 0:
            result["liquidity_detected"] = True
            result["can_buy"] = True
    except Exception as e:
        err_msg = str(e)
        if "INSUFFICIENT_LIQUIDITY" in err_msg or "PancakeLibrary" in err_msg or "UniswapV2" in err_msg:
            result["honeypot_reason"] = "No active liquidity pool found on primary router."
            return result
        result["honeypot_reason"] = f"Router getAmountsOut failed: {err_msg[:80]}"
        return result

    # 2. Simulate Sell path via getAmountsOut
    path_sell = [token_addr, weth_addr]
    try:
        sell_amounts_out = router_contract.functions.getAmountsOut(expected_tokens_out, path_sell).call()
        expected_eth_back = sell_amounts_out[1]
        result["can_sell"] = True
        
        # Calculate theoretical roundtrip tax
        initial_eth = amount_in_wei
        roundtrip_loss = max(0, initial_eth - expected_eth_back)
        approx_tax = (roundtrip_loss / initial_eth) * 100
        
        # Rough split between buy/sell slippage + tax
        result["buy_tax_percent"] = round(min(99.9, max(0.0, (approx_tax / 2) - 0.3)), 2)
        result["sell_tax_percent"] = round(min(99.9, max(0.0, (approx_tax / 2) - 0.3)), 2)

    except Exception as e:
        err_str = str(e).lower()
        result["can_sell"] = False
        result["is_honeypot"] = True
        result["honeypot_reason"] = f"Cannot calculate sell return: {str(e)[:100]}"
        return result

    # 3. Check for Extreme Predatory Taxes (> 50%)
    if result["sell_tax_percent"] >= 50.0 or result["buy_tax_percent"] >= 50.0:
        result["is_honeypot"] = True
        result["honeypot_reason"] = f"Predatory tax detected: Buy ~{result['buy_tax_percent']}%, Sell ~{result['sell_tax_percent']}%"

    return result
