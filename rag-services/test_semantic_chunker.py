from services.pdf_reader import (
    open_pdf,
    extract_page_text,
    split_into_paragraphs
)

from services.semantic_chunker import (
    generate_embeddings,
    calculate_similarities,
    calculate_threshold,
    find_boundaries,
    find_semantic_boundaries,
    create_chunks,
    generate_document_id,
    generate_document_id_from_file,
    generate_chunk_id,
    create_citation_map,
    format_citation,
    retrieve_similar_chunks,
    generate_query_embedding,
    filter_by_similarity,
    has_relevant_chunks,
    create_retrieval_citation,
    create_retrieval_citation_map,
    build_context,
    build_prompt,
    build_response
)

pdf = open_pdf("documents/sample.pdf")

text = extract_page_text(pdf, 1)

paragraphs = split_into_paragraphs(text)

embeddings = generate_embeddings(paragraphs)

similarities = calculate_similarities(embeddings)

threshold = calculate_threshold(similarities)

# boundaries = find_boundaries(
#     similarities,
#     threshold
# )

semantic_boundaries = find_semantic_boundaries(
    similarities,
    min_strength=0.30
)

chunks = create_chunks(
    paragraphs,
    semantic_boundaries,
    document_id="doc_001",
    filename="sample.pdf",
    page=2
)

print("Total paragraphs:", len(paragraphs))
print("Similarities:", [round(x, 4) for x in similarities])
print("Threshold:", round(threshold, 4))
print("Boundaries:", semantic_boundaries)

print("\n--- SEMANTIC CHUNKS ---")

for i, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {i} ---")
    print(chunk)



    print("\n--- LOCAL MINIMA ---")

for i in range(1, len(similarities) - 1):

    if (
        similarities[i] < similarities[i - 1]
        and similarities[i] < similarities[i + 1]
    ):
        print(
            f"Boundary candidate between "
            f"P{i + 1} and P{i + 2} : "
            f"{similarities[i]:.4f}"
        )



print("\n--- FILTERED BOUNDARIES ---")

MIN_STRENGTH = 0.30

for i in range(1, len(similarities) - 1):

    current = similarities[i]
    left = similarities[i - 1]
    right = similarities[i + 1]

    if current < left and current < right:

        neighbor_avg = (left + right) / 2
        strength = neighbor_avg - current

        if strength >= MIN_STRENGTH:
            print(
                f"Boundary between P{i + 1} and P{i + 2} : "
                f"similarity={current:.4f}, "
                f"strength={strength:.4f}"
            )



print("\n--- EDGE CASE TESTS ---")

# Case 1: Empty similarity list
similarities_test = []

print("\nCase 1: Empty similarities")
print("Length:", len(similarities_test))

# Case 2: Only one similarity value
similarities_test = [0.5]

print("\nCase 2: One similarity")
print("Length:", len(similarities_test))

# Case 3: Two similarity values
similarities_test = [0.2, 0.8]

print("\nCase 3: Two similarities")
print("Length:", len(similarities_test))



print("\n--- NEW SEMANTIC BOUNDARIES ---")

semantic_boundaries = find_semantic_boundaries(
    similarities,
    min_strength=0.30
)

print("Semantic boundaries:", semantic_boundaries)


print("\n--- CHUNK METADATA TEST ---")

# document_id = "doc_001"
# filename = "sample.pdf"
# page_number = 2

# for i, chunk in enumerate(chunks, start=1):

#     chunk_data = {
#         "document_id": document_id,
#         "filename": filename,
#         "page": page_number,
#         "chunk_index": i,
#         "text": chunk
#     }

#     print("\n", chunk_data)


# print("\n--- METADATA-AWARE CHUNKS ---")

# for chunk in chunks:
#     print("\n", chunk)

print("\n--- PAGE-WISE METADATA TEST ---")

document_id = generate_document_id_from_file(
    "documents/sample.pdf"
)

next_chunk_index = 1

pages = [
    {
        "page": 1,
        "text": extract_page_text(pdf, 0)
    },
    {
        "page": 2,
        "text": extract_page_text(pdf, 1)
    }
]

