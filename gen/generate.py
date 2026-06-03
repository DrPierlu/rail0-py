#!/usr/bin/env python3
"""
Code generator for the RAIL0 Python SDK.

Reads the OpenAPI schema from ../rail0-api/docs/openapi.json
(or the path in the RAIL0_SCHEMA_PATH env var) and writes:
  - rail0/resources/types.py
  - rail0/resources/accounts.py
  - rail0/resources/payments.py
  - rail0/resources/chains.py
  - rail0/resources/tokens.py

Usage:
    python gen/generate.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_SCHEMA_PATH = REPO_ROOT.parent / "rail0-api" / "docs" / "openapi.json"
SCHEMA_PATH = Path(os.environ.get("RAIL0_SCHEMA_PATH", str(DEFAULT_SCHEMA_PATH)))
RESOURCES_DIR = REPO_ROOT / "rail0" / "resources"

# ---------------------------------------------------------------------------
# Helpers for types.py generation
# ---------------------------------------------------------------------------

# Schemas whose type is `string` (no `properties`) — emitted as simple aliases.
PRIMITIVE_ALIASES: Dict[str, str] = {
    "Address": "Checksummed or lowercase Ethereum address (42 chars, 0x-prefixed).",
    "Bytes32": "32-byte value, hex-encoded (66 chars, 0x-prefixed). Used for payment IDs, hashes, and signature components.",
    "Uint256String": "Unsigned 256-bit integer serialised as a decimal string. Avoids precision loss for large amounts.",
}

# Schema name → Python class name overrides.
CLASS_NAME_OVERRIDES: Dict[str, str] = {
    "Error": "ApiErrorBody",
}

# Fields that are Python keywords and must be renamed.
# Maps (schema_name, json_field_name) → python_field_name.
KEYWORD_RENAMES: Dict[Tuple[str, str], str] = {
    ("EIP3009Message", "from"): "from_",
}

# Desired output order (dependency order).  Schemas not listed here are
# appended after all listed ones in the order they appear in the source file.
EMIT_ORDER = [
    "Address",
    "Bytes32",
    "Uint256String",
    "PaymentConfig",
    "PaymentInput",
    "EIP712Domain",
    "EIP3009Message",
    "SigningPayload",
    "CreatePaymentRequest",
    "PayerSignatureRequest",
    "CapturePaymentRequest",
    "SubmitTransactionRequest",
    "SubmitTransactionAcceptedResponse",
    "ReleaseRequest",
    "RefundPaymentRequest",
    "CreatePaymentResponse",
    "PayerSignatureResponse",
    "GetPaymentResponse",
    "PrepareTransactionResponse",
    "PaymentMethod",
    "WalletToken",
    "PaymentSummary",
    "TransactionRecord",
    "Transaction",
    "Error",
]


def ref_name(ref: str) -> str:
    """Extract schema name from a $ref string."""
    return ref.split("/")[-1]


def python_class_name(schema_name: str) -> str:
    return CLASS_NAME_OVERRIDES.get(schema_name, schema_name)


def resolve_field_type(
    prop_schema: Dict[str, Any],
    schemas: Dict[str, Any],
) -> str:
    """
    Return the Python type annotation string for a single property schema.
    """
    # Direct $ref
    if "$ref" in prop_schema:
        return python_class_name(ref_name(prop_schema["$ref"]))

    # allOf with a single $ref (OpenAPI pattern for adding a description to a $ref)
    if "allOf" in prop_schema:
        items = prop_schema["allOf"]
        if len(items) == 1 and "$ref" in items[0]:
            return python_class_name(ref_name(items[0]["$ref"]))

    typ = prop_schema.get("type")

    if typ == "string":
        if "enum" in prop_schema:
            vals = ", ".join(f'"{v}"' for v in prop_schema["enum"])
            return f"Literal[{vals}]"
        return "str"

    if typ == "integer":
        return "int"

    if typ == "number":
        return "float"

    if typ == "boolean":
        return "bool"

    if typ == "array":
        items = prop_schema.get("items", {})
        if "$ref" in items:
            return f"List[{python_class_name(ref_name(items['$ref']))}]"
        if items.get("type") == "object":
            return "List[Dict[str, Any]]"
        # Fallback for other array item types
        inner = resolve_field_type(items, schemas)
        return f"List[{inner}]"

    if typ == "object":
        return "Dict[str, Any]"

    # Fallback
    return "Any"


def emit_alias(name: str, description: str) -> str:
    lines = [f"{name} = str", f'"""{description}"""', "", ""]
    return "\n".join(lines)


def emit_typeddict(
    schema_name: str,
    schema: Dict[str, Any],
    schemas: Dict[str, Any],
) -> str:
    class_name = python_class_name(schema_name)
    description = schema.get("description", "")
    required_fields: Set[str] = set(schema.get("required", []))
    properties: Dict[str, Any] = schema.get("properties", {})

    # Split into required and optional field lists (preserving source order)
    req_fields: List[Tuple[str, str, str, str]] = []   # (json_name, py_name, type_str, desc)
    opt_fields: List[Tuple[str, str, str, str]] = []

    for json_name, prop_schema in properties.items():
        # Handle Python keyword renames
        py_name = KEYWORD_RENAMES.get((schema_name, json_name), json_name)
        type_str = resolve_field_type(prop_schema, schemas)
        prop_desc = prop_schema.get("description", "")

        if json_name in required_fields:
            req_fields.append((json_name, py_name, type_str, prop_desc))
        else:
            opt_fields.append((json_name, py_name, type_str, prop_desc))

    lines: List[str] = []

    has_required = bool(req_fields)
    has_optional = bool(opt_fields)

    if has_required and has_optional:
        # Inheritance pattern: _<Name>Required base + <Name>(base, total=False)
        base_name = f"_{class_name}Required"

        # Base class (all required fields)
        lines.append(f"class {base_name}(TypedDict):")
        if description:
            lines.append(f'    """{description}"""')
            lines.append("")
        for (json_name, py_name, type_str, prop_desc) in req_fields:
            if py_name != json_name:
                lines.append(f'    # JSON key: "{json_name}"')
            lines.append(f"    {py_name}: {type_str}")
        lines.append("")
        lines.append("")

        # Subclass for optional fields
        lines.append(f"class {class_name}({base_name}, total=False):")
        for (json_name, py_name, type_str, prop_desc) in opt_fields:
            if py_name != json_name:
                lines.append(f'    # JSON key: "{json_name}"')
            lines.append(f"    {py_name}: {type_str}")

    elif not has_required:
        # All optional
        lines.append(f"class {class_name}(TypedDict, total=False):")
        if description:
            lines.append(f'    """{description}"""')
            lines.append("")
        if not properties:
            lines.append("    ...")
        else:
            for (json_name, py_name, type_str, prop_desc) in opt_fields:
                if py_name != json_name:
                    lines.append(f'    # JSON key: "{json_name}"')
                lines.append(f"    {py_name}: {type_str}")

    else:
        # All required
        lines.append(f"class {class_name}(TypedDict):")
        if description:
            lines.append(f'    """{description}"""')
            lines.append("")
        if not properties:
            lines.append("    ...")
        else:
            for (json_name, py_name, type_str, prop_desc) in req_fields:
                if py_name != json_name:
                    lines.append(f'    # JSON key: "{json_name}"')
                lines.append(f"    {py_name}: {type_str}")

    lines.append("")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate types.py
# ---------------------------------------------------------------------------

def generate_types(schemas: Dict[str, Any], output_path: Path) -> None:
    # Determine emit order: use EMIT_ORDER first, then any remaining schemas.
    ordered_names: List[str] = []
    for name in EMIT_ORDER:
        if name in schemas:
            ordered_names.append(name)
    for name in schemas:
        if name not in ordered_names:
            ordered_names.append(name)

    parts: List[str] = []

    # File header
    parts.append('''\
# GENERATED — DO NOT EDIT. Run `python gen/generate.py` to regenerate.
"""
Public types for the RAIL0 Python SDK.

