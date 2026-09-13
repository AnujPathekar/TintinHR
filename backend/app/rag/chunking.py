from dataclasses import dataclass


@dataclass
class ParsedPage:
    page_number: int | None
    text: str
    section: str | None = None


@dataclass
class Chunk:
    text: str
    page_number: int | None
    section: str | None
    token_count: int


def chunk_pages(pages: list[ParsedPage], target_words: int = 350, overlap_words: int = 60) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        words = page.text.split()
        start = 0
        while start < len(words):
            end = min(start + target_words, len(words))
            text = " ".join(words[start:end]).strip()
            if text:
                chunks.append(Chunk(text, page.page_number, page.section, len(words[start:end])))
            if end == len(words):
                break
            start = max(start + 1, end - overlap_words)
    return chunks

