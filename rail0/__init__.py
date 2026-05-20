"""RAIL0 Python SDK — stablecoin payment protocol client."""

from .client import Rail0Client
from .core.error import Rail0ApiError
from .core.http import LogEntry, Logger, debug_logger
from .resources.types import (
    # Primitives
    Address,
    Bytes32,
    Uint256String,
    # Core models
    PaymentConfig,
    PaymentInput,
    EIP712Domain,
    EIP3009Message,
    SigningPayload,
    # Request bodies
    CreatePaymentRequest,
    PayerSignatureRequest,
    CapturePaymentRequest,
    SubmitTransactionRequest,
    ApproveRequest,
    RefundPaymentRequest,
    # Response shapes
    CreatePaymentResponse,
    PayerSignatureResponse,
    AuthorizePaymentResponse,
    ChargePaymentResponse,
    PrepareTransactionResponse,
    CapturePaymentResponse,
    VoidPaymentResponse,
    ReleasePaymentResponse,
    ApproveResponse,
    RefundPaymentResponse,
    PaymentMethod,
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
    # Core models
    "PaymentConfig",
    "PaymentInput",
    "EIP712Domain",
    "EIP3009Message",
    "SigningPayload",
    # Request bodies
    "CreatePaymentRequest",
    "PayerSignatureRequest",
    "CapturePaymentRequest",
    "SubmitTransactionRequest",
    "ApproveRequest",
    "RefundPaymentRequest",
    # Response shapes
    "CreatePaymentResponse",
    "PayerSignatureResponse",
    "AuthorizePaymentResponse",
    "ChargePaymentResponse",
    "PrepareTransactionResponse",
    "CapturePaymentResponse",
    "VoidPaymentResponse",
    "ReleasePaymentResponse",
    "ApproveResponse",
    "RefundPaymentResponse",
    "PaymentMethod",
    "ApiErrorBody",
    # Stablecoins
    "StablecoinInfo",
    "ChainStablecoins",
    "stablecoins",
    "chain_info",
    "eip3009_tokens",
    "eip2612_tokens",
]