for page_data in pages:

    page_number = page_data["page"]
    page_text = page_data["text"]

    page_paragraphs = split_into_paragraphs(page_text)

    page_embeddings = generate_embeddings(page_paragraphs)

    page_similarities = calculate_similarities(
        page_embeddings
    )

    page_boundaries = find_semantic_boundaries(
        page_similarities,
        min_strength=0.30
    )

    page_chunks = create_chunks(
        page_paragraphs,
        page_boundaries,
        document_id=document_id,
        filename="sample.pdf",
        page=page_number,
        start_chunk_index=next_chunk_index
    )

    next_chunk_index += len(page_chunks)

    print(f"\nPage {page_number}")
    print("Chunks:", len(page_chunks))

    for chunk in page_chunks:
        print("\n--- CHUNK ---")
        print("Chunk ID:", chunk["chunk_id"])
        print("Document ID:", chunk["document_id"])
        print("Filename:", chunk["filename"])
        print("Page:", chunk["page"])
        print("Chunk Index:", chunk["chunk_index"])
        print("Text:", chunk["text"])


print("\n--- DOCUMENT ID TEST ---")

filename = "sample.pdf"

document_id = generate_document_id(filename)

print("Filename:", filename)
print("Document ID:", document_id)
print("ID length:", len(document_id))


print("\n--- FILE CONTENT DOCUMENT ID TEST ---")

file_path = "documents/sample.pdf"

file_document_id = generate_document_id_from_file(
    file_path
)

print("File:", file_path)
print("Document ID:", file_document_id)
print("ID length:", len(file_document_id))


print("\n--- CHUNK ID TEST ---")

test_document_id = "abc123"
test_chunk_index = 5

chunk_id = generate_chunk_id(
    test_document_id,
    test_chunk_index
)

print("Document ID:", test_document_id)
print("Chunk Index:", test_chunk_index)
print("Chunk ID:", chunk_id)


print("\n--- CITATION MAP TEST ---")

citation_map = create_citation_map(page_chunks)

for citation, metadata in citation_map.items():
    print(citation, "→", metadata)



print("\n--- FORMATTED CITATION TEST ---")

for citation_number, citation in enumerate(
    citation_map.values(),
    start=1
):
    formatted = format_citation(
        citation_number,
        citation
    )

    print(formatted)



print("\n--- SEMANTIC RETRIEVAL TEST ---")

query = "What is authorization?"

query_embedding = generate_query_embedding(query)

chunk_embeddings = generate_embeddings(
    [chunk["text"] for chunk in page_chunks]
)

results = retrieve_similar_chunks(
    query_embedding,
    chunk_embeddings,
    page_chunks,
    top_k=3
)

print("Query:", query)

for result in results:
    print(
        "Similarity:",
        result["similarity"],
        "| Chunk:",
        result["chunk"]["chunk_id"]
    )

print("\n--- SIMILARITY FILTER TEST ---")

filtered_results = filter_by_similarity(
    results,
    threshold=0.30
)

for result in filtered_results:
    print(
        "Similarity:",
        result["similarity"],
        "| Chunk:",
        result["chunk"]["chunk_id"]
    )

print("\n--- RELEVANT CHUNKS CHECK ---")

if has_relevant_chunks(filtered_results):
    print("Relevant chunks found.")
else:
    print("No relevant chunks found.")

print("\n--- EMPTY RESULT TEST ---")

empty_results = []

if has_relevant_chunks(empty_results):
    print("Relevant chunks found.")
else:
    print("No relevant chunks found.")



print("\n--- RETRIEVAL CITATION TEST ---")

for result in filtered_results:
    citation = create_retrieval_citation(result)

    print(citation)


print("\n--- RETRIEVAL CITATION MAP TEST ---")

retrieval_citation_map = create_retrieval_citation_map(
    filtered_results
)

for citation, metadata in retrieval_citation_map.items():
    print(citation, "→", metadata)


print("\n--- CONTEXT BUILD TEST ---")

context = build_context(filtered_results)

print(context)



print("\n--- PROMPT BUILD TEST ---")

query = "What is authorization?"

prompt = build_prompt(
    query,
    context
)

print(prompt)

print("\n--- FINAL RESPONSE STRUCTURE TEST ---")

response = build_response(
    "Authorization defines what an authenticated user is allowed to do. [1]",
    retrieval_citation_map
)

print(response)