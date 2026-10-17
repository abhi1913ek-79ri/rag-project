from services.pdf_reader import (
    open_pdf,
    extract_all_pages,
    split_into_paragraphs
)

from services.semantic_chunker import (
    generate_embeddings,
    generate_query_embedding,
    calculate_similarities,
    find_semantic_boundaries,
    create_chunks,
    generate_document_id_from_file,
    retrieve_similar_chunks,
    filter_by_similarity,
    build_context,
    create_retrieval_citation_map,
    build_prompt,
    build_response,
    validate_citation_references,
    find_unused_citations,
    get_source_text_for_citation,
    summarize_verification_results,
    calculate_citation_usage,
    compare_cited_source_with_retrieved,
    determine_overall_verdict,
    summarize_claim_audit
)

from services.llm_service import (
    generate_answer,
    verify_citation_support,
    extract_claims_and_citations,
    parse_verification_result
)


# PDF path
PDF_PATH = "documents/sample.pdf"


# Step 1: Open PDF
document = open_pdf(PDF_PATH)

# Step 2: Extract text page-wise
pages = extract_all_pages(document)

# Step 3: Generate document ID from file content
document_id = generate_document_id_from_file(PDF_PATH)

all_chunks = []
next_chunk_index = 1


# Step 4: Process each page
for page_data in pages:

    page_number = page_data["page"]
    text = page_data["text"]

    paragraphs = split_into_paragraphs(text)

    if not paragraphs:
        continue

    # Generate paragraph embeddings
    embeddings = generate_embeddings(paragraphs)

    # Calculate similarities between adjacent paragraphs
    similarities = calculate_similarities(embeddings)

    # Find semantic boundaries
    boundaries = find_semantic_boundaries(similarities)

    # Create chunks with metadata
    chunks = create_chunks(
        paragraphs=paragraphs,
        boundaries=boundaries,
        document_id=document_id,
        filename="sample.pdf",
        page=page_number,
        start_chunk_index=next_chunk_index
    )

    all_chunks.extend(chunks)

    next_chunk_index += len(chunks)


document.close()


# Step 5: Display results
print("Total pages:", len(pages))
print("Total chunks:", len(all_chunks))

for chunk in all_chunks:
    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Page:", chunk["page"])
    print("Chunk index:", chunk["chunk_index"])
    print("Text preview:", chunk["text"][:200])


# Step 6: Prepare embeddings for all generated chunks

chunk_texts = [
    chunk["text"]
    for chunk in all_chunks
]

chunk_embeddings = generate_embeddings(chunk_texts)


# Step 7: Embed the user's query

query = "What is the difference between authentication and authorization?"

query_embedding = generate_query_embedding(query)


# Step 8: Retrieve the top 3 relevant chunks

results = retrieve_similar_chunks(
    query_embedding=query_embedding,
    chunk_embeddings=chunk_embeddings,
    chunks=all_chunks,
    top_k=3
)


# Step 9: Filter results by similarity

filtered_results = filter_by_similarity(
    results,
    threshold=0.30
)


# Step 10: Display retrieved chunks

print("\nQuery:", query)
print("Retrieved chunks:", len(filtered_results))

for result in filtered_results:
    chunk = result["chunk"]

    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Page:", chunk["page"])
    print("Chunk index:", chunk["chunk_index"])
    print("Similarity:", round(result["similarity"], 4))
    print("Text:", chunk["text"][:300])


# Step 13C: Build context from retrieved chunks
context = build_context(filtered_results)

print("\n" + "=" * 60)
print("GENERATED CONTEXT")
print("=" * 60)
print(context)


# Create citation mapping
citation_map = create_retrieval_citation_map(filtered_results)

print("\n" + "=" * 60)
print("CITATION MAP")
print("=" * 60)

for citation, source in citation_map.items():
    print(citation, "->", source)

# Step 13D: Generate final answer using Gemini

# Build the prompt using the retrieved context
prompt = build_prompt(query, context)

# Generate answer using the LLM
answer = generate_answer(prompt)

# Combine answer and source citations
response = build_response(answer, citation_map)

print("\n" + "=" * 60)
print("FINAL RAG RESPONSE")
print("=" * 60)

print("\nAnswer:")
print(response["answer"])

print("\nCitations:")
for citation, source in response["citations"].items():
    print(citation, "->", source)


citation_usage = calculate_citation_usage(
    answer,
    citation_map
)

print("\nCITATION USAGE SUMMARY:")
print(citation_usage)


# Step 13E.1: Validate citation references
validation = validate_citation_references(
    answer=response["answer"],
    citation_map=response["citations"]
)

print("\n" + "=" * 60)
print("CITATION REFERENCE VALIDATION")
print("=" * 60)

