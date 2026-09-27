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
    create_chunks
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


print("\n--- METADATA-AWARE CHUNKS ---")

for chunk in chunks:
    print("\n", chunk)