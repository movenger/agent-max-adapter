from hermes_max_adapter.mapping import build_source_descriptor


def test_build_source_descriptor_for_dm_chat():
    source = build_source_descriptor(
        chat_id="c1",
        user_id="u1",
        user_name="Denis",
        chat_type="dm",
        chat_name="Direct",
    )
    assert source["chat_id"] == "c1"
    assert source["user_id"] == "u1"
    assert source["chat_type"] == "dm"
    assert source["chat_name"] == "Direct"
    assert source["user_name"] == "Denis"
