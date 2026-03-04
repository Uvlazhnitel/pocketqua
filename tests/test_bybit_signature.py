import hashlib
import hmac

from app.integrations.bybit.client import BybitClient


def test_bybit_signature_matches_hmac_sha256():
    client = BybitClient(base_url="https://api.bybit.com", api_key="key", api_secret="secret", recv_window=5000)
    timestamp = "1700000000000"
    query_string = "a=1&b=2"

    expected = hmac.new(
        b"secret",
        f"{timestamp}key5000{query_string}".encode(),
        hashlib.sha256,
    ).hexdigest()

    assert client._sign(timestamp, query_string) == expected
