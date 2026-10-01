from app.utils.logging import redact, token_fingerprint


def test_secrets_and_media_tokens_redacted():
    token = "opaque-token-value"
    output = redact(f"Authorization: Bearer secret /media/pending/{token}?x=1")
    assert "Bearer secret" not in output and token not in output and "{token}" in output
    assert len(token_fingerprint(token)) == 12

