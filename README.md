# Telegram AI Auto Post Bot

Tamil, English, Thanglish understand pannura async Telegram assistant. Normal questions/caption requests LLM-kku pogum; explicit image requests mattum image provider-kku pogum. Generated image pending preview-a save aagum. **Platform select panninaalum publish aagathu — owner Preview → Confirm callback complete pannina mattum publish aagum.**

## Architecture

`backend/app/config` settings/prompts-ai own pannum. `ai` chat, routing, memory; `image` real provider adapters and Pillow overlay; `telegram` PTB lifecycle/handlers/webhook; `social` pending state, media URL, OAuth, encrypted account connection, platform publishing; `utils` HTTP, validation, logging and public-host safety.

Required source layout is under `backend/`: `app/{config,ai,image,social,telegram,utils}`, `scripts`, and `tests`. Runtime-only `data/`, `tmp/pending/`, `out/`, `.tmp/`, caches and `.venv/` are gitignored. Pending token index is memory-only: process restart-kku apram old preview buttons work aagathu; image files alone mapping-ai restore panna mudiyathu.

## Setup and run

Windows PowerShell:

```powershell
cd backend
.\scripts\setup.ps1
# backend/.env-ai private-a edit pannunga
.\scripts\run.ps1
```

Linux/macOS:

```sh
cd backend
chmod +x scripts/*.sh
./scripts/setup.sh
# backend/.env-ai private-a edit pannunga
./scripts/run.sh
```

Direct run: `python -m app`. Process-only `HOST` (default `0.0.0.0`), `PORT` (`8000`) and `RELOAD` (`false`) are supported. Uvicorn full URL access logs are disabled so OAuth codes/media tokens logs-la varathu.

`backend/.env` is the exact active minimal profile: DeepSeek chat + Cloudflare image + Instagram Login mode. Secrets ellam blank. `backend/.env.example` is the complete documented template; adhu Pollinations and Facebook-login defaults-ai preserve pannum. Process environment values file values-ai override pannum.

## Credentials

- Telegram token: [@BotFather](https://t.me/BotFather). `TELEGRAM_BOT_TOKEN`-la set pannunga. Webhook use pannina public URL, path and secret configure pannunga.
- DeepSeek/OpenAI-compatible provider: selected vendor developer dashboard-la API key create panni `AI_API_KEY`, optional `AI_MODEL`/`AI_BASE_URL` set pannunga.
- Cloudflare Workers AI: [Cloudflare API token docs](https://developers.cloudflare.com/workers-ai/get-started/rest-api/) follow panni account ID + token configure pannunga. Current official REST guide custom token-kku Workers AI Read + Edit permissions specify pannuthu. `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`-la store pannunga.

Cloudflare Workers AI **image generate pannum service**. `cloudflared` **local port 8000-ai public HTTPS-la expose pannum tunnel**. Rendum different. Tunnel restart-la quick-tunnel hostname change aagalam; `SOCIAL_PUBLIC_BASE_URL` update panni backend restart, OAuth callback registrations update pannunga.

## Meta, LinkedIn and X

Meta developer app-la exact callback register pannunga:

```text
https://YOUR_PUBLIC_HOST/auth/facebook/callback
```

Page-linked Instagram-ku Facebook Login, managed Page discovery, Page-linked professional Instagram account and approved scopes (`pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`) required. `INSTAGRAM_LOGIN_FLOW=instagram` direct Instagram Login token/Graph host use pannum; `facebook` Page-linked Facebook Graph host use pannum. Token types/endpoints mix panna koodathu. Tester/developer role acceptance development testing-kku applicable; adhu App Review or real publishing permission bypass illa.

LinkedIn image workflow current official [Images API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api) initialize-upload and [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api) create-post endpoints use pannuthu. Member posting-ku `w_member_social`; organization posting-ku approved `w_organization_social` and correct Page role venum. Callback: `https://YOUR_PUBLIC_HOST/auth/linkedin/callback`.

X per-user consent OAuth 2.0 + PKCE use pannum. Media upload implementation OAuth 1.0a credentials-ai preserve pannuthu because configured media endpoint requires that auth; unsupported OAuth 2 media publish-ai another account-ku fallback pannaathu. Callback: `https://YOUR_PUBLIC_HOST/auth/x/callback`.

Secrets, IDs, access tokens-ai chat, source, screenshot, log-la paste panna vendam. `python scripts/generate_social_key.py --write-env` encrypted SQLite key-ai print pannama `.env`-la write pannum; existing key-ai overwrite pannaathu. Key illana connection memory-only, restart-la disappear aagum.

## Bot flow

1. `/connect facebook|linkedin|x` consent link open pannunga. Direct Instagram Login server token mode `.env`-la configure pannunga.
2. `/status` connection summary check pannunga.
3. Explicit image request or `/image ...` anuppunga.
4. Bot image + platform buttons return pannum. Innum publish aagala.
5. Platform select → preview check → **Confirm publish**. Owner user mattum confirm/cancel panna mudiyum; atomic claim double-click duplicate publish-ai block pannum.

Commands: `/start`, `/help`, `/id`, `/reset`, `/image`, `/post`, `/cancel`, `/status`, `/connect`, `/disconnect`.

## Public media troubleshooting

Meta server exact `https://HOST/media/pending/REAL_OPAQUE_TOKEN` GET panna vendum. `SOCIAL_PUBLIC_BASE_URL` clean public HTTPS host-a irukkanum; localhost/private IP/credentials/wrapper backticks reject aagum. Tunnel same backend `http://127.0.0.1:8000`-ku forward aaganum. Exact URL response `200`, `Content-Type: image/jpeg`, nonempty valid bytes irukkanum. PNG/WEBP serving time-la JPEG conversion aagum; existing JPEG byte-for-byte preserve aagum. Unknown/cancelled/expired token `404`. Quick tunnel DNS, current hostname, preview TTL and process restart check pannunga. `python scripts/media_probe_server.py path/to/image.png` is an explicit safe GET probe; raw tokenized URL print pannaathu and publish call pannaathu.

DNS/public URL failure generated image corruption illa. Tunnel-ai fix pannunga; image generation provider-ai maathuradhu solution illa.

## Tests and diagnostics

```powershell
cd backend
python -m pytest -q
python -m ruff check app scripts tests
python scripts/local_smoke_test.py
python scripts/check_setup.py
```

Tests mocked boundaries use pannum; real social post create pannaathu. `check_setup.py --generate` mattum explicit opt-in provider generation/cost trigger pannalam. `check_instagram.py` account read check; `check_social_oauth.py` callback/config check. `set_webhook.py` and `delete_webhook.py` explicit operations.

Docker:

```sh
docker build -t telegram-ai-bot backend
docker run --env-file backend/.env -p 8000:8000 telegram-ai-bot
```

Credentials/vendor roles/quota/App Review illama integration success claim panna mudiyathu. Readiness `503` degraded reasons return pannum; `/healthz` liveness separate. Live publish always explicit preview confirmation-kku apram mattum.

