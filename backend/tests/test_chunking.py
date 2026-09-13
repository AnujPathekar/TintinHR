from app.rag.chunking import ParsedPage, chunk_pages


def test_chunking_preserves_page_and_overlap() -> None:
    pages = [ParsedPage(page_number=4, text=" ".join(f"word{i}" for i in range(30)))]
    chunks = chunk_pages(pages, target_words=20, overlap_words=5)
    assert len(chunks) == 2
    assert all(chunk.page_number == 4 for chunk in chunks)
    assert chunks[0].text.split()[-5:] == chunks[1].text.split()[:5]

