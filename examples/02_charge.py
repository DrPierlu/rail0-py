"""One-shot payment: charge (authorize + capture in a single transaction)

Funds go directly to the payee with no hold period.
Use this when the merchant can fulfil the order immediately.

On-chain flow:
  buyer signs EIP-712 → charge()   funds move buyer → merchant (minus fee)
"""

from rail0 import Rail0ApiError, Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

# ----------------------------------------------------------------
# Step 1 — Payer creates a payment intent (mode = "charge")
# ----------------------------------------------------------------

try:
    create_resp = client.payments.create({
        "chain_id": 8453,          # Base
        "mode": "charge",
        "amount": "25000000",      # 25 USDC (6 decimals)
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        "payer": "0xBuyerAddress000000000000000000000000000000",
        "payee": "0xMerchantAddress0000000000000000000000000000",
    })
    payment_id = create_resp["rail0_id"]
    print(f"Payment ID: {payment_id}")
except Rail0ApiError as err:
    print(f"create failed [{err.error}]: {err}")
    raise

# The payer signs create_resp["signing_payload"] using eth_signTypedData_v4:
#
#   from rail0.signing import sign_charge, SignPaymentParams, TokenDomain
#   sig = sign_charge(SignPaymentParams(
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
    client.payments.sign(payment_id, {
        "signature": "0x111...222",  # 65-byte hex signature from the payer's wallet
    })
except Rail0ApiError as err:
    print(f"sign failed [{err.error}]: {err}")
    raise

# ----------------------------------------------------------------
# Step 3 — Payee gets the unsigned charge transaction, signs and submits
# ----------------------------------------------------------------

try:
    prep_charge = client.payments.charge_prepare(payment_id)
    print(f"Unsigned charge tx: {prep_charge['unsigned_transaction'][:20]}...")

    # Payee signs prep_charge["unsigned_transaction"] offline, then submits:
    #   signed_tx = payee_wallet.sign_transaction(prep_charge["unsigned_transaction"])
    signed_tx = "0x02f8..."  # placeholder

    tx = client.payments.charge(payment_id, {
        "signed_transaction": signed_tx,
    })
    print(f"Charged: {tx['rail0_id']} — status: {tx['status']}")
except Rail0ApiError as err:
    print(f"charge failed [{err.error}]: {err}")
    raise
