"""Refund a previously captured payment.

After capture, the merchant holds the funds in their wallet.
The merchant can refund them before refund_expiry.

On-chain flow:
  merchant → refund()   funds move merchant → buyer
"""

from rail0 import Rail0ApiError, Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

PAYMENT_ID = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

# Check current state before refunding
state = client.payments.get(PAYMENT_ID)
print(f"Refundable: {state.get('on_chain', {}).get('refundableAmount', 'unknown')}")

# ----------------------------------------------------------------
# Phase 1 — Get the EIP-3009 signing payload for the refund
# ----------------------------------------------------------------

try:
    phase1 = client.payments.refund_prepare(PAYMENT_ID, amount="50000000")
    print("Phase 1 — sign this payload off-chain:")
    print(f"  signing_payload nonce: {phase1.get('signing_payload', {}).get('message', {}).get('nonce', '')}")
except Rail0ApiError as err:
    print(f"refund_prepare phase 1 failed [{err.error}]: {err}")
    raise

# Payee signs the EIP-3009 payload off-chain:
#
#   from rail0.signing import sign_transfer_with_authorization, SignTransferParams
#   sig = sign_transfer_with_authorization(SignTransferParams(
#       private_key="0x...",
#       from_=state["payee"],
#       to=state["rail0_contract"],
#       value=50_000_000,
#       nonce=phase1["signing_payload"]["message"]["nonce"],
#       ...
#   ))

# ----------------------------------------------------------------
# Phase 2 — Get the unsigned refund transaction
# ----------------------------------------------------------------

try:
    phase2 = client.payments.refund_prepare(
        PAYMENT_ID,
        amount="50000000",
        signature="0x111...222",  # 65-byte hex signature from phase 1
    )
    print("Phase 2 — unsigned refund tx ready for signing")

    # Payee signs phase2["unsigned_transaction"] offline, then submits:
    #   signed_refund = payee_wallet.sign_transaction(phase2["unsigned_transaction"])
    signed_refund = "0x02f8..."  # placeholder

    refund_resp = client.payments.refund(PAYMENT_ID, {
        "signed_transaction": signed_refund,
    })
    print(f"Refunded: {refund_resp['rail0_id']} — status: {refund_resp['status']}")
except Rail0ApiError as err:
    print(f"refund failed [{err.error}]: {err}")
    raise
