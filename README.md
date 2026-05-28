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

# Step 5 — payee prepares the unsigned authorize tx
tx = client.payments.authorize(payment_id)
# sign tx["unsignedTransaction"] with payee's key (EIP-1559)

# Step 6 — broadcast signed authorize tx
client.payments.submit_transaction(payment_id, {"signedTransaction": signed_bytes})

# Step 7 — payee captures the funds
capture_tx = client.payments.prepare_capture(payment_id, {"amount": "50000000"})
client.payments.submit_transaction(payment_id, {"signedTransaction": sign(capture_tx)})
```

## Payment lifecycle

```text
                            authorizationExpiry       refundExpiry
                                   │                       │
  ─────────────────────────────────┼───────────────────────┼──────▶ time
   create → sign → authorize       │   capture / void       │   approve+refund
                                    │   release              │
```

| Operation | Caller | What it does |
|-----------|--------|--------------|
| `authorize` + `submit_transaction` | payee | Prepare + broadcast the authorize tx; funds move to escrow |
| `charge` | payee | Server-side one-shot: authorize + capture with no escrow window |
| `prepare_capture` + `submit_transaction` | payee | Moves escrowed funds to the merchant |
| `prepare_void` + `submit_transaction` | payee | Cancels the hold, returns funds to the payer |
| `prepare_release` + `submit_transaction` | anyone | Reclaims escrow after `authorizationExpiry` |
| `prepare_approve` + `submit_transaction` | payee | ERC-20 `approve()` required before a refund |
| `prepare_refund` + `submit_transaction` | payee | Returns captured funds to the payer |

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

#### `.authorize(payment_id)` → `dict`

Prepares the unsigned `authorize()` transaction. Called by the payee. Sign `unsignedTransaction` and pass to `submit_transaction`.

#### `.submit_transaction(payment_id, params)` → HTTP 202

Broadcasts a signed transaction for any operation (async). Body: `{ signedTransaction: '0x...' }`. Returns HTTP 202. Poll `.get()` until status leaves `'submitting'`.

```python
tx = client.payments.authorize(payment_id)
client.payments.submit_transaction(payment_id, {"signedTransaction": signed_bytes})
```

#### `.charge(payment_id)` → `dict`

Server-side one-shot: authorize + capture in a single transaction. No `submit` step. Called by the payee.

#### `.prepare_capture(payment_id, params)`

Build the capture transaction. Partial captures are supported.

```python
tx = client.payments.prepare_capture(payment_id, {"amount": "50000000"})
client.payments.submit_transaction(payment_id, {"signedTransaction": signed})
```

#### `.prepare_void(payment_id)`

Void the authorization — releases all escrowed funds to the payer.

#### `.prepare_release(payment_id, params?)`

Release escrowed funds after `authorizationExpiry`. Pass `{"callerAddress": addr}` for buyer-initiated release.

```python
tx = client.payments.prepare_release(payment_id, {"callerAddress": buyer_addr})
client.payments.submit_transaction(payment_id, {"signedTransaction": buyer_signed})
```

#### `.prepare_approve(payment_id, params)`

ERC-20 `approve()` before a refund.

```python
tx = client.payments.prepare_approve(payment_id, {"amount": "50000000"})
client.payments.submit_transaction(payment_id, {"signedTransaction": signed})
```

#### `.prepare_refund(payment_id, params)`

Build the refund transaction. Partial refunds are supported.

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
    client.payments.submit_transaction(payment_id, {"signedTransaction": signed})
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
