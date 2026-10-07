from __future__ import annotations

import socket
from pathlib import Path

from worker.imagegen.chatgpt import (
    build_parser,
    iter_chunks,
    jitter,
    load_prompt,
    mime_to_ext,
)
from worker.imagegen.session import cdp_ready, port_alive


def test_iter_chunks_covers_text_with_bounded_sizes() -> None:
    text = "a quiet harbor at dawn, wide cinematic light" * 3
    chunks = list(iter_chunks(text, jitter))
    assert "".join(chunks) == text
    assert chunks
    # Full chunks are 5-13 characters; only the final remainder may be shorter.
    assert all(len(chunk) <= 13 for chunk in chunks)
    assert all(len(chunk) >= 5 for chunk in chunks[:-1])
    assert 1 <= len(chunks[-1]) <= 13


def test_iter_chunks_handles_empty_text_and_tiny_random() -> None:
    assert list(iter_chunks("", jitter)) == []
    # A degenerate random source must never produce zero-length chunks
    # (which would loop forever).
    chunks = list(iter_chunks("abcdefghij", lambda _lo, _hi: 0.4))
    assert "".join(chunks) == "abcdefghij"
    assert all(len(chunk) >= 1 for chunk in chunks)


def test_jitter_stays_within_bounds() -> None:
    for _ in range(60):
        value = jitter(2.5, 6.5)
        assert 2.5 <= value <= 6.5


def test_mime_to_ext_maps_known_and_falls_back() -> None:
    assert mime_to_ext("image/png") == "png"
    assert mime_to_ext("image/jpeg") == "jpg"
    assert mime_to_ext("image/webp") == "webp"
    assert mime_to_ext("application/octet-stream") == "bin"


def test_parser_requires_exactly_one_prompt_source() -> None:
    parser = build_parser()
    # Missing source.
    try:
        parser.parse_args(["--out", "cover.png"])
        raise AssertionError("expected SystemExit")
    except SystemExit:
        pass
    # Both sources at once.
    try:
        parser.parse_args(["--prompt", "a", "--prompt-file", "p.txt", "--out", "cover.png"])
        raise AssertionError("expected SystemExit")
    except SystemExit:
        pass
    # Missing --out.
    try:
        parser.parse_args(["--prompt", "a"])
        raise AssertionError("expected SystemExit")
    except SystemExit:
        pass
    # Happy path.
    args = parser.parse_args(["--prompt", "a scene", "--out", "cover.png", "--chat", "continue"])
    assert args.out == "cover.png"
    assert args.chat == "continue"
    assert not args.standalone


def test_load_prompt_reads_file_and_rejects_blank(tmp_path: Path) -> None:
    parser = build_parser()
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("  a lantern-lit pier\n", encoding="utf-8")
    args = parser.parse_args(["--prompt-file", str(prompt_file), "--out", "x.png"])
    assert load_prompt(args, parser) == "a lantern-lit pier"

    empty = tmp_path / "empty.txt"
    empty.write_text("   \n", encoding="utf-8")
    args = parser.parse_args(["--prompt-file", str(empty), "--out", "x.png"])
    try:
        load_prompt(args, parser)
        raise AssertionError("expected SystemExit for empty prompt")
    except SystemExit:
        pass


def test_cdp_probes_distinguish_closed_listening_and_http_ports() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    probe.listen(1)
    port = probe.getsockname()[1]
    try:
        # Listening but not a CDP endpoint.
        assert port_alive(port) is True
        assert cdp_ready(port) is False
    finally:
        probe.close()
    # Just-closed ephemeral port: nothing is listening.
    assert port_alive(port) is False
    assert cdp_ready(port) is False
