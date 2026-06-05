from hermes_max_adapter.renderer import chunk_text


def test_chunk_text_preserves_short_messages():
    assert chunk_text("hello", limit=4000) == ["hello"]
