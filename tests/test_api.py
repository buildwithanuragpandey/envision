import pytest
import io
import fitz
from fastapi.testclient import TestClient
from app.main import app
from app.services.vector_store_service import vector_store_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    vector_store_service.clear_all()
    yield
    vector_store_service.clear_all()

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_analytics_endpoint():
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_chunks" in data

def test_upload_and_chat_pipeline():
    # 1. Create in-memory test PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "DocuMind is an advanced Multi-PDF RAG assistant built for accurate document question answering.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload
    files = [("files", ("test_manual.pdf", io.BytesIO(pdf_bytes), "application/pdf"))]
    upload_res = client.post("/api/documents/upload", files=files)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert len(upload_data["documents"]) == 1
    assert upload_data["documents"][0]["filename"] == "test_manual.pdf"
    assert upload_data["documents"][0]["status"] == "Indexed"

    # 3. List documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Chat
    chat_res = client.post(
        "/api/chat",
        json={"message": "What is DocuMind designed for?"}
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert chat_data["sources"][0]["filename"] == "test_manual.pdf"
    assert chat_data["is_grounded"] is True

    # 5. Stream Chat with History
    stream_res = client.post(
        "/api/chat/stream",
        json={
            "message": "Can you explain it more?",
            "history": [
                {"role": "user", "content": "What is DocuMind designed for?"},
                {"role": "assistant", "content": "DocuMind is an advanced Multi-PDF RAG assistant."}
            ]
        }
    )
    assert stream_res.status_code == 200
    assert "event: token" in stream_res.text or "event: done" in stream_res.text

def test_delete_document():
    # Create and upload
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Temporary document content for deletion test.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = [("files", ("temp_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf"))]
    upload_res = client.post("/api/documents/upload", files=files)
    doc_id = upload_res.json()["documents"][0]["document_id"]

    # Delete
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["document_id"] == doc_id
