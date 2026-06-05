from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib import request as urllib_request

from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentSourceKind, AttachmentRef

_ATTACHMENT_REQUEST_TYPE_BY_KIND: dict[AttachmentKind, str] = {
    AttachmentKind.PHOTO: "image",
    AttachmentKind.VIDEO: "video",
    AttachmentKind.DOCUMENT: "file",
    AttachmentKind.AUDIO: "audio",
}

_UPLOAD_TYPE_BY_KIND: dict[AttachmentKind, str] = {
    AttachmentKind.PHOTO: "image",
    AttachmentKind.VIDEO: "video",
    AttachmentKind.DOCUMENT: "file",
    AttachmentKind.AUDIO: "audio",
    AttachmentKind.VOICE: "audio",
    AttachmentKind.STICKER: "image",
    AttachmentKind.ANIMATION: "video",
}

_SEND_FIELD_BY_KIND: dict[AttachmentKind, str] = {
    AttachmentKind.PHOTO: "photo",
    AttachmentKind.VIDEO: "video",
    AttachmentKind.DOCUMENT: "document",
    AttachmentKind.AUDIO: "audio",
    AttachmentKind.VOICE: "voice",
    AttachmentKind.STICKER: "sticker",
    AttachmentKind.ANIMATION: "animation",
}


def normalize_upload_source(attachment: AttachmentRef) -> dict[str, str]:
    if attachment.source == AttachmentSourceKind.VENDOR_TOKEN and attachment.upload_token:
        return {"mode": "token", "value": attachment.upload_token}
    if attachment.source == AttachmentSourceKind.EXTERNAL_URL and attachment.url:
        return {"mode": "url", "value": attachment.url}
    if attachment.source == AttachmentSourceKind.LOCAL_FILE and attachment.local_path:
        return {"mode": "file", "value": attachment.local_path}
    raise ValueError(f"Unsupported upload source: {attachment.source}")


def upload_local_file_for_attachment(
    *,
    base_url: str,
    token: str,
    attachment: AttachmentRef,
) -> dict[str, str]:
    upload_type = _UPLOAD_TYPE_BY_KIND.get(attachment.kind)
    send_field = _SEND_FIELD_BY_KIND.get(attachment.kind)
    local_path = attachment.local_path
    if upload_type is None or send_field is None or not local_path:
        raise ValueError(f"Local file upload is not supported for attachment kind: {attachment.kind}")

    file_path = Path(local_path)
    file_name = attachment.file_name or file_path.name
    mime_type = attachment.mime_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    boundary = "----HermesMaxAdapterBoundary7MA4YWxkTrZu0gW"
    file_bytes = file_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{file_name}\"\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib_request.Request(
        f"{base_url}/uploads?type={upload_type}",
        data=body,
        headers={
            "Authorization": token,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=30) as resp:
        import json
        response = json.loads(resp.read().decode("utf-8", errors="replace"))

    if send_field in {"audio", "voice"} and response.get("token"):
        return {send_field: response["token"]}
    if response.get("url"):
        if send_field in {"video", "voice", "sticker", "animation"}:
            if send_field != "video":
                token = response.get("token")
                if token:
                    return {send_field: token}
            return {send_field: response["url"]}
    if request_type := _ATTACHMENT_REQUEST_TYPE_BY_KIND.get(attachment.kind):
        if response.get("token"):
            return {"attachments": [{"type": request_type, "payload": {"token": response["token"]}}]}
        photos = response.get("photos")
        if isinstance(photos, dict):
            for item in photos.values():
                token = item.get("token") if isinstance(item, dict) else None
                if token:
                    return {"attachments": [{"type": request_type, "payload": {"token": token}}]}
    raise ValueError(f"Upload response missing usable send handle for attachment kind: {attachment.kind}")


def build_outbound_attachment_payload(attachment: AttachmentRef):
    if attachment.kind in {AttachmentKind.CONTACT, AttachmentKind.LOCATION}:
        if attachment.kind == AttachmentKind.CONTACT:
            return {
                "contact": {
                    "name": attachment.metadata.get("name", ""),
                    "phone": attachment.metadata.get("phone", ""),
                }
            }
        return {
            "location": {
                "latitude": attachment.metadata.get("latitude"),
                "longitude": attachment.metadata.get("longitude"),
            }
        }

    resolved = normalize_upload_source(attachment)
    if resolved["mode"] == "file":
        raise ValueError(f"Local file attachment requires vendor upload before send: {attachment.kind}")

    request_type = _ATTACHMENT_REQUEST_TYPE_BY_KIND.get(attachment.kind)
    if request_type is None:
        return {str(attachment.kind): resolved["value"]}

    payload: dict[str, str] = {"token": resolved["value"]} if resolved["mode"] == "token" else {"url": resolved["value"]}
    return {"attachments": [{"type": request_type, "payload": payload}]}
