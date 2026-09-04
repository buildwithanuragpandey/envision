import os
import sys
import json
import asyncio

# Ensure backend and root paths are in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))
sys.path.insert(0, ROOT_DIR)

from app.core.config import settings
from app.services.pdf_service import pdf_service
from app.services.chunking_service import chunking_service
from app.services.vector_store_service import vector_store_service
from app.services.retrieval_service import retrieval_service
from app.services.chat_service import chat_service
from app.schemas.chat import ChatRequest
from evaluation.generate_sample_pdfs import generate_all_samples

async def run_evaluation():
    print("=" * 60)
    print("        DocuMind AI — Comprehensive RAG Evaluation        ")
    print("=" * 60)

    # 1. Seed or ensure sample documents are indexed
    samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_docs"))
    samples = generate_all_samples(samples_dir)
    
    print(f"\n[1/3] Indexing benchmark sample documents into ChromaDB...")
    vector_store_service.clear_all()
    
    for filename, filepath in samples.items():
        with open(filepath, "rb") as f:
            content = f.read()
        meta, pages = pdf_service.validate_and_extract(content, filename)
        chunks = chunking_service.chunk_pages(pages, meta)
        vector_store_service.add_chunks(chunks)
        print(f"  ✓ Indexed '{filename}': {meta.total_pages} pages, {len(chunks)} chunks")

    # 2. Load dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        benchmark_items = json.load(f)

    print(f"\n[2/3] Running evaluation over {len(benchmark_items)} benchmark queries (Top-K = {settings.TOP_K})...\n")

    top_k = settings.TOP_K
    precisions = []
    recalls = []
    reciprocal_ranks = []
    citation_accuracies = []
    groundedness_scores = []

    for item in benchmark_items:
        qid = item["id"]
        question = item["question"]
        expected_doc = item["expected_document"]
        expected_page = item["expected_page"]
        key_facts = item["key_facts"]

        # Run retrieval
        chunks, citations, confidence, latency_ms = retrieval_service.retrieve_context(
            query=question,
            top_k=top_k
        )

        # Retrieval Metrics
        relevant_retrieved = 0
        first_relevant_rank = None

        for rank, chunk in enumerate(chunks, start=1):
            is_relevant = False
            if expected_doc == "multi_doc":
                # For cross-document queries, any of the key facts matching indicates relevance
                if any(fact.lower() in chunk["content"].lower() for fact in key_facts):
                    is_relevant = True
            else:
                if chunk["filename"] == expected_doc:
                    # Check page proximity or content match
                    if chunk["page_number"] == expected_page or any(fact.lower() in chunk["content"].lower() for fact in key_facts):
                        is_relevant = True

            if is_relevant:
                relevant_retrieved += 1
                if first_relevant_rank is None:
                    first_relevant_rank = rank

        precision_k = relevant_retrieved / max(len(chunks), 1)
        # Assuming at least 1 ground truth chunk per single query, or 2 for multi-doc
        expected_relevant_total = 2 if expected_doc == "multi_doc" else 1
        recall_k = min(1.0, relevant_retrieved / expected_relevant_total)
        mrr = (1.0 / first_relevant_rank) if first_relevant_rank else 0.0

        precisions.append(precision_k)
        recalls.append(recall_k)
        reciprocal_ranks.append(mrr)

        # Run full chat pipeline to test generation & citations
        chat_req = ChatRequest(message=question)
        response = await chat_service.answer_question(chat_req)

        # Evaluate citations
        citation_valid = False
        if citations:
            if expected_doc == "multi_doc":
                citation_valid = len(citations) >= 2
            else:
                citation_valid = any(c.filename == expected_doc for c in citations)
        citation_accuracies.append(1.0 if citation_valid else 0.0)

        # Evaluate faithfulness (absence of hallucinated contradiction)
        groundedness_scores.append(1.0 if response.is_grounded else 0.0)

        print(f"Query [{qid}]: \"{question[:50]}...\"")
        print(f"  → P@{top_k}: {precision_k:.2f} | R@{top_k}: {recall_k:.2f} | RR: {mrr:.2f} | Citations: {len(citations)} | Latency: {latency_ms:.1f}ms")

    # Aggregate Metrics
    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    avg_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    avg_citation_acc = sum(citation_accuracies) / len(citation_accuracies)
    avg_groundedness = sum(groundedness_scores) / len(groundedness_scores)

    print("\n" + "=" * 60)
    print("                     EVALUATION RESULTS                    ")
    print("=" * 60)
    print(f" Total Benchmark Questions Evaluated : {len(benchmark_items)}")
    print(f" Precision@{top_k}                        : {avg_precision:.4f} ({avg_precision*100:.1f}%)")
    print(f" Recall@{top_k}                           : {avg_recall:.4f} ({avg_recall*100:.1f}%)")
    print(f" Mean Reciprocal Rank (MRR)          : {avg_mrr:.4f}")
    print(f" Citation Accuracy                   : {avg_citation_acc:.4f} ({avg_citation_acc*100:.1f}%)")
    print(f" Response Faithfulness / Groundedness: {avg_groundedness:.4f} ({avg_groundedness*100:.1f}%)")
    print("=" * 60)

    results = {
        f"Precision@{top_k}": round(avg_precision, 4),
        f"Recall@{top_k}": round(avg_recall, 4),
        "MRR": round(avg_mrr, 4),
        "CitationAccuracy": round(avg_citation_acc, 4),
        "Faithfulness": round(avg_groundedness, 4),
        "TotalQueries": len(benchmark_items)
    }

    results_file = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    asyncio.run(run_evaluation())
