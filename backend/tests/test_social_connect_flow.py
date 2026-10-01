from cryptography.fernet import Fernet

from app.social.connections import ConnectionStore
from app.social.credentials import SocialCredentials


def test_fernet_persistence_and_cross_user_isolation(tmp_path):
    key = Fernet.generate_key().decode()
    path = tmp_path / "social.db"
    store = ConnectionStore(path, key)
    store.set(1, SocialCredentials("facebook", "secret", "page"))
    reloaded = ConnectionStore(path, key)
    assert reloaded.get(1, "facebook").access_token == "secret"
    assert reloaded.get(2, "facebook") is None
    assert b"secret" not in path.read_bytes()

