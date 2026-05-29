# rail0

Python SDK for the [RAIL0](https://github.com/commercelayer/rail0) stablecoin payment API.

RAIL0 is an immutable smart contract that brings the authorize → capture → refund lifecycle of card networks to stablecoin payments — no intermediaries, no protocol fees, no permission required. This SDK wraps the REST API that sits in front of the contract, giving you fully-typed access to every operation from any Python environment.

## Requirements

- Python ≥ 3.11

## Installation

```bash
pip install rail0
```

For off-chain EIP-3009 signing support:

```bash
pip install rail0[signing]
```

## Quick start

```python
from rail0 import Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

# Step 1 — discover payment methods
methods = client.merchants.payment_methods(1)
usdc = next(m for m in methods if m["tokenSymbol"] == "USDC")

# Step 2 — create payment intent
resp = client.payments.create_payment({
    "payment": {
        "payer":  "0xBuyer...",
        "payee":  usdc["walletAddress"],
        "token":  usdc["tokenAddress"],
        "amount": "50000000",   # 50 USDC (6 decimals)
    },
    "chainId": usdc["chainId"],
    "mode": "authorize",
})
payment_id = resp["rail0_id"]

# Step 3 — payer signs EIP-3009 off-chain
from rail0.signing import sign_authorize, SignPaymentParams, TokenDomain

sig = sign_authorize(SignPaymentParams(
    private_key="0x...",
    payment=resp["payment"],
    amount=int(resp["payment"]["amount"]),
    nonce=resp["signingPayload"]["message"]["nonce"],
    contract_address=resp["rail0Contract"],
    token_domain=TokenDomain(
        name="USD Coin", version="2",
        chain_id=usdc["chainId"], verifying_contract=usdc["tokenAddress"],
    ),
))

# Step 4 — submit payer signature
client.payments.sign(payment_id, {"signature": sig.to_hex()})

# Step 5 — payee fetches the unsigned authorize tx (payload step)
tx = client.payments.authorize_payload(payment_id)
# sign tx["unsignedTransaction"] with payee's key (EIP-1559)

# Step 6 — broadcast signed authorize tx (async, HTTP 202)
client.payments.authorize(payment_id, {"signedTransaction": signed_bytes})

# Step 7 — payee captures the funds
capture_tx = client.payments.capture_payload(payment_id, {"amount": "50000000"})
client.payments.capture(payment_id, {"signedTransaction": sign(capture_tx)})
```

## Payment lifecycle

Each operation follows the same two-step pattern:

1. **Payload step** — `POST /payments/:id/operation/payload` — returns an unsigned EIP-1559 transaction. Sign it off-chain with the payee's key.
2. **Submit step** — `POST /payments/:id/operation` with `{"signedTransaction": "0x..."}` — broadcasts the signed tx (HTTP 202, async). Poll `get()` until status leaves `"submitting"`.

```text
                            authorizationExpiry       refundExpiry
                                   │                       │
  ─────────────────────────────────┼───────────────────────┼──────▶ time
   create → sign → authorize       │   capture / void       │   refund (EIP-3009)
                                    │   release              │
```

| Operation | Caller | What it does |
|-----------|--------|--------------|
| `authorize_payload` + `authorize` | payee | Prepare + broadcast the authorize tx; funds move to escrow |
| `charge_payload` + `charge` | payee | One-shot: authorize + capture with no escrow window |
| `capture_payload` + `capture` | payee | Moves escrowed funds to the merchant |
| `void_payload` + `void` | payee | Cancels the hold, returns funds to the payer |
| `release_payload` + `release` | anyone | Reclaims escrow after `authorizationExpiry` |
| `refund_payload` + `refund` | payee | EIP-3009 `receiveWithAuthorization` refund (no ERC-20 approve needed) |

## Contract addresses (v9)

| Network | Chain ID | Contract |
|---------|----------|----------|
| Arc Testnet | 5042002 | `0x0e393A626EfC45EBd030EBB997CDa207013C4364` |
| Celo Sepolia | 44787 | `0x7337ce441e831ef2904b7B2f33507d655a4381d0` |

## API reference

### `Rail0Client(base_url, **options)`

```python
from rail0 import Rail0Client, debug_logger

client = Rail0Client(
    base_url="https://api.rail0.xyz",
    headers={"Authorization": "Bearer ..."},  # optional
    timeout=30.0,                              # seconds, default 30
    max_retries=3,                             # default 0 (no retry)
    retry_delay=0.2,                           # seconds base delay, doubles each attempt
    logger=debug_logger,                       # optional — see Logging
)
```

---

### Logging

Pass any callable matching `(entry: LogEntry) -> None` as `logger`.

```python
from rail0 import Rail0Client, debug_logger

client = Rail0Client(base_url="https://api.rail0.xyz", logger=debug_logger)
```

Output:
```text
[rail0] POST 200 https://.../payments 87ms
[rail0] ERROR PUT https://.../payments/0x.../sign 30001ms ! TimeoutException
```

To integrate with an existing logger:

```python
import logging
log = logging.getLogger("rail0")

client = Rail0Client(
    base_url="https://api.rail0.xyz",
    logger=lambda e: (
        log.error("rail0 request failed", extra={"entry": e})
        if e.error else log.debug("rail0 request", extra={"entry": e})
    ),
)
```

---

### `client.merchants`

#### `.payment_methods(merchant_id)` → `list[dict]`

Returns the active payment methods (chain + token + wallet) for a merchant.

```python
methods = client.merchants.payment_methods(1)
# [{"chainId", "chainSlug", "tokenAddress", "tokenSymbol",
#   "tokenDecimals", "walletAddress", "isDefault", ...}]
```

---

### `client.payments`

All methods return a `dict`. Errors raise `Rail0ApiError`.

#### `.list()` → `list[dict]`

Lists payments for the authenticated account. Requires a bearer token.

#### `.get(payment_id)` → `dict`

Fetches the current payment state (DB status + live on-chain escrow balances).

```python
state = client.payments.get(payment_id)
# state["status"]                        → "authorized", "captured", …
# state["onChain"]["capturableAmount"]   → escrowed amount still available
# state["onChain"]["refundableAmount"]   → captured amount eligible for refund
```

#### `.create_payment(params)` → `dict`

Creates a payment intent. Returns `signingPayload` for the payer to sign, plus `rail0Contract`.

#### `.sign(payment_id, params)` → `dict`

Submits the payer's EIP-712 signature as a single unified hex string.

#### `.authorize_payload(payment_id)` → `dict`

Prepares the unsigned `authorize()` transaction. Called by the payee. Sign `unsignedTransaction` and pass to `authorize()`.

#### `.authorize(payment_id, params)` → `dict`

Broadcasts the signed authorize transaction (HTTP 202, async). Poll `.get()` until status leaves `'submitting'`.

```python
tx = client.payments.authorize_payload(payment_id)
# sign tx["unsignedTransaction"] with payee's key
client.payments.authorize(payment_id, {"signedTransaction": signed_bytes})
```

#### `.charge_payload(payment_id)` → `dict`

Prepares the unsigned charge transaction (one-shot authorize + capture, no escrow window).

#### `.charge(payment_id, params)` → `dict`

Broadcasts the signed charge transaction (HTTP 202, async).

#### `.capture_payload(payment_id, params)` → `dict`

Build the capture transaction. Partial captures are supported.

```python
tx = client.payments.capture_payload(payment_id, {"amount": "50000000"})
client.payments.capture(payment_id, {"signedTransaction": signed})
```

#### `.void_payload(payment_id)` → `dict`

Build the unsigned void transaction — releases all escrowed funds to the payer.

#### `.void(payment_id, params)` → `dict`

Broadcasts the signed void transaction (HTTP 202, async).

#### `.release_payload(payment_id, params?)` → `dict`

Build the unsigned release transaction for reclaiming escrow after `authorizationExpiry`. Pass `{"callerAddress": addr}` for buyer-initiated release.

```python
tx = client.payments.release_payload(payment_id, {"callerAddress": buyer_addr})
client.payments.release(payment_id, {"signedTransaction": buyer_signed})
```

#### `.refund_payload(payment_id, params)` → `dict`

Two-phase EIP-3009 `receiveWithAuthorization` refund payload. No ERC-20 approve step is required.

**Phase 1** — pass `{"amount": "..."}` only: returns the EIP-3009 signing payload. Sign off-chain to obtain `v`, `r`, `s`.

**Phase 2** — pass `{"amount": "...", "v": ..., "r": "...", "s": "..."}`: returns the unsigned on-chain refund transaction.

```python
# Phase 1 — get EIP-3009 signing payload
sig_payload = client.payments.refund_payload(payment_id, {"amount": "50000000"})
# sign sig_payload off-chain → v, r, s

# Phase 2 — get unsigned on-chain tx
tx = client.payments.refund_payload(payment_id, {"amount": "50000000", "v": v, "r": r, "s": s})
# sign tx["unsignedTransaction"] with payee's key
client.payments.refund(payment_id, {"signedTransaction": signed_bytes})
```

#### `.refund(payment_id, params)` → `dict`

Broadcasts the signed refund transaction (HTTP 202, async).

---

## Off-chain signing

Install `rail0[signing]` to use the signing utilities.

```python
from rail0.signing import sign_authorize, sign_charge, SignPaymentParams, TokenDomain

token_domain = TokenDomain(
    name="USD Coin", version="2",
    chain_id=84532,  # Base Sepolia
    verifying_contract=usdc["tokenAddress"],
)

sig = sign_authorize(SignPaymentParams(
    private_key="0x...",   # payer's private key
    payment=resp["payment"],
    amount=int(resp["payment"]["amount"]),
    nonce=resp["signingPayload"]["message"]["nonce"],
    contract_address=resp["rail0Contract"],
    token_domain=token_domain,
))

# sig.to_hex() — pass to client.payments.sign
```

Use `sign_charge` instead of `sign_authorize` when `mode: "charge"`.

---

## Error handling

Every 4xx / 5xx response is raised as `Rail0ApiError`:

```python
from rail0 import Rail0ApiError

try:
    client.payments.authorize(payment_id, {"signedTransaction": signed})
except Rail0ApiError as err:
    print(err.status)  # HTTP status code, e.g. 422
    print(err.error)   # contract error name, e.g. "AuthorizationExpired"
    print(str(err))    # human-readable description
```

Common error codes:

| Error | Cause |
|-------|-------|
| `PaymentAlreadyExists` | `authorize` / `charge` called twice with the same `paymentId` |
| `PaymentNotFound` | `paymentId` does not exist |
| `AuthorizationExpired` | `authorizationExpiry` is in the past (capture) |
| `AuthorizationNotExpired` | `authorizationExpiry` has not passed yet (release) |
| `RefundExpired` | `refundExpiry` is in the past |
| `InvalidAmount` | `amount` is 0 |
| `NotPayee` | caller is not `payment.payee` |

---

## Stablecoins reference

```python
from rail0 import stablecoins, eip3009_tokens

# All EIP-3009 tokens on Base
tokens = eip3009_tokens("base")
# [{"symbol": "USDC", "address": "0x833589...", "decimals": 6}]

# Chain metadata
chain = stablecoins["base"]
print(chain.chain_id)  # 8453
```

---

## Development

```bash
pip install -e ".[dev]"
pytest
mypy rail0
ruff check rail0 tests

# Regenerate rail0/resources/types.py after an API change:
# 1. Update the schema in rail0-api (sibling repo),
#    or set RAIL0_SCHEMA_PATH to point to a local file.
# 2. Regenerate:
python3 gen/generate.py
```

## Project structure

```text
gen/
  generate.py       regenerates rail0/resources/types.py from the schema

rail0/
  __init__.py       public re-exports
  client.py         Rail0Client — entry point
  signing.py        EIP-712 / EIP-3009 off-chain signing (optional dep)
  stablecoins.py    stablecoin address registry

  core/
    error.py        Rail0ApiError
    http.py         HttpClient (httpx, timeout, retry, logging)

  resources/
    types.py        TypedDict shapes
    merchants.py    MerchantsResource
    payments.py     PaymentsResource

tests/
  test_client.py
  test_signing.py
  test_http.py
```

---

## License

[MIT](LICENSE)
