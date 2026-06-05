# MAX Media Truth Log

**Date:** 2026-06-05
**Scope:** outbound media delivery in `hermes-max-adapter`

## ДОКАЗАНО РАБОТАЕТ
- `GET /` on public webhook endpoint returns `200 ok`.
- `GET /.env` on public webhook endpoint returns `404 not found`.
- Inbound webhook delivery is live-confirmed by real `message_created` POSTs reaching the managed local listener.
- `POST /messages` text send is live-confirmed.
- Client-visible outbound `document` delivery is live-confirmed via upload -> token -> `attachments[{type:"file",payload:{token}}]`.
- Client-visible outbound `image/photo` delivery is live-confirmed via upload -> `photos[*].token` -> `attachments[{type:"image",payload:{token}}]`.
- Client-visible outbound `video` delivery is live-confirmed when using a valid MP4 artifact and the documented flow: `POST /uploads?type=video` -> upload file -> send `attachments[{type:"video",payload:{token}}]`.
- MAX docs confirm canonical outbound media surface on `POST /messages` is `attachments[]` with per-kind `{type, payload}` objects for documented media flows, and this is now client-visible confirmed for `document`, `image/photo`, and `video`.
- MAX docs confirm upload enum names: `image`, `video`, `audio`, `file`.
- MAX docs confirm `type=photo` is deprecated and must be replaced with `type=image`.
- MAX docs confirm upload processing may lag behind send and may return `attachment.not.ready`, requiring wait/retry.
- The earlier video failures were caused by a bad/insufficient video sample, not enough to invalidate the documented contract.
- Fresh test evidence after latest code changes: `pytest -q` => `159 passed`.

## НЕ РАБОТАЕТ / НЕ ПРОВЕРЕНО
- Uniform local-file upload -> send -> visible render path is not yet locked for every media kind.
- It is not yet proven which documented attachment/token shape the real MAX client reliably renders for every remaining media kind in this repo.
- Earlier `HTTP 200` media sends must not be treated as proof: user previously reported text-only visible result before the token attachment flow was corrected.

## OPEN HYPOTHESES
1. Some media kinds require `attachments[{type,payload:{token}}]` plus readiness delay/retry before they render visibly.
2. At least part of the current repo still mixes documented attachment flow with older top-level field flow.
3. `document` should be the narrowest next live probe because it has the clearest documented `file` attachment contract.