print("Valid:", validation["valid"])
print("Valid references:", validation["valid_references"])
print("Invalid references:", validation["invalid_references"])


# Step 13E.2: Test invalid citation detection

test_answer = """
Authentication verifies identity [1].
Authorization controls permissions [99].
"""

test_validation = validate_citation_references(
    answer=test_answer,
    citation_map=response["citations"]
)

print("\n" + "=" * 60)
print("INVALID CITATION TEST")
print("=" * 60)

print("Valid:", test_validation["valid"])
print("Valid references:", test_validation["valid_references"])
print("Invalid references:", test_validation["invalid_references"])

# Step 13E.3: Detect unused citations

unused_citations = find_unused_citations(
    answer=response["answer"],
    citation_map=response["citations"]
)

print("\n" + "=" * 60)
print("UNUSED CITATION TEST")
print("=" * 60)

print("Unused citations:", unused_citations)

# Step 13E.6: Citation support verification test cases

verification_tests = [
    {
        "claim": "Authentication verifies a user's identity.",
        "source": (
            "Authentication means verifying the identity "
            "of the user."
        ),
        "expected_verdict": "SUPPORTED"
    },
    {
        "claim": "Authentication encrypts passwords using AES-256.",
        "source": (
            "Authentication means verifying the identity "
            "of the user."
        ),
        "expected_verdict": "NOT_SUPPORTED"
    },
    {
        "claim": "The authentication system uses a particular "
                 "encryption algorithm.",
        "source": (
            "The document describes authentication but does "
            "not specify the encryption algorithm."
        ),
        "expected_verdict": "UNCERTAIN"
    }
]

print("\n" + "=" * 60)
print("CITATION VERIFICATION TEST CASES")
print("=" * 60)

for index, test in enumerate(verification_tests, start=1):
    print(f"\nTest Case {index}")
    print("Claim:", test["claim"])
    print("Source:", test["source"])
    print("Expected:", test["expected_verdict"])



# Step 13E.8: Test citation support verification

test_claim = "Authentication verifies a user's identity."

test_source = (
    "Authentication means verifying the identity "
    "of the user."
)

verification_result = verify_citation_support(
    claim=test_claim,
    source_text=test_source
)

print("\n" + "=" * 60)
print("CITATION SUPPORT VERIFICATION")
print("=" * 60)

print("Claim:", test_claim)
print("Source:", test_source)
print("Verification result:")
print(verification_result)


# Step 13E.9: Test unsupported claim

test_claim = "Authentication encrypts passwords using AES-256."

test_source = (
    "Authentication means verifying the identity "
    "of the user."
)

verification_result = verify_citation_support(
    claim=test_claim,
    source_text=test_source
)

print("\n" + "=" * 60)
print("UNSUPPORTED CLAIM VERIFICATION")
print("=" * 60)

print("Claim:", test_claim)
print("Source:", test_source)
print("Verification result:")
print(verification_result)

source_text = get_source_text_for_citation(
    "[1]",
    filtered_results
)

print("\nSOURCE TEXT FOR [1]:")
print(source_text)

print("\nINVALID CITATION:")
print(
    get_source_text_for_citation(
        "[99]",
        filtered_results
    )
)


# Claim that we want to verify
claim = "Authentication verifies a user's identity."

# Retrieve the actual source associated with citation [1]
source_text = get_source_text_for_citation(
    "[1]",
    filtered_results
)

if source_text:
    verification = verify_citation_support(
        claim,
        source_text
    )

    print("\nCLAIM:")
    print(claim)

    print("\nSOURCE TEXT:")
    print(source_text)

    print("\nVERIFICATION RESULT:")
    print(verification)

else:
    print("Source not found for citation [1].")


extracted_claims = extract_claims_and_citations(answer)

print("\nEXTRACTED CLAIMS AND CITATIONS:")

for item in extracted_claims:
    print(item)



print("\nCLAIM VERIFICATION RESULTS:")

for item in extracted_claims:
    claim = item["claim"]
    citations = item["citations"]

    print("\n" + "=" * 60)
    print("CLAIM:", claim)

    if not citations:
        print("VERDICT: UNCERTAIN")
        print("REASON: No citation was provided for this claim.")
        continue

    for citation in citations:
        source_text = get_source_text_for_citation(
            citation,
            filtered_results
        )

        print("\nCITATION:", citation)

        if source_text is None:
            print("VERDICT: UNCERTAIN")
            print("REASON: Corresponding source was not found.")
            continue

        print("SOURCE TEXT:", source_text)

        verification = verify_citation_support(
            claim,
            source_text
        )

        print("VERIFICATION:", verification)


