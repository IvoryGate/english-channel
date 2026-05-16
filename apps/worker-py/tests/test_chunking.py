from worker.chunking import chunk_text


def test_chunk_text_splits_long_input() -> None:
    source = " ".join(["hello"] * 300)
    chunks = chunk_text(source, max_chars=120)
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)
