from hermes_max_adapter.capabilities import build_capability_snapshot
from hermes_max_adapter.models.capabilities import SupportLevel


def test_support_level_covers_honest_adapter_states():
    assert SupportLevel.FULL == "full"
    assert SupportLevel.DEGRADED == "degraded"
    assert SupportLevel.UNSUPPORTED == "unsupported"
    assert SupportLevel.UNKNOWN == "unknown"


def test_capability_snapshot_declares_current_support_honestly():
    snapshot = build_capability_snapshot()

    assert snapshot["outbound"]["text"] == SupportLevel.FULL
    assert snapshot["outbound"]["buttons"] in {SupportLevel.FULL, SupportLevel.DEGRADED}
    assert snapshot["interactions"]["callback_answer"] in {SupportLevel.UNKNOWN, SupportLevel.DEGRADED}
    assert snapshot["interactions"]["callback_answer_notification"] == SupportLevel.FULL
    assert snapshot["interactions"]["callback_answer_show_alert"] == SupportLevel.DEGRADED
    assert snapshot["outbound"]["location"] != SupportLevel.FULL
    assert snapshot["inbound"]["contact"] in {SupportLevel.DEGRADED, SupportLevel.UNKNOWN}
    assert snapshot["inbound"]["location"] in {SupportLevel.DEGRADED, SupportLevel.UNKNOWN}
    assert snapshot["outbound"]["external_url_attachment"] == SupportLevel.UNKNOWN
    assert snapshot["outbound"]["local_file_attachment"] == SupportLevel.UNSUPPORTED
