# MAX Format Capability Matrix

**Date:** 2026-06-05  
**Status:** Honest runtime capability snapshot for current implementation stage.

## Outbound
- `text`: `live_confirmed`
- `buttons`: `full`
- `photo`: `live_confirmed`
- `video`: `live_confirmed`
- `document`: `live_confirmed`
- `audio`: `live_confirmed`
- `voice`: `live_confirmed`
- `sticker`: `live_confirmed`
- `animation`: `live_confirmed`
- `contact`: `live_confirmed`
- `location`: `live_confirmed`
- `external_url_attachment`: `degraded`
- `local_file_attachment`: `partially_live_confirmed`

## Inbound
- `text`: `live_confirmed`
- `photo`: `full`
- `video`: `full`
- `document`: `full`
- `audio`: `full`
- `voice`: `full`
- `sticker`: `full`
- `animation`: `full`
- `contact`: `degraded`
- `location`: `degraded`
- `callback`: `live_confirmed`
- `service`: `degraded`

## Interactions
- `callback_receive`: `live_confirmed`
- `callback_answer`: `live_confirmed`
- `callback_answer_notification`: `live_confirmed`
- `callback_answer_show_alert`: `live_confirmed`

## Notes
- `live_confirmed` means the path was exercised against the real MAX API and confirmed by a user-visible result where relevant.
- `partially_live_confirmed` means real upload/send flows are proven for important attachment kinds, but not every modeled local-file path is equally locked.
- `full` means code path and automated tests exist for the currently modeled canonical behavior.
- `degraded` means the adapter recognizes or can render the class of content, but full vendor-shape parity or semantics are not locked for every edge.
- Outbound `document`, `image/photo`, and `video` are now client-visible confirmed through the documented upload -> token -> `attachments[{type,payload}]` flow.
- Earlier false negatives on video were caused by a bad synthetic sample; a valid MP4 confirmed the documented contract.
- `HTTP 200` alone is not proof of media delivery; client-visible confirmation remains the source of truth.
- `local_file_attachment` is no longer blanket-unknown: key upload paths are proven, but the whole long-tail matrix is still not claimed complete.
- Live smoke scripts are runnable from `.env`; outbound smoke is live-token ready, webhook smoke is ready when `MAX_WEBHOOK_URL` is set.
