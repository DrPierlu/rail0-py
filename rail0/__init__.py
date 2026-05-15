"""RAIL0 Python SDK — stablecoin payment protocol client."""

from .client import Rail0Client
from .core.error import Rail0ApiError
from .core.http import LogEntry, Logger, debug_logger
from .resources.types import (
    # Primitives
    Address,
    Bytes32,
    Uint256String,
    # Core model
    Payment,
    PaymentState,
    # Request params
    AuthorizeParams,
    ChargeParams,
    CaptureParams,
    VoidParams,
    ReleaseParams,
    RefundParams,
    # Response shapes
    PaymentResponse,
    TransactionResponse,
    TransactionStatus,
    TokenStatusResponse,
    HashResponse,
    NonceResponse,
    DomainSeparatorResponse,
    VersionResponse,
    ApiErrorBody,
)
from .stablecoins import StablecoinInfo, ChainStablecoins, stablecoins, chain_info, eip3009_tokens, eip2612_tokens

__all__ = [
    # Client
    "Rail0Client",
    # Error
    "Rail0ApiError",
    # Logging
    "LogEntry",
    "Logger",
    "debug_logger",
    # Primitives
    "Address",
    "Bytes32",
    "Uint256String",
    # Core model
    "Payment",
    "PaymentState",
    # Request params
    "AuthorizeParams",
    "ChargeParams",
    "CaptureParams",
    "VoidParams",
    "ReleaseParams",
    "RefundParams",
    # Response shapes
    "PaymentResponse",
    "TransactionResponse",
    "TransactionStatus",
    "TokenStatusResponse",
    "HashResponse",
    "NonceResponse",
    "DomainSeparatorResponse",
    "VersionResponse",
    "ApiErrorBody",
    # Stablecoins
    "StablecoinInfo",
    "ChainStablecoins",
    "stablecoins",
    "chain_info",
    "eip3009_tokens",
    "eip2612_tokens",
]
