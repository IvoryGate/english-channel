from __future__ import annotations


def chunk_text(text: str, max_chars: int = 380) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    words = normalized.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word]).strip()
        if len(candidate) <= max_chars:
            current.append(word)
            continue
        if current:
            chunks.append(" ".join(current))
        current = [word]
    if current:
        chunks.append(" ".join(current))
    return chunks
