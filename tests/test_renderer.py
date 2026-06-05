from hermes_max_adapter.models.actions import ActionButton, ActionButtonKind
from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.models.max_messages import (
    OutboundActionRowPart,
    OutboundAttachmentPart,
    OutboundMessage,
    OutboundTextPart,
)
from hermes_max_adapter.renderer import chunk_text, render_canonical_outbound_message, render_outbound_payload


def test_attachment_kind_and_source_cover_production_surface():
    assert AttachmentKind.PHOTO == "photo"
    assert AttachmentKind.VIDEO == "video"
    assert AttachmentKind.DOCUMENT == "document"
    assert AttachmentKind.AUDIO == "audio"
    assert AttachmentKind.VOICE == "voice"
    assert AttachmentKind.STICKER == "sticker"
    assert AttachmentKind.ANIMATION == "animation"
    assert AttachmentKind.CONTACT == "contact"
    assert AttachmentKind.LOCATION == "location"
    assert AttachmentKind.UNKNOWN == "unknown"

    assert AttachmentSourceKind.VENDOR_TOKEN == "vendor_token"
    assert AttachmentSourceKind.EXTERNAL_URL == "external_url"
    assert AttachmentSourceKind.LOCAL_FILE == "local_file"


def test_attachment_ref_can_model_remote_url_and_local_sources():
    remote = AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="tok-1")
    url = AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.EXTERNAL_URL, url="https://example.com/file.pdf")
    local = AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.LOCAL_FILE, local_path="/tmp/a.mp3")

    assert remote.upload_token == "tok-1"
    assert url.url == "https://example.com/file.pdf"
    assert local.local_path == "/tmp/a.mp3"


def test_action_button_kind_covers_production_surface():
    assert ActionButtonKind.CALLBACK == "callback"
    assert ActionButtonKind.LINK == "link"
    assert ActionButtonKind.MESSAGE == "message"
    assert ActionButtonKind.OPEN_APP == "open_app"
    assert ActionButtonKind.CLIPBOARD == "clipboard"
    assert ActionButtonKind.REQUEST_CONTACT == "request_contact"
    assert ActionButtonKind.REQUEST_LOCATION == "request_location"
    assert ActionButtonKind.UNKNOWN == "unknown"

    button = ActionButton(kind=ActionButtonKind.CALLBACK, text="Press", payload="btn:1")
    assert button.payload == "btn:1"
    assert button.url is None


def test_chunk_text_splits_long_messages():
    text = "a" * 9001
    chunks = chunk_text(text, limit=4000)
    assert len(chunks) == 3
    assert all(len(chunk) <= 4000 for chunk in chunks)


def test_render_canonical_outbound_message_text_only():
    payloads = render_canonical_outbound_message(
        OutboundMessage(target_chat_id="c1", parts=[OutboundTextPart(text="hello")])
    )
    assert payloads == [{"text": "hello"}]


def test_render_canonical_outbound_message_with_callback_button():
    payloads = render_canonical_outbound_message(
        OutboundMessage(
            target_chat_id="c1",
            parts=[
                OutboundTextPart(text="choose"),
                OutboundActionRowPart(
                    rows=[[ActionButton(kind=ActionButtonKind.CALLBACK, text="Go", payload="go:1")]]
                ),
            ],
        )
    )
    assert payloads == [
        {
            "text": "choose",
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [[{"type": "callback", "text": "Go", "payload": "go:1"}]]
                    },
                }
            ],
        }
    ]


def test_render_canonical_outbound_message_with_attachment_caption():
    payloads = render_canonical_outbound_message(
        OutboundMessage(
            target_chat_id="c1",
            parts=[
                OutboundAttachmentPart(
                    attachment=AttachmentRef(
                        kind=AttachmentKind.DOCUMENT,
                        source=AttachmentSourceKind.VENDOR_TOKEN,
                        upload_token="doc-1",
                    ),
                    caption="see file",
                )
            ],
        )
    )
    assert payloads == [
        {
            "attachments": [{"type": "file", "payload": {"token": "doc-1"}}],
            "text": "see file",
        }
    ]


def test_render_canonical_outbound_message_supports_photo_video_audio_and_voice_tokens():
    payloads = render_canonical_outbound_message(
        OutboundMessage(
            target_chat_id="c1",
            parts=[
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="ph-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.VIDEO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="vid-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="aud-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.VOICE, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="voc-1")),
            ],
        )
    )
    assert payloads == [
        {
            "attachments": [
                {"type": "image", "payload": {"token": "ph-1"}},
                {"type": "video", "payload": {"token": "vid-1"}},
                {"type": "audio", "payload": {"token": "aud-1"}},
            ],
            "voice": "voc-1",
        }
    ]


def test_render_canonical_outbound_message_supports_sticker_and_animation_tokens():
    payloads = render_canonical_outbound_message(
        OutboundMessage(
            target_chat_id="c1",
            parts=[
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.STICKER, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="st-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.ANIMATION, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="gif-1")),
            ],
        )
    )
    assert payloads == [
        {
            "sticker": "st-1",
            "animation": "gif-1",
        }
    ]


def test_render_canonical_outbound_message_supports_contact_and_location_payloads():
    payloads = render_canonical_outbound_message(
        OutboundMessage(
            target_chat_id="c1",
            parts=[
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.CONTACT, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"name": "Denis", "phone": "+799****0000"})),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.LOCATION, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"latitude": 55.75, "longitude": 37.61})),
            ],
        )
    )
    assert payloads == [
        {
            "contact": {"name": "Denis", "phone": "+799****0000"},
            "location": {"latitude": 55.75, "longitude": 37.61},
        }
    ]


def test_render_outbound_payload_returns_text_chunks():
    payloads = render_outbound_payload("hello")
    assert payloads == [{"text": "hello"}]


def test_render_outbound_payload_downgrades_unsupported_formatting():
    payloads = render_outbound_payload("hello ||spoiler|| world")
    assert payloads == [{"text": "hello spoiler world"}]
