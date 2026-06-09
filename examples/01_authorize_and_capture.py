"""Standard two-step payment flow: authorize → capture

The buyer locks funds in escrow using an EIP-3009 signature (authorize).
The merchant releases them once the order is fulfilled (capture).
If something goes wrong before capture the merchant can void,
or anyone can call release after authorization_expiry.

On-chain flow:
  buyer signs EIP-712  → authorize()   funds move buyer → escrow
  merchant             → capture()     funds move escrow → merchant (minus fee)
  merchant             → void()        alternative: funds move escrow → buyer
  anyone               → release()     fallback after authorization_expiry
"""

from rail0 import Rail0ApiError, Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

# ----------------------------------------------------------------
# Step 1 — Payer creates a payment intent and receives the EIP-712 payload
# ----------------------------------------------------------------

try:
    create_resp = client.payments.create({
        "chain_id": 8453,          # Base
        "mode": "authorize",
        "amount": "50000000",      # 50 USDC (6 decimals)
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        "payer": "0xBuyerAddress000000000000000000000000000000",
        "payee": "0xMerchantAddress0000000000000000000000000000",
    })
    payment_id = create_resp["rail0_id"]
    print(f"Payment ID: {payment_id}")
    print(f"Config hash: {create_resp['config_hash']}")
except Rail0ApiError as err:
    print(f"create failed [{err.error}]: {err}")
    raise

# The payer signs create_resp["signing_payload"] using eth_signTypedData_v4:
#
#   from rail0.signing import sign_authorize, SignPaymentParams, TokenDomain
#   sig = sign_authorize(SignPaymentParams(
#       private_key="0x...",
#       payer=create_resp["payment"]["payer"],
#       payee=create_resp["payment"]["payee"],
#       token=create_resp["payment"]["token"],
#       amount=create_resp["payment"]["amount"],
#       nonce=create_resp["signing_payload"]["message"]["nonce"],
#       contract_address=create_resp["rail0_contract"],
#       token_domain=TokenDomain(
#           name=create_resp["signing_payload"]["domain"]["name"],
#           version=create_resp["signing_payload"]["domain"]["version"],
#           chain_id=create_resp["signing_payload"]["domain"]["chainId"],
#           verifying_contract=create_resp["signing_payload"]["domain"]["verifyingContract"],
#       ),
#   ))

# ----------------------------------------------------------------
# Step 2 — Payer submits the EIP-712 signature
# ----------------------------------------------------------------

try:
    sig_resp = client.payments.sign(payment_id, {
        "signature": "0x111...222",  # 65-byte hex signature from the payer's wallet
    })
    print(f"Signature status: {sig_resp['status']}")
except Rail0ApiError as err:
    print(f"sign failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 3 — Payee gets the unsigned authorize transaction, signs and submits
# ----------------------------------------------------------------

try:
    prep_authorize = client.payments.authorize_prepare(payment_id)
    print(f"Unsigned authorize tx: {prep_authorize['unsigned_transaction'][:20]}...")

    # Payee signs prep_authorize["unsigned_transaction"] offline, then submits:
    #   signed_auth_tx = payee_wallet.sign_transaction(prep_authorize["unsigned_transaction"])
    signed_auth_tx = "0x02f8..."  # placeholder

    auth_resp = client.payments.authorize(payment_id, {
        "signed_transaction": signed_auth_tx,
    })
    print(f"Authorized: {auth_resp['rail0_id']} — status: {auth_resp['status']}")
except Rail0ApiError as err:
    print(f"authorize failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 4a — Payee prepares and submits a capture transaction
# ----------------------------------------------------------------

try:
    prep_capture = client.payments.capture_prepare(payment_id, {"amount": "50000000"})

    # Payee signs prep_capture["unsigned_transaction"] offline, then submits:
    #   signed_tx = payee_wallet.sign_transaction(prep_capture["unsigned_transaction"])
    signed_tx = "0x02f8..."  # placeholder

    capture_resp = client.payments.capture(payment_id, {
        "signed_transaction": signed_tx,
    })
    print(f"Captured: {capture_resp['rail0_id']} — status: {capture_resp['status']}")
except Rail0ApiError as err:
    print(f"capture failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 4b — Alternatively: payee voids (order cancelled)
# Uncomment to use instead of capture.
# ----------------------------------------------------------------

# prep_void = client.payments.void_prepare(payment_id)
# signed_void = payee_wallet.sign_transaction(prep_void["unsigned_transaction"])
# client.payments.void(payment_id, {"signed_transaction": signed_void})

# ----------------------------------------------------------------
# Step 4c — Release (fallback: merchant never captured)
# Only callable after authorization_expiry. Anyone can call this.
# ----------------------------------------------------------------

# prep_release = client.payments.release_prepare(payment_id)
# signed_release = payer_wallet.sign_transaction(prep_release["unsigned_transaction"])
# client.payments.release(payment_id, {"signed_transaction": signed_release})
