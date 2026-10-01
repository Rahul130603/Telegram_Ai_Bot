from app.telegram.handlers import confirm_keyboard, platform_keyboard


def test_callbacks_contain_opaque_token_and_require_confirm():
    token = "opaque"
    platforms = platform_keyboard(token).inline_keyboard
    assert any(button.callback_data == f"platform:instagram:{token}" for row in platforms for button in row)
    confirm = confirm_keyboard(token).inline_keyboard[0]
    assert confirm[0].callback_data == f"confirm:{token}"
    assert confirm[1].callback_data == f"cancel:{token}"

