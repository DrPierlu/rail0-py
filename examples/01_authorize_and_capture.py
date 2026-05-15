"""Standard two-step payment flow: authorize → capture

The buyer locks funds in escrow using an EIP-3009 signature (authorize).
The merchant releases them once the order is fulfilled (capture).
If something goes wrong before capture the merchant can void,
or anyone can call release after authorizationExpiry.

On-chain flow:
  buyer signs EIP-3009 → authorize()   funds move buyer → escrow
  merchant             → capture()     funds move escrow → merchant (minus fee)
  merchant             → void()        alternative: funds move escrow → buyer
  anyone               → release()     fallback after authorizationExpiry
"""

import time

from rail0 import Rail0ApiError, Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

# ----------------------------------------------------------------
# Shared payment configuration
# A unique ID for this payment — in practice derive it from your
# order ID, e.g. keccak256(abi.encode("order", orderId)).
# ----------------------------------------------------------------

PAYMENT_ID = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

now = int(time.time())

payment = {
    "payer": "0xBuyerAddress000000000000000000000000000000",
    "payee": "0xMerchantAddress0000000000000000000000000000",
    "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
    "maxAmount": "100000000",  # 100 USDC (6 decimals)
    "authorizationExpiry": now + 60 * 60 * 24,    # merchant has 24 h to capture
    "refundExpiry": now + 60 * 60 * 24 * 7,       # refund window: 7 days
    "feeBps": 50,                                  # 0.5% protocol fee
    "feeReceiver": "0xFeeReceiverAddress000000000000000000000000",
}

# ----------------------------------------------------------------
# Step 1 — Buyer fetches the authorize nonce, signs EIP-3009, calls authorize
# ----------------------------------------------------------------

# Fetch the nonce the EIP-3009 signature must use.
nonce_response = client.payments.authorize_nonce(PAYMENT_ID, payment["payer"])
nonce = nonce_response["nonce"]

# The buyer builds and signs transferWithAuthorization off-chain:
#
#   from rail0.signing import sign_authorize, SignPaymentParams, TokenDomain
#
#   sig = sign_authorize(SignPaymentParams(
#       private_key="0x...",
#       payment=payment,
#       amount=50_000_000,
#       nonce=nonce,
#       contract_address=RAIL0_CONTRACT_ADDRESS,
#       token_domain=TokenDomain(
#           name="USD Coin",
#           version="2",
#           chain_id=8453,
#           verifying_contract=payment["token"],
#       ),
#   ))

try:
    auth_tx = client.payments.authorize(PAYMENT_ID, {
        "payment": payment,
        "amount": "50000000",  # 50 USDC
        "v": 27,               # from signature
        "r": "0x1111111111111111111111111111111111111111111111111111111111111111",
        "s": "0x2222222222222222222222222222222222222222222222222222222222222222",
    })
    print(f"Authorized: {auth_tx['transactionHash']} — status: {auth_tx['status']}")
    print(f"Nonce used: {nonce}")
except Rail0ApiError as err:
    # Common errors: TokenNotAccepted, InvalidAmount, PaymentAlreadyExists
    print(f"Authorize failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 2a — Merchant captures 50 USDC (happy path)
# ----------------------------------------------------------------

try:
    capture_tx = client.payments.capture(PAYMENT_ID, {
        "payment": payment,
        "amount": "50000000",
    })
    print(f"Captured: {capture_tx['transactionHash']}")
except Rail0ApiError as err:
    # Common errors: AuthorizationExpired, InvalidCaptureAmount, PaymentMismatch
    print(f"Capture failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 2b — Merchant voids (alternative: order cancelled)
# Uncomment to use instead of capture.
# ----------------------------------------------------------------

# void_tx = client.payments.void(PAYMENT_ID, {"payment": payment})
# print(f"Voided: {void_tx['transactionHash']}")

# ----------------------------------------------------------------
# Step 2c — Release (fallback: merchant never captured)
# Only callable after authorizationExpiry. Anyone can call this.
# ----------------------------------------------------------------

# release_tx = client.payments.release(PAYMENT_ID, {"payment": payment})
# print(f"Released: {release_tx['transactionHash']}")

# ----------------------------------------------------------------
# Inspect on-chain state at any point
# ----------------------------------------------------------------

state = client.payments.get(PAYMENT_ID)
print(f"Payment state: {state['state']}")
# {"exists": True, "capturableAmount": "0", "refundableAmount": "50000000"}
