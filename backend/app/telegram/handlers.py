from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.config.prompts import SAFE_FAILURE
from app.utils.errors import AppError

logger = logging.getLogger(__name__)


def platform_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(name.title(), callback_data=f"platform:{name}:{token}") for name in ("instagram", "facebook")], [InlineKeyboardButton(name.title(), callback_data=f"platform:{name}:{token}") for name in ("linkedin", "x")], [InlineKeyboardButton("Cancel", callback_data=f"cancel:{token}")]])


def confirm_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm publish", callback_data=f"confirm:{token}"), InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{token}")]])


def register_handlers(runtime) -> None:
    app = runtime.application

    async def allowed(update: Update) -> bool:
        user = update.effective_user
        chat = update.effective_chat
        if not user or not chat:
            return False
        if runtime.settings.allowed_user_ids and user.id not in runtime.settings.allowed_user_ids:
            await runtime.client.send_message(chat.id, "Indha bot use panna permission illa.")
            return False
        if not runtime.rate_limiter.allow(user.id):
            await runtime.client.send_message(chat.id, "Konjam slow-a try pannunga; rate limit reach aayiduchu.")
            return False
        return True

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await allowed(update):
            await runtime.client.send_message(update.effective_chat.id, "Vanakkam! Question, caption, illa explicit image request anuppunga. Publish panna Preview → Confirm mandatory.")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await allowed(update):
            await runtime.client.send_message(update.effective_chat.id, "/image prompt · /post · /status · /connect platform · /disconnect platform · /reset · /cancel")

    async def identity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await allowed(update):
            await runtime.client.send_message(update.effective_chat.id, f"User ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}")

    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await allowed(update):
            runtime.agent.memory.clear(update.effective_chat.id)
            await runtime.client.send_message(update.effective_chat.id, "Conversation memory clear aayiduchu.")

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await allowed(update):
            return
        lines = ["Status:"]
        for platform in ("instagram", "facebook", "linkedin", "x"):
            connected = runtime.connections.get(update.effective_user.id, platform)
            lines.append(f"• {platform}: {'connected' if connected else 'env fallback / not connected'}")
        await runtime.client.send_message(update.effective_chat.id, "\n".join(lines))

    async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await allowed(update):
            return
        if not context.args or context.args[0].lower() not in {"facebook", "linkedin", "x", "instagram"}:
            await runtime.client.send_message(update.effective_chat.id, "Usage: /connect facebook|linkedin|x. Instagram Page-linked access uses /connect facebook; Instagram Login token is server-configured.")
            return
        platform = context.args[0].lower()
        if platform == "instagram":
            await runtime.client.send_message(update.effective_chat.id, "Instagram connection mode clear-a choose pannunga: Page-linked flow-ku /connect facebook; Instagram Login token server .env-la configure pannunga.")
            return
        try:
            url = runtime.oauth.consent_url(platform, update.effective_user.id)
        except AppError as exc:
            await runtime.client.send_message(update.effective_chat.id, exc.safe_message)
            return
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"Connect {platform.title()}", url=url)]])
        await runtime.client.send_message(update.effective_chat.id, "Official consent page open pannunga. URL/code inga paste panna vendam.", markup)

    async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await allowed(update):
            return
        if not context.args or context.args[0].lower() not in {"instagram", "facebook", "linkedin", "x"}:
            await runtime.client.send_message(update.effective_chat.id, "Usage: /disconnect instagram|facebook|linkedin|x")
            return
        runtime.connections.delete(update.effective_user.id, context.args[0].lower())
        await runtime.client.send_message(update.effective_chat.id, "Connection local-a remove aayiduchu. Vendor access revoke panna provider settings-um check pannunga.")

    async def handle_text(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text_override: str | None = None,
    ) -> None:
        if not await allowed(update):
            return
        text = text_override if text_override is not None else (update.effective_message.text or "")
        await runtime.client.chat_action(update.effective_chat.id, ChatAction.TYPING)
        try:
            result = await runtime.agent.handle(update.effective_chat.id, text)
            if result.intent != "image":
                await runtime.client.send_message(update.effective_chat.id, result.text)
                return
            await runtime.client.send_message(
                update.effective_chat.id,
                "⏳ Image generate aaguthu... konjam wait pannunga.",
            )
            await runtime.client.chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)
            spec = result.image_spec
            generated = await runtime.image_provider.generate(spec.visual_prompt, runtime.settings.image_size)
            from app.image.overlay import add_text_overlay
            generated = add_text_overlay(generated, [] if spec.no_text else spec.overlay_lines, enabled=runtime.settings.image_overlay_enabled, position=runtime.settings.image_overlay_position, max_lines=runtime.settings.image_overlay_max_lines, font_path=runtime.settings.image_overlay_font_path)
            pending = await runtime.social.register(update.effective_chat.id, update.effective_user.id, generated.data, spec.caption, spec.hashtags)
            await runtime.client.send_message(
                update.effective_chat.id,
                "✅ Image generate aayiduchu. Telegram-ku upload pannuren...",
            )
            await runtime.client.send_photo(update.effective_chat.id, generated.data, spec.caption or "Image ready. Platform select pannunga; idhu publish aagala.", platform_keyboard(pending.token))
        except AppError as exc:
            await runtime.client.send_message(update.effective_chat.id, exc.safe_message)
        except Exception:
            logger.exception("Telegram request failed")
            await runtime.client.send_message(update.effective_chat.id, SAFE_FAILURE)

    async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await runtime.client.send_message(update.effective_chat.id, "Usage: /image your visual request")
            return
        await handle_text(update, context, "Generate image " + " ".join(context.args))

    async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not update.effective_user:
            return
        await query.answer()
        parts = (query.data or "").split(":", 2)
        try:
            if parts[0] == "platform" and len(parts) == 3:
                post = await runtime.social.select_platform(parts[2], update.effective_user.id, parts[1])
                await runtime.client.edit_or_send(post.chat_id, query.message.message_id, f"Preview ready for {parts[1].title()}. Confirm panna mattum publish aagum.", confirm_keyboard(post.token))
            elif parts[0] == "confirm" and len(parts) == 2:
                result = await runtime.social.confirm(parts[1], update.effective_user.id)
                await runtime.client.edit_or_send(update.effective_chat.id, query.message.message_id, result.safe_message + (f"\n{result.permalink}" if result.permalink else ""))
            elif parts[0] == "cancel" and len(parts) == 2:
                post = await runtime.pending.cancel(parts[1], update.effective_user.id)
                await runtime.client.edit_or_send(post.chat_id, query.message.message_id, "Preview cancel aayiduchu. Publish aagala.")
        except AppError as exc:
            logger.warning("Social callback failed action=%s error=%s", parts[0] if parts else "unknown", exc)
            await runtime.client.edit_or_send(update.effective_chat.id, query.message.message_id, exc.safe_message)

    for command, handler in (("start", start), ("help", help_command), ("id", identity), ("reset", reset), ("status", status), ("connect", connect), ("disconnect", disconnect), ("image", image_command), ("post", help_command), ("cancel", help_command)):
        app.add_handler(CommandHandler(command, handler))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
