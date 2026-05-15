"""Stablecoin addresses and capabilities for supported EVM networks.

eip3009 — transferWithAuthorization (Circle / USDC standard).
eip2612 — permit (ERC-20 extension).
bridged  — token is a bridge-wrapped variant and may not support either extension.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StablecoinInfo:
    """Static metadata for a single stablecoin on a specific chain."""

    address: str
    """Checksummed contract address."""

    decimals: int
    """Number of decimal places (typically 6 for USDC/USDT, 18 for DAI)."""

    eip3009: bool
    """Supports transferWithAuthorization (EIP-3009 / Circle standard). Required by RAIL0."""

    eip2612: bool
    """Supports permit (EIP-2612). Not used by RAIL0 but useful for other integrations."""

    bridged: Optional[bool] = field(default=None)
    """Token is a bridge-wrapped variant and may not support either auth extension."""


@dataclass(frozen=True)
class ChainStablecoins:
    chain_id: int
    tokens: dict[str, StablecoinInfo]


stablecoins: dict[str, ChainStablecoins] = {
    "ethereum": ChainStablecoins(
        chain_id=1,
        tokens={
            "USDC": StablecoinInfo(
                address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "EURC": StablecoinInfo(
                address="0x1aBaEA1f7C830bD89Acc67eC4af516284b1bC33c",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "PYUSD": StablecoinInfo(
                address="0x6c3ea9036406852006290770BEdFcAbA0e23A0e8",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDT": StablecoinInfo(
                address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                decimals=6,
                eip3009=False,
                eip2612=False,
            ),
            "DAI": StablecoinInfo(
                address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
                decimals=18,
                eip3009=False,
                eip2612=True,
            ),
        },
    ),
    "base": ChainStablecoins(
        chain_id=8453,
        tokens={
            "USDC": StablecoinInfo(
                address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "EURC": StablecoinInfo(
                address="0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDbC": StablecoinInfo(
                address="0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
                decimals=6,
                eip3009=False,
                eip2612=False,
                bridged=True,
            ),
        },
    ),
    "polygon": ChainStablecoins(
        chain_id=137,
        tokens={
            "USDC": StablecoinInfo(
                address="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDC.e": StablecoinInfo(
                address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                decimals=6,
                eip3009=True,
                eip2612=False,
                bridged=True,
            ),
            "USDT": StablecoinInfo(
                address="0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                decimals=6,
                eip3009=False,
                eip2612=False,
            ),
            "DAI": StablecoinInfo(
                address="0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                decimals=18,
                eip3009=False,
                eip2612=False,
            ),
        },
    ),
    "arbitrumOne": ChainStablecoins(
        chain_id=42161,
        tokens={
            "USDC": StablecoinInfo(
                address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDC.e": StablecoinInfo(
                address="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                decimals=6,
                eip3009=False,
                eip2612=False,
                bridged=True,
            ),
            "USDT": StablecoinInfo(
                address="0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                decimals=6,
                eip3009=False,
                eip2612=False,
            ),
            "DAI": StablecoinInfo(
                address="0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                decimals=18,
                eip3009=False,
                eip2612=True,
            ),
        },
    ),
    "optimism": ChainStablecoins(
        chain_id=10,
        tokens={
            "USDC": StablecoinInfo(
                address="0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDC.e": StablecoinInfo(
                address="0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                decimals=6,
                eip3009=False,
                eip2612=False,
                bridged=True,
            ),
            "USDT": StablecoinInfo(
                address="0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
                decimals=6,
                eip3009=False,
                eip2612=False,
            ),
            "DAI": StablecoinInfo(
                address="0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                decimals=18,
                eip3009=False,
                eip2612=True,
            ),
        },
    ),
    "avalanche": ChainStablecoins(
        chain_id=43114,
        tokens={
            "USDC": StablecoinInfo(
                address="0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "USDC.e": StablecoinInfo(
                address="0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",
                decimals=6,
                eip3009=False,
                eip2612=False,
                bridged=True,
            ),
            "USDT": StablecoinInfo(
                address="0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
                decimals=6,
                eip3009=False,
                eip2612=False,
            ),
        },
    ),
    "celo": ChainStablecoins(
        chain_id=42220,
        tokens={
            "USDC": StablecoinInfo(
                address="0xcebA9300f2b948710d2De3250b7Ad3e4aFb0e50a",
                decimals=6,
                eip3009=True,
                eip2612=False,
            ),
            "cUSD": StablecoinInfo(
                address="0x765DE816845861e75A25fCA122bb6898B8B1282a",
                decimals=18,
                eip3009=True,
                eip2612=False,
            ),
            "cEUR": StablecoinInfo(
                address="0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73",
                decimals=18,
                eip3009=True,
                eip2612=False,
            ),
        },
    ),
}


def chain_info(chain: str) -> Optional[ChainStablecoins]:
    """Returns the registry entry for a chain, or None if the chain is unknown.

    Supported chain names: "ethereum", "base", "polygon", "arbitrumOne",
    "optimism", "avalanche", "celo".
    """
    return stablecoins.get(chain)


def eip3009_tokens(chain: str) -> list[dict[str, object]]:
    """Returns all tokens on a chain that support EIP-3009 (transferWithAuthorization)."""
    chain_data = stablecoins[chain]
    return [
        {"symbol": symbol, "address": info.address, "decimals": info.decimals}
        for symbol, info in chain_data.tokens.items()
        if info.eip3009
    ]


def eip2612_tokens(chain: str) -> list[dict[str, object]]:
    """Returns all tokens on a chain that support EIP-2612 (permit)."""
    chain_data = stablecoins[chain]
    return [
        {"symbol": symbol, "address": info.address, "decimals": info.decimals}
        for symbol, info in chain_data.tokens.items()
        if info.eip2612
    ]
