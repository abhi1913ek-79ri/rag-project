from services.pdf_reader import (
    open_pdf,
    extract_all_pages,
    split_into_paragraphs
)

from services.semantic_chunker import (
    # Embeddings and semantic chunking
    generate_embeddings,
    generate_query_embedding,
    calculate_similarities,
    find_semantic_boundaries,
    create_chunks,
    generate_document_id_from_file,

    # Retrieval
    retrieve_similar_chunks,
    filter_by_similarity,

    # Context, prompt and response
    build_context,
    create_retrieval_citation_map,
    build_prompt,
    build_response,

    # Citation validation and usage
    validate_citation_references,
    calculate_citation_usage,
    get_source_text_for_citation,
    compare_cited_source_with_retrieved,

    # Claim audit
    determine_overall_verdict,
    summarize_claim_audit,

    #intent classification
    classify_query_intent

    
)

from services.llm_service import (
    # Answer generation
    generate_answer,

    # Claim extraction and verification
    extract_claims_and_citations,
    verify_citation_support,
    parse_verification_result,
    verify_multiple_claims,
    parse_multiple_verification_results
)

import time

# In-memory cache for processed documents
document_cache = {}

def process_pdf(pdf_path: str) -> list:
    """
    Extract text from a PDF and convert it into
    semantically meaningful chunks with metadata.
    """

    document = open_pdf(pdf_path)

    try:
        pages = extract_all_pages(document)
    finally:
        document.close()

    document_id = generate_document_id_from_file(pdf_path)

    all_chunks = []
    next_chunk_index = 1

    for page_data in pages:
        page_number = page_data["page"]
        text = page_data["text"]

        paragraphs = split_into_paragraphs(text)

        if not paragraphs:
            continue

        # Generate paragraph embeddings
        embeddings = generate_embeddings(paragraphs)

        # Calculate adjacent paragraph similarities
        similarities = calculate_similarities(embeddings)

        # Find semantic boundaries
        boundaries = find_semantic_boundaries(similarities)

        # Create chunks with source metadata
        chunks = create_chunks(
            paragraphs=paragraphs,
            boundaries=boundaries,
            document_id=document_id,
            filename=pdf_path.split("/")[-1].split("\\")[-1],
            page=page_number,
            start_chunk_index=next_chunk_index
        )

        all_chunks.extend(chunks)
        next_chunk_index += len(chunks)

    return all_chunks