All types mirror the OpenAPI schema in rail0-api/docs/openapi.json.
Request / response bodies use camelCase keys to match the JSON wire format.

This file is generated — do not hand-edit. Run `python gen/generate.py` to regenerate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal
from typing_extensions import TypedDict
''')

    # ---- Primitive aliases ----
    parts.append("\n# ================================================================\n")
    parts.append("#  Primitive aliases\n")
    parts.append("# ================================================================\n\n")

    for name in ordered_names:
        if name in PRIMITIVE_ALIASES:
            parts.append(emit_alias(name, PRIMITIVE_ALIASES[name]))

    # ---- TypedDicts ----
    sections = [
        ("Core models", ["PaymentConfig", "PaymentInput", "EIP712Domain", "EIP3009Message", "SigningPayload"]),
        ("Request bodies", ["CreatePaymentRequest", "PayerSignatureRequest", "CapturePaymentRequest",
                            "SubmitTransactionRequest", "SubmitTransactionAcceptedResponse",
                            "ReleaseRequest", "RefundPaymentRequest"]),
        ("Response shapes", ["CreatePaymentResponse", "PayerSignatureResponse", "GetPaymentResponse",
                              "PrepareTransactionResponse", "PaymentMethod",
                              "WalletToken", "PaymentSummary", "TransactionRecord",
                              "Transaction", "Error"]),
    ]

    # Collect which names are in a section
    sectioned: Set[str] = set()
    for _, names in sections:
        sectioned.update(names)

    for section_title, section_names in sections:
        emitted_any = False
        for name in section_names:
            if name not in schemas:
                continue
            schema = schemas[name]
            if name in PRIMITIVE_ALIASES:
                continue  # already emitted above
            if not emitted_any:
                parts.append(
                    f"# ================================================================\n"
                    f"#  {section_title}\n"
                    f"# ================================================================\n\n\n"
                )
                emitted_any = True
            parts.append(emit_typeddict(name, schema, schemas))

    # Any schema not covered by sections or primitives
    remainder = [n for n in ordered_names if n not in sectioned and n not in PRIMITIVE_ALIASES]
    if remainder:
        parts.append(
            "\n# ================================================================\n"
            "#  Other\n"
            "# ================================================================\n\n\n"
        )
        for name in remainder:
            schema = schemas[name]
            parts.append(emit_typeddict(name, schema, schemas))

    # Also add extra hardcoded types
    parts.append('''
# ================================================================
#  Pagination helpers (not in OpenAPI spec)
# ================================================================


class PageMeta(TypedDict):
    """Pagination metadata returned by list endpoints."""

    page: int
    per_page: int
    total: int


class PaginatedResponse(TypedDict):
    """Generic paginated list response."""

    data: List[Any]
    meta: PageMeta
''')

    output = "".join(parts).rstrip("\n") + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(output)

    print(f"Generated {output_path}")


# ---------------------------------------------------------------------------
# Generate resource files
# ---------------------------------------------------------------------------

FILE_HEADER = "# GENERATED — DO NOT EDIT. Run `python gen/generate.py` to regenerate."


def generate_chains(output_path: Path) -> None:
    content = f'''{FILE_HEADER}
from __future__ import annotations

from typing import List, TypedDict

from ..core.http import HttpClient


class Blockchain(TypedDict):
    chain_id: int
    name: str
    slug: str
    network_type: str
    explorer_url: str


class ChainsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> List[Blockchain]:
        """List all active blockchains supported by RAIL0."""
        return self._http.get("/blockchains")
'''
    output_path.write_text(content)
    print(f"Generated {output_path}")


def generate_tokens(output_path: Path) -> None:
    content = f'''{FILE_HEADER}
from __future__ import annotations

from typing import List, Optional, TypedDict

from ..core.http import HttpClient


class Token(TypedDict):
    chain_id: int
    chain_slug: str
    symbol: str
    address: str
    decimals: int


class TokensResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, chain_id: Optional[int] = None) -> List[Token]:
        """List active tokens. Pass chain_id to filter by chain."""
        path = f"/tokens?chain_id={{chain_id}}" if chain_id else "/tokens"
        return self._http.get(path)
'''
    output_path.write_text(content)
    print(f"Generated {output_path}")


def generate_accounts(output_path: Path) -> None:
    content = f'''{FILE_HEADER}
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..core.http import HttpClient
from .types import PageMeta, PaginatedResponse, PaymentMethod, WalletToken


class AccountsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def payment_methods(self, account_id: str) -> List[PaymentMethod]:
        """Return the active payment methods (chain + token + wallet) for the given account."""
        return self._http.get(f"/accounts/{{account_id}}/payment-methods")

    def wallets(
        self,
        account_id: str,
        *,
        chain_id: Optional[int] = None,
        chain_slug: Optional[str] = None,
        token_symbol: Optional[str] = None,
        active: Optional[bool] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List wallet tokens for an account. Public — no JWT required."""
        params: Dict[str, Any] = {{}}
        if chain_id is not None:
            params["chain_id"] = chain_id
        if chain_slug is not None:
            params["chain_slug"] = chain_slug
        if token_symbol is not None:
            params["token_symbol"] = token_symbol
        if active is not None:
            params["active"] = "true" if active else "false"
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/accounts/{{account_id}}/wallets{{qs}}")

    def wallet(self, account_id: str, wallet_id: str) -> WalletToken:
        """Fetch a single wallet token by id for the given account."""
        return self._http.get(f"/accounts/{{account_id}}/wallets/{{wallet_id}}")
'''
    output_path.write_text(content)
    print(f"Generated {output_path}")


def generate_payments(output_path: Path) -> None:
    content = f'''{FILE_HEADER}
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..core.http import HttpClient
from .types import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    CapturePaymentRequest,
    PageMeta,
    PaginatedResponse,
    PayerSignatureRequest,
    PayerSignatureResponse,
    PrepareTransactionResponse,
    ReleaseRequest,
    SubmitTransactionRequest,
    SubmitTransactionAcceptedResponse,
    WalletToken,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        payer: Optional[str] = None,
        payee: Optional[str] = None,
        token: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List payments for the authenticated wallet (requires JWT)."""
        params: Dict[str, Any] = {{}}
        if status is not None:
            params["status"] = status
        if mode is not None:
            params["mode"] = mode
        if payer is not None:
            params["payer"] = payer
        if payee is not None:
            params["payee"] = payee
        if token is not None:
            params["token"] = token
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/payments{{qs}}")

    def create(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        """Create a payment intent. Returns the EIP-712 signingPayload for the payer to sign."""
        return self._http.post("/payments", dict(params))

    def get(self, rail0_id: str) -> Any:
        """Fetch current payment state (DB status + live on-chain amounts)."""
        return self._http.get(f"/payments/{{rail0_id}}")

    def transactions(
        self,
        rail0_id: str,
        *,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List on-chain transactions for a payment."""
        params: Dict[str, Any] = {{}}
        if operation is not None:
            params["operation"] = operation
        if status is not None:
            params["status"] = status
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/payments/{{rail0_id}}/transactions{{qs}}")

    def sign(self, payment_id: str, params: PayerSignatureRequest) -> PayerSignatureResponse:
        """Submit the payer's EIP-712 signature (v, r, s)."""
        return self._http.put(f"/payments/{{payment_id}}/sign", dict(params))

    # ── Authorize ────────────────────────────────────────────────────────

    def authorize_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Prepare the unsigned authorize() transaction. Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/authorize/prepare")

    def authorize(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed authorize transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/authorize", dict(params))

    # ── Charge ───────────────────────────────────────────────────────────

    def charge_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Prepare the unsigned charge() transaction (one-shot, no escrow). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/charge/prepare")

    def charge(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed charge transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/charge", dict(params))

    # ── Capture ──────────────────────────────────────────────────────────

    def capture_prepare(self, payment_id: str, params: CapturePaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned capture() transaction. Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/capture/prepare", dict(params))

    def capture(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed capture transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/capture", dict(params))

    # ── Void ─────────────────────────────────────────────────────────────

    def void_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Build the unsigned void() transaction. Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/void/prepare")

    def void(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed void transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/void", dict(params))

    # ── Release ──────────────────────────────────────────────────────────

    def release_prepare(self, payment_id: str, params: Optional[ReleaseRequest] = None) -> PrepareTransactionResponse:
        """Build the unsigned release() transaction."""
        return self._http.post(f"/payments/{{payment_id}}/release/prepare", dict(params) if params else None)

    def release(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed release transaction (HTTP 202, async)."""
        return self._http.post(f"/payments/{{payment_id}}/release", dict(params))

    # ── Refund (EIP-3009) ────────────────────────────────────────────────

    def refund_prepare(self, payment_id: str, amount: str, *, v: Optional[int] = None, r: Optional[str] = None, s: Optional[str] = None) -> PrepareTransactionResponse:
        """Two-phase EIP-3009 refund flow.

        Phase 1 — pass only amount: returns a signing payload.
        Phase 2 — pass amount + v, r, s: returns unsigned refund transaction.
        """
        params: Dict[str, Any] = {{"amount": amount}}
        if v is not None:
            params["v"] = v
        if r is not None:
            params["r"] = r
        if s is not None:
            params["s"] = s
        return self._http.post(f"/payments/{{payment_id}}/refund/prepare", params)

    def refund(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed refund transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{{payment_id}}/refund", dict(params))
'''
    output_path.write_text(content)
    print(f"Generated {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        print("Set RAIL0_SCHEMA_PATH to override the default location.", file=sys.stderr)
        sys.exit(1)

    with SCHEMA_PATH.open() as f:
        spec = json.load(f)

    schemas: Dict[str, Any] = spec["components"]["schemas"]

    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    generate_types(schemas, RESOURCES_DIR / "types.py")
    generate_chains(RESOURCES_DIR / "chains.py")
    generate_tokens(RESOURCES_DIR / "tokens.py")
    generate_accounts(RESOURCES_DIR / "accounts.py")
    generate_payments(RESOURCES_DIR / "payments.py")

    print(f"Schema source: {SCHEMA_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()
