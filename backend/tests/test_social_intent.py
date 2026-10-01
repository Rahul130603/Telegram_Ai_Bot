from app.social.intent import detect_platform


def test_aliases_and_unknown():
    assert detect_platform("post it to insta") == "instagram"
    assert detect_platform("send Facebook") == "facebook"
    assert detect_platform("save only") is None