def run_rag_query(query: str, pdf_path: str) -> dict:
    """
    Process a PDF, retrieve relevant chunks,
    and generate an answer with source citations.
    """

    
    # intent classification
    # intent = classify_query_intent(query)
    # print("Detected query intent:", intent)
    start = time.perf_counter()

    intent = classify_query_intent(query)

    print(
        f"Intent detection: "
        f"{time.perf_counter() - start:.2f} seconds"
    )

    # Step 1: Process the PDF
    # chunks = process_pdf(pdf_path)
    start = time.perf_counter()

    # Step 1: Generate a cache key for this PDF
    document_id = generate_document_id_from_file(pdf_path)

    # Step 2: Check whether the PDF is already cached
    if document_id in document_cache:
        chunks = document_cache[document_id]["chunks"]
        print("PDF cache: HIT")
    else:
        chunks = process_pdf(pdf_path)
        document_cache[document_id] = {
            "chunks": chunks
        }
        print("PDF cache: MISS")

    print(
        f"PDF processing: "
        f"{time.perf_counter() - start:.2f} seconds"
    )

    if not chunks:
        return {
            "answer": "No readable text was found in the PDF.",
            "citations": {}
        }

    # Step 2: Generate embeddings for all chunks
    start = time.perf_counter()

    if document_id in document_cache and "embeddings" in document_cache[document_id]:
        chunk_embeddings = document_cache[document_id]["embeddings"]
        print("Embedding cache: HIT")
    else:
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_embeddings = generate_embeddings(chunk_texts)

        document_cache[document_id]["embeddings"] = chunk_embeddings
        print("Embedding cache: MISS")

    print(
        f"Chunk embeddings: "
        f"{time.perf_counter() - start:.2f} seconds"
    )
    # Step 3: Generate query embedding
    query_embedding = generate_query_embedding(query)

    # Step 4: Retrieve top 3 relevant chunks
    results = retrieve_similar_chunks(
        query_embedding=query_embedding,
        chunk_embeddings=chunk_embeddings,
        chunks=chunks,
        top_k=3
    )

    # Step 5: Filter by similarity
    filtered_results = filter_by_similarity(
        results,
        threshold=0.30
    )

    if not filtered_results:
        return {
            "answer": (
                "I could not find sufficiently relevant "
                "information in the provided document."
            ),
            "citations": {}
        }

    # Step 6: Build context and citation mapping
    context = build_context(filtered_results)

    citation_map = create_retrieval_citation_map(
        filtered_results
    )

    # Step 7: Build prompt
    prompt = build_prompt(query, context)

    # Step 8: Generate answer using Gemini
    # answer = generate_answer(prompt)
    start = time.perf_counter()
    answer = generate_answer(prompt)

    print(
        f"Answer generation: "
        f"{time.perf_counter() - start:.2f} seconds"
    )

    # Step 9: Return answer and citations

    response = build_response(
        answer,
        citation_map
    )

    # Step 10: Validate citation references
    citation_validation = validate_citation_references(
        answer=response["answer"],
        citation_map=response["citations"]
    )

    # Step 11: Calculate citation usage
    citation_usage = calculate_citation_usage(
        response["answer"],
        response["citations"]
    )

    # Step 12: Extract claims and their citations
    extracted_claims = extract_claims_and_citations(
        response["answer"]
    )

    claim_audit_results = []

    # Step 13: Batch verify claims against their cited sources

    verification_start = time.perf_counter()

    # Store verification results for each claim and citation
    verification_cache = {}

    # Group claims by source text
    source_groups = {}

    for claim_index, item in enumerate(extracted_claims):
        claim = item["claim"]
        citations = item["citations"]

        for citation in citations:
            source_text = get_source_text_for_citation(
                citation,
                filtered_results
            )

            if source_text is None:
                continue

            source_key = (citation, source_text)

            if source_key not in source_groups:
                source_groups[source_key] = []

            source_groups[source_key].append({
                "claim_index": claim_index,
                "claim": claim
            })


    # Verify claims belonging to each source in batches
    for (citation, source_text), group in source_groups.items():

        claims_to_verify = [
            item["claim"] for item in group
        ]

        raw_results = verify_multiple_claims(
            claims_to_verify,
            source_text
        )

        parsed_results = parse_multiple_verification_results(
            raw_results,
            len(claims_to_verify)
        )

        for position, group_item in enumerate(group, start=1):
            verification_cache[
                (group_item["claim_index"], citation)
            ] = parsed_results[position]


    print(
        f"Batch claim verification: "
        f"{time.perf_counter() - verification_start:.2f} seconds"
    )


    # Build the audit results while preserving existing output structure
    for claim_index, item in enumerate(extracted_claims):
        claim = item["claim"]
        citations = item["citations"]

        audited_claim = {
            "claim": claim,
            "citations": citations,
            "verification": []
        }

        if not citations:
            audited_claim["verification"].append({
                "citation": None,
                "verdict": "UNCERTAIN",
                "reason": "No citation was provided.",
                "source": None,
                "retrieval_comparison": None
            })

        for citation in citations:
            source_text = get_source_text_for_citation(
                citation,
                filtered_results
            )

            if source_text is None:
                audited_claim["verification"].append({
                    "citation": citation,
                    "verdict": "UNCERTAIN",
                    "reason": "Corresponding source was not found.",
                    "source": None,
                    "retrieval_comparison": None
                })
                continue

            parsed = verification_cache.get(
                (claim_index, citation)
            )

            if parsed is None:
                audited_claim["verification"].append({
                    "citation": citation,
                    "verdict": "UNCERTAIN",
                    "reason": "Batch verification result was unavailable.",
                    "source": None,
                    "retrieval_comparison": None
                })
                continue

            source_metadata = citation_map.get(citation, {})

            comparison = compare_cited_source_with_retrieved(
                citation,
                citation_map,
                filtered_results
            )

            audited_claim["verification"].append({
                "citation": citation,
                "verdict": parsed["verdict"],
                "reason": parsed["reason"],
                "source": {
                    "filename": source_metadata.get("filename"),
                    "page": source_metadata.get("page"),
                    "chunk_id": source_metadata.get("chunk_id")
                },
                "retrieval_comparison": {
                    "found": comparison["found"],
                    "similarity": comparison.get("cited_similarity"),
                    "rank": comparison.get("cited_rank")
                }
            })

        audited_claim["overall_verdict"] = (
            determine_overall_verdict(
                audited_claim["verification"]
            )
        )

        claim_audit_results.append(audited_claim)
    
    # Step 14: Generate audit summary
    audit_summary = summarize_claim_audit(
        claim_audit_results
    )

    # Step 15: Return complete result
    return {
        "answer": response["answer"],
        "citations": response["citations"],
        "citation_validation": citation_validation,
        "citation_usage": citation_usage,
        "claim_audit": claim_audit_results,
        "audit_summary": audit_summary
    }



if __name__ == "__main__":
    result = run_rag_query(
        query="What is the difference between authentication and authorization?",
        pdf_path="documents/sample.pdf"
    )

    print("\nANSWER:")
    print(result["answer"])

    print("\nCITATIONS:")

    for citation, source in result["citations"].items():
        print(citation, "->", source)

    print("\nCITATION VALIDATION:")
    print(result["citation_validation"])

    print("\nCITATION USAGE:")
    print(result["citation_usage"])

    print("\nCLAIM AUDIT:")
    for claim in result["claim_audit"]:
        print(claim)

    print("\nAUDIT SUMMARY:")
    print(result["audit_summary"])