# MAX Bot API — Research Notes for Hermes Adapter

**Date:** 2026-06-03

## Confirmed

### Delivery model
- MAX supports **Webhook** and **Long Polling**.
- **Webhook is the recommended production mode**.
- **Long Polling is not suitable for production** due to speed and event-retention limits.
- Both modes **cannot be used simultaneously**.

### Webhook subscription
- Create subscription: `POST /subscriptions`
- List subscriptions: `GET /subscriptions`
- Webhook delivers events as HTTPS POST with an `Update` object.

### Webhook security
- Optional subscription `secret` is echoed back in header `X-Max-Bot-Api-Secret`.
- Header should be validated.
- Bot API auth token is passed via `Authorization` header.

### TLS / endpoint constraints
- Webhook endpoint must be **HTTPS**.
- Supported port: **443 only**.
- Self-signed certificates are not supported.
- Trusted CA cert, valid hostname, and full chain are required.

### Delivery guarantees / failure behavior
- Endpoint must return `HTTP 200` within **30 seconds**.
- Any non-200 or timeout counts as failure.
- MAX retries failed delivery up to **10 times**.
- Backoff starts `60s`, `150s`, `375s`, then continues ×2.5.
- If no successful answer for **8 hours**, bot is automatically unsubscribed from webhook.

### Outbound send
- Official send-message endpoint: `POST /messages`.

### Limits
- Official docs recommend no more than **30 rps** to `platform-api.max.ru`.

### Observed update/event names from docs/examples
- `message_created`
- `message_callback`
- `bot_started`

## Likely but not fully confirmed
- Full body schema for `POST /messages`
- Attachment/media object contracts
- Edit/delete exact endpoint semantics
- Full callback-answer flow
- All update types
- Text size limit and formatting guarantees

## Sources
- https://dev.max.ru/docs-api
- https://dev.max.ru/docs-api/methods/POST/subscriptions
- https://dev.max.ru/docs/chatbots/bots-coding/prepare
- Secondary cross-check: https://github.com/BushlanovDev/max-bot-api-client-php/blob/master/docs/README.md

## Notes
This file intentionally separates confirmed facts from open questions. Unknown areas must stay feature-flagged or safely degraded during implementation.
