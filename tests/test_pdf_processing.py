import os
import pytest
import fitz
from app.services.pdf_service import pdf_service, PDFProcessingError
from app.schemas.document import DocumentStatus

def test_pdf_hash_calculation():
    data = b"DocuMind Test PDF Content"
    hash1 = pdf_service.calculate_sha256(data)
    hash2 = pdf_service.calculate_sha256(data)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_pdf_text_cleaning():
    raw_text = "Line 1   with    extra    spaces.\n\n\n\nLine 2 with \xa0 non-breaking spaces."
    cleaned = pdf_service.clean_text(raw_text)
    assert "   " not in cleaned
    assert "\xa0" not in cleaned
    assert "Line 1 with extra spaces." in cleaned
    assert "Line 2 with non-breaking spaces." in cleaned

def test_valid_pdf_extraction(tmp_path):
    # Create test PDF
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Hello from Page 1 of DocuMind test document.")
    p2 = doc.new_page()
    p2.insert_text((50, 50), "Hello from Page 2 with secondary findings.")
    pdf_bytes = doc.tobytes()
    doc.close()

    metadata, pages = pdf_service.validate_and_extract(pdf_bytes, "test_sample.pdf")
    
    assert metadata.filename == "test_sample.pdf"
    assert metadata.total_pages == 2
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Page 1" in pages[0].text
    assert pages[1].page_number == 2
    assert "Page 2" in pages[1].text

def test_invalid_file_extension():
    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.validate_and_extract(b"Not a pdf", "test.txt")
    assert "Only .pdf files are supported" in str(exc_info.value)
