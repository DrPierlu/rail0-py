# rail0

Python SDK for the [RAIL0](https://github.com/your-org/rail0) stablecoin payment API.

RAIL0 is an immutable smart contract that brings the authorize → capture → refund lifecycle of card networks to stablecoin payments — no intermediaries, no protocol fee, no permission required. This SDK wraps the REST API that sits in front of the contract, giving you fully-typed access to every operation from any Python environment.

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

import time
now = int(time.time())

payment = {
    "payer":               "0xBuyer...",
    "payee":               "0xMerchant...",
    "token":               "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
    "maxAmount":           "100000000",   # 100 USDC (6 decimals)
    "authorizationExpiry": now + 3600 * 24,     # 24 h to capture
    "refundExpiry":        now + 3600 * 24 * 7, # 7-day refund window
    "feeBps":              50,                  # 0.5% protocol fee
    "feeReceiver":         "0xFeeReceiver...",
}

payment_id = "0xabc..."  # your unique identifier for this payment

# Step 1 — buyer locks funds in escrow (v/r/s from off-chain EIP-3009 signature)
auth_tx = client.payments.authorize(payment_id, {
    "payment": payment,
    "amount": "50000000",  # 50 USDC
    "v": 27,
    "r": "0x...",
    "s": "0x...",
})

# Step 2 — merchant releases them
capture_tx = client.payments.capture(payment_id, {
    "payment": payment,
    "amount": "50000000",
})
```

## Payment lifecycle

```text
                 authorizationExpiry    refundExpiry
                        │                   │
 ───────────────────────┼───────────────────┼────▶ time
  authorize / charge     │   capture / void   │   refund
                         │   release          │
```

| Operation   | Caller | What it does                                    |
|-------------|--------|-------------------------------------------------|
| `authorize` | payer  | Locks `amount` in escrow                        |
| `charge`    | payer  | Authorize + capture in one transaction          |
| `capture`   | payee  | Moves escrowed funds to the merchant            |
| `void`      | payee  | Cancels the hold, returns funds to the buyer    |
| `release`   | anyone | Reclaims escrow after `authorizationExpiry`     |
| `refund`    | payee  | Returns captured funds back to the buyer        |

## API reference

### `Rail0Client(base_url, **options)`

```python
from rail0 import Rail0Client, debug_logger

client = Rail0Client(
    base_url="https://api.rail0.xyz",
    headers={"Authorization": "Bearer ..."},  # optional
    timeout=30.0,                              # seconds, default 30
    max_retries=3,                             # optional, default 0 (no retry)
    retry_delay=0.2,                           # seconds base delay, doubles each attempt
    logger=debug_logger,                       # optional — see Logging
)
```

---

### Logging

Pass any callable matching `(entry: LogEntry) -> None` as `logger` to receive structured log entries for every request.

```python
from rail0 import Rail0Client, debug_logger

# Built-in logger — writes to stdout
client = Rail0Client(base_url="https://api.rail0.xyz", logger=debug_logger)
```

Output format:

```text
[rail0] POST 202 https://api.rail0.xyz/payments/0x.../authorize 87ms → { ... } ← { ... }
[rail0] ERROR GET https://api.rail0.xyz/payments/0x... 30001ms ! TimeoutException
```

To integrate with an existing logger:

```python
import logging
from rail0 import LogEntry

log = logging.getLogger("rail0")

client = Rail0Client(
    base_url="https://api.rail0.xyz",
    logger=lambda entry: (
        log.error("rail0 request failed", extra={"entry": entry})
        if entry.error
        else log.debug("rail0 request", extra={"entry": entry})
    ),
)
```

`LogEntry` fields:

| Field          | Type              | Present                         |
|----------------|-------------------|---------------------------------|
| `method`       | `str`             | always                          |
| `url`          | `str`             | always                          |
| `duration_ms`  | `float`           | always                          |
| `request_body` | `Any`             | POST requests                   |
| `status`       | `int \| None`     | when a response was received    |
| `response_body`| `Any`             | when a response was received    |
| `error`        | `Exception \| None` | on HTTP errors and network failures |
| `attempt`      | `int \| None`     | when `max_retries > 0`          |
| `will_retry`   | `bool \| None`    | when a retry is scheduled       |

---

### `client.payments`

#### `.get(payment_id)`

Returns the on-chain state and configuration hash for a payment.

```python
result = client.payments.get(payment_id)
# result["state"]: { "exists": bool, "capturableAmount": str, "refundableAmount": str }
```

#### `.authorize(payment_id, params)`

Locks `amount` from the buyer into escrow using an EIP-3009 signature.

```python
tx = client.payments.authorize(payment_id, {
    "payment": payment,
    "amount": "50000000",
    "v": 27,
    "r": "0x...",
    "s": "0x...",
})
```

#### `.charge(payment_id, params)`

Authorize and capture in one transaction. Same shape as `authorize`.

#### `.capture(payment_id, params)`

Moves escrowed funds to the merchant.

```python
tx = client.payments.capture(payment_id, {"payment": payment, "amount": "50000000"})
```

#### `.void(payment_id, params)`

Cancels an authorization and returns escrowed funds to the buyer.

```python
tx = client.payments.void(payment_id, {"payment": payment})
```

#### `.release(payment_id, params)`

Returns escrowed funds to the buyer after `authorizationExpiry`. Permissionless.

```python
tx = client.payments.release(payment_id, {"payment": payment})
```

#### `.refund(payment_id, params)`

Returns previously captured funds from the merchant to the buyer.

```python
tx = client.payments.refund(payment_id, {"payment": payment, "amount": "50000000"})
```

#### `.authorize_nonce(payment_id, payer)`

Returns the EIP-3009 nonce for an authorize signature.

```python
result = client.payments.authorize_nonce(payment_id, payment["payer"])
nonce = result["nonce"]
```

#### `.charge_nonce(payment_id, payer)`

Returns the EIP-3009 nonce for a charge signature.

#### `.hash(payment)`

Computes the EIP-712 digest of a Payment configuration.

```python
result = client.payments.hash(payment)
config_hash = result["hash"]
```

---

### `client.tokens`

#### `.is_accepted(address)`

Returns whether a token address is in this deployment's allowlist.

```python
result = client.tokens.is_accepted("0x833589...")
# result["accepted"]: bool
```

---

### `client.utils`

#### `.domain_separator()`

Returns the EIP-712 domain separator for the RAIL0 contract.

```python
result = client.utils.domain_separator()
domain_sep = result["domainSeparator"]
```

#### `.version()`

Returns the contract version number.

```python
result = client.utils.version()
# result["version"]: int
```

---

## Off-chain signing

Install `rail0[signing]` to use the signing utilities.

```python
from rail0 import Rail0Client
from rail0.signing import sign_authorize, sign_charge, SignPaymentParams, TokenDomain

token_domain = TokenDomain(
    name="USD Coin",
    version="2",
    chain_id=8453,  # Base
    verifying_contract=payment["token"],
)

# Fetch nonce
nonce = client.payments.authorize_nonce(payment_id, payment["payer"])["nonce"]

# Sign off-chain
sig = sign_authorize(SignPaymentParams(
    private_key="0x...",   # payer's private key
    payment=payment,
    amount=50_000_000,     # token base units
    nonce=nonce,
    contract_address="0x...",  # RAIL0 contract
    token_domain=token_domain,
))

# Submit
tx = client.payments.authorize(payment_id, {
    "payment": payment,
    "amount": "50000000",
    "v": sig.v,
    "r": sig.r,
    "s": sig.s,
})
```

---

## Error handling

Every 4xx / 5xx response is raised as `Rail0ApiError`:

```python
from rail0 import Rail0ApiError

try:
    client.payments.capture(payment_id, {"payment": payment, "amount": "50000000"})
except Rail0ApiError as err:
    print(err.status)   # HTTP status code, e.g. 422
    print(err.error)    # contract error name, e.g. "AuthorizationExpired"
    print(err)          # human-readable description
```

Common error codes:

| Error                   | Cause                                                       |
|-------------------------|-------------------------------------------------------------|
| `PaymentAlreadyExists`  | `authorize` / `charge` called twice with the same `paymentId` |
| `PaymentNotFound`       | `paymentId` does not exist                                  |
| `PaymentMismatch`       | `payment` config does not match the stored hash             |
| `AuthorizationExpired`  | `authorizationExpiry` is in the past (capture)              |
| `AuthorizationNotExpired` | `authorizationExpiry` has not passed yet (release)        |
| `RefundExpired`         | `refundExpiry` is in the past                               |
| `InvalidAmount`         | `amount` is 0 or exceeds `maxAmount`                        |
| `InvalidCaptureAmount`  | `amount` exceeds `capturableAmount`                         |
| `InvalidRefundAmount`   | `amount` exceeds `refundableAmount`                         |
| `TokenNotAccepted`      | token is not in this deployment's allowlist                 |

---

## Stablecoins reference

```python
from rail0 import stablecoins, eip3009_tokens

# All EIP-3009 tokens on Base
tokens = eip3009_tokens("base")
# [{"symbol": "USDC", "address": "0x833589...", "decimals": 6}]

# Direct lookup
usdc = stablecoins["base"].tokens["USDC"]
print(usdc.address, usdc.decimals, usdc.eip3009)
```

Supported chains: `ethereum`, `base`, `polygon`, `arbitrumOne`, `optimism`, `avalanche`, `celo`.

---

## Project structure

```text
gen/
  openapi.json      source of truth for the API surface

rail0/
  __init__.py       public re-exports
  client.py         Rail0Client — assembles the resources
  signing.py        EIP-712 / EIP-3009 off-chain signing (optional dep)
  stablecoins.py    hardcoded stablecoin addresses and helpers

  core/
    error.py        Rail0ApiError
    http.py         HttpClient (httpx, timeout, retry, logging)

  resources/
    types.py        TypedDict shapes from the OpenAPI schema
    payments.py     PaymentsResource
    tokens.py       TokensResource
    utils.py        UtilsResource

examples/
  01_authorize_and_capture.py
  02_charge.py
  03_refund.py

tests/
  test_client.py
  test_signing.py
  test_http.py
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy rail0

# Lint
ruff check rail0 tests
```

---

## License

[MIT](LICENSE)
