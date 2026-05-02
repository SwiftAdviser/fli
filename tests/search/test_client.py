from fli.search.client import Client


def test_client_uses_us_usd_google_locale_by_default(monkeypatch):
    """Google Flights requests should ask for USD independent of server region."""
    monkeypatch.delenv("FLI_GOOGLE_LANGUAGE", raising=False)
    monkeypatch.delenv("FLI_GOOGLE_REGION", raising=False)
    monkeypatch.delenv("FLI_GOOGLE_CURRENCY", raising=False)

    params = Client._with_default_params({})["params"]

    assert params == {"hl": "en-US", "gl": "US", "curr": "USD"}


def test_client_locale_can_be_overridden(monkeypatch):
    """Deployments can still change the Google Flights locale via env vars."""
    monkeypatch.setenv("FLI_GOOGLE_LANGUAGE", "en-GB")
    monkeypatch.setenv("FLI_GOOGLE_REGION", "GB")
    monkeypatch.setenv("FLI_GOOGLE_CURRENCY", "gbp")

    params = Client._with_default_params({"params": {"curr": "EUR"}})["params"]
    headers = Client._headers()

    assert params == {"hl": "en-GB", "gl": "GB", "curr": "EUR"}
    assert headers["accept-language"] == "en-GB,en;q=0.9"
