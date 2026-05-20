#!/usr/bin/env python3
"""
Code generator for rail0/resources/types.py.

Reads the OpenAPI schema from ../rail0-api/doc/openapi.json
(or the path in the RAIL0_SCHEMA_PATH env var) and writes
rail0/resources/types.py.

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

DEFAULT_SCHEMA_PATH = REPO_ROOT.parent / "rail0-api" / "doc" / "openapi.json"
SCHEMA_PATH = Path(os.environ.get("RAIL0_SCHEMA_PATH", str(DEFAULT_SCHEMA_PATH)))
OUTPUT_PATH = REPO_ROOT / "rail0" / "resources" / "types.py"

# ---------------------------------------------------------------------------
# Helpers
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
    "ApproveRequest",
    "RefundPaymentRequest",
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
    req_fields: List[Tuple[str, str, str]] = []   # (json_name, py_name, type_str)
    opt_fields: List[Tuple[str, str, str]] = []

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


def generate(schema_path: Path, output_path: Path) -> None:
    if not schema_path.exists():
        print(f"ERROR: schema not found at {schema_path}", file=sys.stderr)
        print("Set RAIL0_SCHEMA_PATH to override the default location.", file=sys.stderr)
        sys.exit(1)

    with schema_path.open() as f:
        spec = json.load(f)

    schemas: Dict[str, Any] = spec["components"]["schemas"]

    # Determine emit order: use EMIT_ORDER first, then any remaining schemas.
    ordered_names: List[str] = []
    for name in EMIT_ORDER:
        if name in schemas:
            ordered_names.append(name)
    for name in schemas:
        if name not in ordered_names:
            ordered_names.append(name)

    # ---------------------------------------------------------------------------
    # Build output
    # ---------------------------------------------------------------------------
    parts: List[str] = []

    # File header
    parts.append('''\
"""
Public types for the RAIL0 Python SDK.

All types mirror the OpenAPI schema in rail0-api/doc/openapi.json.
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
    # Group into logical sections matching the original file structure
    sections = [
        ("Core models", ["PaymentConfig", "PaymentInput", "EIP712Domain", "EIP3009Message", "SigningPayload"]),
        ("Request bodies", ["CreatePaymentRequest", "PayerSignatureRequest", "CapturePaymentRequest",
                            "SubmitTransactionRequest", "ApproveRequest", "RefundPaymentRequest"]),
        ("Response shapes", ["CreatePaymentResponse", "PayerSignatureResponse", "AuthorizePaymentResponse",
                              "ChargePaymentResponse", "PrepareTransactionResponse", "CapturePaymentResponse",
                              "VoidPaymentResponse", "ReleasePaymentResponse", "ApproveResponse",
                              "RefundPaymentResponse", "PaymentMethod", "Error"]),
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

    output = "".join(parts).rstrip("\n") + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(output)

    print(f"Generated {output_path}")
    print(f"  Schema source: {schema_path}")


if __name__ == "__main__":
    generate(SCHEMA_PATH, OUTPUT_PATH)
