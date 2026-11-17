from typing import Dict, Any
from web3 import Web3

FACTORY_CONFIGS = {
    "bsc": {
        "factory": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73", # PancakeFactory
        "weth": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    },
    "eth": {
        "factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", # UniswapV2Factory
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    "base": {
        "factory": "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6", # UniswapV2Factory on Base
        "weth": "0x4200000000000000000000000000000000000006",
    }
}

FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "type": "function"
    }
]

PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

DEAD_ADDRESSES = [
    "0x000000000000000000000000000000000000dEaD",
    "0x0000000000000000000000000000000000000000"
]

def check_liquidity_pool(w3: Web3, chain: str, token_address: str) -> Dict[str, Any]:
    cfg = FACTORY_CONFIGS.get(chain.lower())
    result = {
        "pair_address": None,
        "has_pair": False,
        "lp_burned_percent": 0.0,
        "is_lp_burned": False,
        "reserve_eth": 0.0,
        "reserve_tokens": 0.0,
        "total_lp_supply": 0,
        "note": ""
    }

    if not cfg:
        result["note"] = f"DEX factory not pre-configured for chain '{chain}'"
        return result

    factory_addr = Web3.to_checksum_address(cfg["factory"])
    weth_addr = Web3.to_checksum_address(cfg["weth"])
    token_addr = Web3.to_checksum_address(token_address)

    factory = w3.eth.contract(address=factory_addr, abi=FACTORY_ABI)

    try:
        pair_address = factory.functions.getPair(token_addr, weth_addr).call()
        if not pair_address or pair_address == "0x0000000000000000000000000000000000000000":
            return result

        result["pair_address"] = pair_address
        result["has_pair"] = True

        pair = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=PAIR_ABI)
        reserves = pair.functions.getReserves().call()
        total_lp = pair.functions.totalSupply().call()
        result["total_lp_supply"] = total_lp

        # Check burned LP
        burned_lp = 0
        for dead in DEAD_ADDRESSES:
            try:
                b = pair.functions.balanceOf(Web3.to_checksum_address(dead)).call()
                burned_lp += b
            except Exception:
                pass

        if total_lp > 0:
            burn_pct = round((burned_lp / total_lp) * 100, 2)
            result["lp_burned_percent"] = burn_pct
            result["is_lp_burned"] = burn_pct >= 95.0

    except Exception:
        pass

    return result