sample_result = """
Verdict: SUPPORTED
Reason: The source explicitly supports the claim.
"""

parsed_result = parse_verification_result(sample_result)

print("\nSTRUCTURED VERIFICATION RESULT:")
print(parsed_result)


verification_results = []

for item in extracted_claims:
    claim = item["claim"]
    citations = item["citations"]

    claim_result = {
        "claim": claim,
        "citations": citations,
        "verification": []
    }

    # No citation provided
    if not citations:
        claim_result["verification"].append({
            "citation": None,
            "verdict": "UNCERTAIN",
            "reason": "No citation was provided."
        })

        verification_results.append(claim_result)
        continue

    # Verify claim against each cited source
    for citation in citations:

        source_text = get_source_text_for_citation(
            citation,
            filtered_results
        )

        if source_text is None:
            claim_result["verification"].append({
                "citation": citation,
                "verdict": "UNCERTAIN",
                "reason": "Corresponding source was not found."
            })

            continue

        raw_verification = verify_citation_support(
            claim,
            source_text
        )

        parsed_verification = parse_verification_result(
            raw_verification
        )

        citation_metadata = citation_map.get(citation, {})
        claim_result["verification"].append({
            "citation": citation,
            "source": {
                "filename": citation_metadata.get("filename"),
                "page": citation_metadata.get("page"),
                "chunk_id": citation_metadata.get("chunk_id"),
                "chunk_index": citation_metadata.get("chunk_index")
            },
            "verdict": parsed_verification["verdict"],
            "reason": parsed_verification["reason"]
        })

    verification_results.append(claim_result)


print("\n" + "=" * 60)
print("COMPLETE CLAIM VERIFICATION RESULTS")
print("=" * 60)

for result in verification_results:
    print(result)



summary = summarize_verification_results(
    verification_results
)

print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)

print("Total Claims:", summary["total_claims"])
print("Supported:", summary["supported"])
print("Not Supported:", summary["not_supported"])
print("Uncertain:", summary["uncertain"])


test_citation = extracted_claims[0]["citations"][0]

comparison = compare_cited_source_with_retrieved(
    test_citation,
    citation_map,
    filtered_results
)

print("\nCITATION COMPARISON:")
print(comparison)

claim_audit_results = []

for claim_result in verification_results:
    audited_claim = {
        "claim": claim_result["claim"],
        "citations": claim_result["citations"],
        "verification": []
    }

    for verification in claim_result["verification"]:
        citation = verification["citation"]

        audit_item = {
            "citation": citation,
            "verdict": verification["verdict"],
            "reason": verification["reason"],
            "source": verification.get("source"),
            "retrieval_comparison": None
        }

        if citation is not None:
            comparison = compare_cited_source_with_retrieved(
                citation,
                citation_map,
                filtered_results
            )

            audit_item["retrieval_comparison"] = {
                "found": comparison["found"],
                "similarity": comparison.get("cited_similarity"),
                "rank": comparison.get("cited_rank")
            }

        audited_claim["verification"].append(audit_item)

    audited_claim["overall_verdict"] = determine_overall_verdict(
        audited_claim["verification"]
    )
    claim_audit_results.append(audited_claim)


print("\n" + "=" * 60)
print("CLAIM AUDIT RESULTS")
print("=" * 60)

for result in claim_audit_results:
    print(result)

    test_cases = [
    ["SUPPORTED", "SUPPORTED"],
    ["SUPPORTED", "UNCERTAIN"],
    ["NOT_SUPPORTED", "UNCERTAIN"],
    ["NOT_SUPPORTED", "SUPPORTED"],
    ["UNCERTAIN", "UNCERTAIN"]
]

for verdicts in test_cases:
    items = [
        {"verdict": verdict}
        for verdict in verdicts
    ]

    print(
        verdicts,
        "->",
        determine_overall_verdict(items)
    )


audit_summary = summarize_claim_audit(
    claim_audit_results
)

print("\n" + "=" * 60)
print("FINAL CLAIM AUDIT SUMMARY")
print("=" * 60)

print("Total Claims:", audit_summary["total_claims"])
print("Supported:", audit_summary["supported"])
print("Not Supported:", audit_summary["not_supported"])
print("Uncertain:", audit_summary["uncertain"])
print("Conflicting:", audit_summary["conflicting"])


print("\n" + "=" * 60)
print("CONTRADICTION DETECTION TEST")
print("=" * 60)

claim = "Authorization controls what resources a user can access."

source_text = """
The document explicitly states that authorization does not
control or determine which resources a user can access.
"""

result = verify_citation_support(claim, source_text)

print("Claim:", claim)
print("Source:", source_text)
print("Verification result:")
print(result)