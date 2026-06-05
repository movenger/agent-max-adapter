# Deployment notes

## Production ingress

- MAX production delivery should use **HTTPS** only.
- Webhook endpoint should be exposed on **port 443**.
- Put the Python app behind a **reverse proxy** (for example nginx or Caddy).
- TLS certificate must be valid and trusted.

## Suggested topology

- MAX Bot API -> reverse proxy -> local webhook app
- reverse proxy terminates TLS
- application runs on localhost high port

## Subscription reconcile and watchdog

- On startup, inspect current remote **subscriptions**.
- If remote subscription URL/secret do not match local config, perform re-subscribe.
- Run a lightweight **watchdog** on a schedule to detect webhook drift or silent unsubscribe.
- Watchdog can be implemented via systemd timer, Hermes cron, or external scheduler.

## systemd recommendation

- Run adapter/webhook process as a **systemd** service.
- Run reconcile/watchdog as a periodic **systemd timer** or equivalent job.
- Keep secrets in environment files, not in unit files committed to repo.

## Operational checklist

- Configure `MAX_WEBHOOK_SECRET`
- Configure `MAX_WEBHOOK_URL`
- Ensure proxy forwards `X-Max-Bot-Api-Secret`
- Ensure JSON request bodies reach the app unchanged
- Add health endpoint and logs before public rollout
