"""Tests for Rail0Client and HttpClient."""

import pytest
import respx
import httpx

from rail0 import Rail0Client, Rail0ApiError, debug_logger

BASE_URL = "https://api.rail0.xyz"

PAYMENT_ID = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

PAYMENT = {
    "payer": "0xBuyerAddress000000000000000000000000000000",
    "payee": "0xMerchantAddress0000000000000000000000000000",
    "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "maxAmount": "100000000",
    "authorizationExpiry": 9999999999,
    "refundExpiry": 9999999999,
    "feeBps": 50,
    "feeReceiver": "0xFeeReceiverAddress000000000000000000000000",
}

PAYMENT_RESPONSE = {
    "paymentId": PAYMENT_ID,
    "state": {
        "exists": True,
        "capturableAmount": "50000000",
        "refundableAmount": "0",
    },
    "configHash": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
}

TX_RESPONSE = {
    "transactionHash": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    "status": "pending",
}


# ================================================================
#  payments.get
# ================================================================


@respx.mock
def test_payments_get():
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(
        return_value=httpx.Response(200, json=PAYMENT_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.get(PAYMENT_ID)
    assert result["paymentId"] == PAYMENT_ID
    assert result["state"]["exists"] is True
    assert result["state"]["capturableAmount"] == "50000000"


# ================================================================
#  payments.authorize
# ================================================================


@respx.mock
def test_payments_authorize():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/authorize").mock(
        return_value=httpx.Response(202, json=TX_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.authorize(PAYMENT_ID, {
        "payment": PAYMENT,
        "amount": "50000000",
        "v": 27,
        "r": "0x1111111111111111111111111111111111111111111111111111111111111111",
        "s": "0x2222222222222222222222222222222222222222222222222222222222222222",
    })
    assert result["status"] == "pending"


# ================================================================
#  payments.capture
# ================================================================


@respx.mock
def test_payments_capture():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/capture").mock(
        return_value=httpx.Response(202, json=TX_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.capture(PAYMENT_ID, {"payment": PAYMENT, "amount": "50000000"})
    assert result["transactionHash"] == TX_RESPONSE["transactionHash"]


# ================================================================
#  payments.void
# ================================================================


@respx.mock
def test_payments_void():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/void").mock(
        return_value=httpx.Response(202, json=TX_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.void(PAYMENT_ID, {"payment": PAYMENT})
    assert result["status"] == "pending"


# ================================================================
#  payments.release
# ================================================================


@respx.mock
def test_payments_release():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/release").mock(
        return_value=httpx.Response(202, json=TX_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.release(PAYMENT_ID, {"payment": PAYMENT})
    assert result["status"] == "pending"


# ================================================================
#  payments.refund
# ================================================================


@respx.mock
def test_payments_refund():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/refund").mock(
        return_value=httpx.Response(202, json=TX_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.refund(PAYMENT_ID, {"payment": PAYMENT, "amount": "10000000"})
    assert result["status"] == "pending"


# ================================================================
#  payments.authorize_nonce / charge_nonce
# ================================================================


@respx.mock
def test_payments_authorize_nonce():
    nonce = "0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccdddd"
    config_hash = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}/authorize-nonce?configHash={config_hash}").mock(
        return_value=httpx.Response(200, json={"nonce": nonce})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.authorize_nonce(PAYMENT_ID, config_hash)
    assert result["nonce"] == nonce


@respx.mock
def test_payments_charge_nonce():
    nonce = "0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccdddd"
    config_hash = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}/charge-nonce?configHash={config_hash}").mock(
        return_value=httpx.Response(200, json={"nonce": nonce})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.charge_nonce(PAYMENT_ID, config_hash)
    assert result["nonce"] == nonce


# ================================================================
#  payments.hash
# ================================================================


@respx.mock
def test_payments_hash():
    config_hash = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    respx.post(f"{BASE_URL}/payments/hash").mock(
        return_value=httpx.Response(200, json={"hash": config_hash})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.payments.hash(PAYMENT)
    assert result["hash"] == config_hash


# ================================================================
#  tokens.is_accepted
# ================================================================


@respx.mock
def test_tokens_is_accepted():
    address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    respx.get(f"{BASE_URL}/tokens/{address}").mock(
        return_value=httpx.Response(200, json={"address": address, "accepted": True})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.tokens.is_accepted(address)
    assert result["accepted"] is True


# ================================================================
#  utils.domain_separator / version
# ================================================================


@respx.mock
def test_utils_domain_separator():
    ds = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    respx.get(f"{BASE_URL}/domain-separator").mock(
        return_value=httpx.Response(200, json={"domainSeparator": ds})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.utils.domain_separator()
    assert result["domainSeparator"] == ds


@respx.mock
def test_utils_version():
    respx.get(f"{BASE_URL}/version").mock(
        return_value=httpx.Response(200, json={"version": 6})
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.utils.version()
    assert result["version"] == 6


# ================================================================
#  Error handling
# ================================================================


@respx.mock
def test_raises_rail0_api_error_on_404():
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(
        return_value=httpx.Response(
            404,
            json={"error": "PaymentNotFound", "message": "No payment exists for the given paymentId."},
        )
    )
    client = Rail0Client(base_url=BASE_URL)
    with pytest.raises(Rail0ApiError) as exc_info:
        client.payments.get(PAYMENT_ID)
    err = exc_info.value
    assert err.status == 404
    assert err.error == "PaymentNotFound"
    assert "No payment exists" in str(err)


@respx.mock
def test_raises_rail0_api_error_on_409():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/authorize").mock(
        return_value=httpx.Response(
            409,
            json={"error": "PaymentAlreadyExists", "message": "Payment already exists."},
        )
    )
    client = Rail0Client(base_url=BASE_URL)
    with pytest.raises(Rail0ApiError) as exc_info:
        client.payments.authorize(PAYMENT_ID, {
            "payment": PAYMENT,
            "amount": "50000000",
            "v": 27,
            "r": "0x" + "11" * 32,
            "s": "0x" + "22" * 32,
        })
    assert exc_info.value.status == 409
    assert exc_info.value.error == "PaymentAlreadyExists"


@respx.mock
def test_raises_rail0_api_error_on_422():
    respx.post(f"{BASE_URL}/payments/{PAYMENT_ID}/capture").mock(
        return_value=httpx.Response(
            422,
            json={"error": "AuthorizationExpired", "message": "The authorizationExpiry timestamp has passed."},
        )
    )
    client = Rail0Client(base_url=BASE_URL)
    with pytest.raises(Rail0ApiError) as exc_info:
        client.payments.capture(PAYMENT_ID, {"payment": PAYMENT, "amount": "50000000"})
    assert exc_info.value.status == 422
    assert exc_info.value.error == "AuthorizationExpired"


# ================================================================
#  Logging
# ================================================================


@respx.mock
def test_debug_logger_is_called(capsys):
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(
        return_value=httpx.Response(200, json=PAYMENT_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL, logger=debug_logger)
    client.payments.get(PAYMENT_ID)
    captured = capsys.readouterr()
    assert "[rail0]" in captured.out
    assert "GET" in captured.out
    assert "200" in captured.out


@respx.mock
def test_custom_logger_receives_log_entry():
    log_entries = []
    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(
        return_value=httpx.Response(200, json=PAYMENT_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL, logger=log_entries.append)
    client.payments.get(PAYMENT_ID)
    assert len(log_entries) == 1
    entry = log_entries[0]
    assert entry.method == "GET"
    assert entry.status == 200
    assert entry.error is None


# ================================================================
#  Retry
# ================================================================


@respx.mock
def test_retries_on_network_error():
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.NetworkError("connection refused")
        return httpx.Response(200, json=PAYMENT_RESPONSE)

    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(side_effect=side_effect)
    client = Rail0Client(base_url=BASE_URL, max_retries=2, retry_delay=0.0)
    result = client.payments.get(PAYMENT_ID)
    assert result["paymentId"] == PAYMENT_ID
    assert call_count == 3


@respx.mock
def test_does_not_retry_http_errors():
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(404, json={"error": "PaymentNotFound", "message": "Not found."})

    respx.get(f"{BASE_URL}/payments/{PAYMENT_ID}").mock(side_effect=side_effect)
    client = Rail0Client(base_url=BASE_URL, max_retries=2, retry_delay=0.0)
    with pytest.raises(Rail0ApiError):
        client.payments.get(PAYMENT_ID)
    assert call_count == 1  # no retry for HTTP errors
