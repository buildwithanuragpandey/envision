import pytest
import uuid
from app.schemas.document import TextChunk
from app.services.vector_store_service import vector_store_service
from app.services.retrieval_service import retrieval_service

@pytest.fixture(autouse=True)
def setup_teardown_vectors():
    vector_store_service.clear_all()
    # Seed chunks
    doc1_id = str(uuid.uuid4())
    doc2_id = str(uuid.uuid4())
    
    chunks = [
        TextChunk(
            chunk_id=str(uuid.uuid4()),
            document_id=doc1_id,
            filename="Quantum_Paper.pdf",
            page_number=1,
            chunk_index=0,
            content="The Hyperion-X quantum processor features 1,024 superconducting qubits with 320 microseconds coherence time.",
            document_hash="hash1"
        ),
        TextChunk(
            chunk_id=str(uuid.uuid4()),
            document_id=doc2_id,
            filename="Battery_Paper.pdf",
            page_number=3,
            chunk_index=0,
            content="Solid-state Lithium-Sulfur battery cells demonstrated 650 Wh/kg energy density and 1,500 cycle life.",
            document_hash="hash2"
        )
    ]
    vector_store_service.add_chunks(chunks)
    yield
    vector_store_service.clear_all()

def test_semantic_retrieval():
    chunks, citations, confidence, latency_ms = retrieval_service.retrieve_context(
        query="What is the coherence time of the quantum processor?",
        top_k=2
    )
    assert len(chunks) > 0
    assert "Quantum_Paper.pdf" in chunks[0]["filename"]
    assert citations[0].page_number == 1
    assert confidence > 0.3

def test_document_filtering():
    # Retrieve all document IDs
    doc_ids = vector_store_service.get_all_document_ids()
    assert len(doc_ids) == 2
    
    # Filter to only the battery paper
    battery_doc_id = [d for d in doc_ids if "Battery_Paper.pdf" in vector_store_service.search("battery", document_ids=[d])[0]["filename"]][0]
    
    chunks, citations, _, _ = retrieval_service.retrieve_context(
        query="Tell me about computing and batteries",
        document_ids=[battery_doc_id]
    )
    
    assert len(chunks) == 1
    assert chunks[0]["filename"] == "Battery_Paper.pdf"
