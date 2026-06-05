import pytest

from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.upload import build_outbound_attachment_payload, normalize_upload_source, upload_local_file_for_attachment


def test_normalize_upload_source_accepts_vendor_token_ref():
    attachment = AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="tok-1")
    resolved = normalize_upload_source(attachment)
    assert resolved["mode"] == "token"
    assert resolved["value"] == "tok-1"


def test_normalize_upload_source_accepts_external_url_ref():
    attachment = AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.EXTERNAL_URL, url="https://example.com/a.jpg")
    resolved = normalize_upload_source(attachment)
    assert resolved["mode"] == "url"
    assert resolved["value"] == "https://example.com/a.jpg"


def test_normalize_upload_source_accepts_local_file_ref():
    attachment = AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.LOCAL_FILE, local_path="/tmp/a.mp3")
    resolved = normalize_upload_source(attachment)
    assert resolved["mode"] == "file"
    assert resolved["value"] == "/tmp/a.mp3"


def test_build_outbound_attachment_payload_prefers_vendor_token():
    attachment = AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="tok-1")
    payload = build_outbound_attachment_payload(attachment)
    assert payload == {"attachments": [{"type": "file", "payload": {"token": "tok-1"}}]}


def test_build_outbound_attachment_payload_supports_external_url():
    attachment = AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.EXTERNAL_URL, url="https://example.com/a.jpg")
    payload = build_outbound_attachment_payload(attachment)
    assert payload == {"attachments": [{"type": "image", "payload": {"url": "https://example.com/a.jpg"}}]}


def test_build_outbound_attachment_payload_uses_file_attachment_envelope_for_vendor_token():
    attachment = AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="tok-1")
    payload = build_outbound_attachment_payload(attachment)
    assert payload == {"attachments": [{"type": "file", "payload": {"token": "tok-1"}}]}


def test_build_outbound_attachment_payload_uses_image_attachment_envelope_for_external_url():
    attachment = AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.EXTERNAL_URL, url="https://example.com/a.jpg")
    payload = build_outbound_attachment_payload(attachment)
    assert payload == {"attachments": [{"type": "image", "payload": {"url": "https://example.com/a.jpg"}}]}


def test_build_outbound_attachment_payload_preserves_vendor_payload_for_contact_and_location():
    contact = AttachmentRef(kind=AttachmentKind.CONTACT, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"name": "Denis", "phone": "+799"})
    location = AttachmentRef(kind=AttachmentKind.LOCATION, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"latitude": 55.75, "longitude": 37.61})
    assert build_outbound_attachment_payload(contact) == {"contact": {"name": "Denis", "phone": "+799"}}
    assert build_outbound_attachment_payload(location) == {"location": {"latitude": 55.75, "longitude": 37.61}}


def test_build_outbound_attachment_payload_rejects_local_file_without_vendor_upload():
    attachment = AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.LOCAL_FILE, local_path="/tmp/a.mp3")
    with pytest.raises(ValueError, match="requires vendor upload"):
        build_outbound_attachment_payload(attachment)


def test_normalize_upload_source_rejects_unknown_source_kind():
    attachment = AttachmentRef(kind=AttachmentKind.UNKNOWN, source=AttachmentSourceKind.UNKNOWN)
    with pytest.raises(ValueError, match="Unsupported upload source"):
        normalize_upload_source(attachment)


def test_upload_local_file_for_document_prefers_token_envelope_when_available(tmp_path, monkeypatch):
    path = tmp_path / "probe.txt"
    path.write_text("hello")

    captured = {}

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"fileId":3799165784,"token":"doc-token"}'

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["content_type"] = req.headers.get("Content-type") or req.headers.get("Content-Type")
        captured["authorization"] = req.headers.get("Authorization")
        body = req.data
        assert b'name="file"' in body
        assert b'filename="probe.txt"' in body
        assert b'hello' in body
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert captured["url"] == "https://platform-api.max.ru/uploads?type=file"
    assert "multipart/form-data" in captured["content_type"]
    assert captured["authorization"] == "token"
    assert payload == {"attachments": [{"type": "file", "payload": {"token": "doc-token"}}]}


def test_upload_local_file_for_audio_prefers_token(tmp_path, monkeypatch):
    path = tmp_path / "probe.mp3"
    path.write_bytes(b"ID3fake")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"url":"https://upload.example/audio-url","token":"audio-token"}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=audio"
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"audio": "audio-token"}


def test_upload_local_file_for_voice_prefers_token(tmp_path, monkeypatch):
    path = tmp_path / "probe.ogg"
    path.write_bytes(b"OggSfake")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"url":"https://upload.example/voice-url","token":"voice-token"}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=audio"
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.VOICE, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"voice": "voice-token"}


def test_upload_local_file_for_photo_prefers_image_token_envelope_when_available(tmp_path, monkeypatch):
    path = tmp_path / "probe.jpg"
    path.write_bytes(b"\xff\xd8\xff")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"photos":{"photo-id":{"token":"photo-token"}}}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=image"
        assert b'name="file"' in req.data
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"attachments": [{"type": "image", "payload": {"token": "photo-token"}}]}


def test_upload_local_file_for_video_prefers_upload_url_even_when_token_is_available(tmp_path, monkeypatch):
    path = tmp_path / "probe.mp4"
    path.write_bytes(b"ftypmp42")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"url":"https://upload.example/video-url","token":"video-token"}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=video"
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.VIDEO, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"video": "https://upload.example/video-url"}


def test_upload_local_file_for_sticker_prefers_token_when_available(tmp_path, monkeypatch):
    path = tmp_path / "probe.webp"
    path.write_bytes(b"RIFFfakeWEBP")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"url":"https://upload.example/sticker-url","token":"sticker-token"}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=image"
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.STICKER, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"sticker": "sticker-token"}


def test_upload_local_file_for_animation_prefers_token_when_available(tmp_path, monkeypatch):
    path = tmp_path / "probe.gif"
    path.write_bytes(b"GIF89a")

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"url":"https://upload.example/animation-url","token":"animation-token"}'

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://platform-api.max.ru/uploads?type=video"
        assert timeout == 30
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = upload_local_file_for_attachment(
        base_url="https://platform-api.max.ru",
        token="token",
        attachment=AttachmentRef(kind=AttachmentKind.ANIMATION, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
    )

    assert payload == {"animation": "animation-token"}


def test_upload_local_file_rejects_unsupported_kinds(tmp_path):
    path = tmp_path / "probe.bin"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="Local file upload is not supported"):
        upload_local_file_for_attachment(
            base_url="https://platform-api.max.ru",
            token="token",
            attachment=AttachmentRef(kind=AttachmentKind.UNKNOWN, source=AttachmentSourceKind.LOCAL_FILE, local_path=str(path)),
        )
