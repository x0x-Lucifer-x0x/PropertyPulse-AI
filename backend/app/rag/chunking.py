import re


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    """Splits text into chunks on sentence boundaries, each up to
    max_chars. Our knowledge-base docs are short (a paragraph or so), so
    most produce a single chunk; this exists so longer documents added
    later don't need special-casing.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks
