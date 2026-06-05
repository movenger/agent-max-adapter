from hermes_max_adapter.plugin import build_registration


def test_build_registration_contains_adapter_factory_and_validate_config():
    registration = build_registration()
    assert callable(registration["adapter_factory"])
    assert callable(registration["validate_config"])
    assert registration["label"] == "MAX"
