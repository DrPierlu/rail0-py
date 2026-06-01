"""Tests for AuthResource and crypto helpers."""

import json

import pytest
import respx
import httpx

from rail0 import Rail0Client
from rail0.resources.auth import personal_sign, private_key_to_address

BASE_URL = "https://api.rail0.xyz"

HARDHAT_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
HARDHAT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

NONCE_RESPONSE = {
    "nonce": "test-nonce",
    "expires_at": "2099-01-01T00:00:00Z",
}

AUTH_RESPONSE = {
    "token": "jwt",
    "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2099-01-01T00:00:00Z",
}


# ================================================================
#  auth.get_nonce
# ================================================================


@respx.mock
def test_get_nonce():
    respx.post(f"{BASE_URL}/nonces").mock(
        return_value=httpx.Response(200, json=NONCE_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.auth.get_nonce()
    assert result["nonce"] == "test-nonce"
    assert result["expires_at"] == "2099-01-01T00:00:00Z"


# ================================================================
#  auth.verify
# ================================================================


@respx.mock
def test_verify():
    route = respx.post(f"{BASE_URL}/auth").mock(
        return_value=httpx.Response(200, json=AUTH_RESPONSE)
    )
    client = Rail0Client(base_url=BASE_URL)
    result = client.auth.verify(message="some message", signature="0x" + "ab" * 65)

    assert result["token"] == "jwt"
    assert result["address"] == HARDHAT_ADDRESS
    assert result["account_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert result["expires_at"] == "2099-01-01T00:00:00Z"

    # Verify the POST body contained message and signature
    sent_body = json.loads(route.calls[0].request.content)
    assert "message" in sent_body
    assert "signature" in sent_body


# ================================================================
#  auth.login (full flow)
# ================================================================


@respx.mock
def test_login_full_flow():
    respx.post(f"{BASE_URL}/nonces").mock(
        return_value=httpx.Response(200, json=NONCE_RESPONSE)
    )
    auth_route = respx.post(f"{BASE_URL}/auth").mock(
        return_value=httpx.Response(200, json=AUTH_RESPONSE)
    )

    client = Rail0Client(base_url=BASE_URL)
    result = client.auth.login(private_key_hex=HARDHAT_KEY, domain="api.rail0.xyz")

    assert result["token"] == "jwt"

    sent_body = json.loads(auth_route.calls[0].request.content)
    assert "message" in sent_body
    assert "signature" in sent_body

    message = sent_body["message"]
    assert HARDHAT_ADDRESS in message
    assert "Nonce: test-nonce" in message

    signature = sent_body["signature"]
    assert signature.startswith("0x")
    # 65 bytes = 130 hex chars + "0x" prefix = 132 chars total
    assert len(signature) == 132


# ================================================================
#  personal_sign — unit tests
# ================================================================


def test_personal_sign_length():
    sig = personal_sign(HARDHAT_KEY, "hello")
    assert sig.startswith("0x")
    # 65 bytes → 130 hex chars after the 0x prefix
    assert len(sig) == 132


def test_private_key_to_address():
    addr = private_key_to_address(HARDHAT_KEY)
    assert addr == HARDHAT_ADDRESS
