"""Refund a previously captured payment.

After capture, the merchant holds the funds in their wallet.
The merchant can refund them before refundExpiry.

On-chain flow:
  merchant → refund()   funds move merchant → buyer
"""

import time

from rail0 import Rail0ApiError, Rail0Client

client = Rail0Client(base_url="https://api.rail0.xyz")

PAYMENT_ID = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

now = int(time.time())

payment = {
    "payer": "0xBuyerAddress000000000000000000000000000000",
    "payee": "0xMerchantAddress0000000000000000000000000000",
    "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "maxAmount": "100000000",
    "authorizationExpiry": now + 60 * 60 * 24,
    "refundExpiry": now + 60 * 60 * 24 * 7,
    "feeBps": 50,
    "feeReceiver": "0xFeeReceiverAddress000000000000000000000000",
}

# Check current state before refunding
state = client.payments.get(PAYMENT_ID)
print(f"Refundable: {state['state']['refundableAmount']}")

try:
    refund_tx = client.payments.refund(PAYMENT_ID, {
        "payment": payment,
        "amount": "50000000",  # full refund of 50 USDC
    })
    print(f"Refunded: {refund_tx['transactionHash']} — status: {refund_tx['status']}")
except Rail0ApiError as err:
    # Common errors: RefundExpired, InvalidRefundAmount, PaymentMismatch
    print(f"Refund failed [{err.error}]: {err}")
    raise
