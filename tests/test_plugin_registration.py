from hermes_max_adapter.plugin import build_registration


def test_build_registration_exposes_expected_platform_metadata():
    registration = build_registration()
    assert registration["name"] == "max"
    assert registration["required_env"] == ["MAX_BOT_TOKEN"]
    assert registration["cron_deliver_env_var"] == "MAX_HOME_CHANNEL"
    assert registration["max_message_length"] > 0
