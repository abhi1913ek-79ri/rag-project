from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from services.pdf_reader import (
    open_pdf,
    extract_page_text,
    split_into_paragraphs
)


model = SentenceTransformer("all-MiniLM-L6-v2")

pdf = open_pdf("documents/sample.pdf")

text = extract_page_text(pdf, 0)

paragraphs = split_into_paragraphs(text)

embeddings = model.encode(paragraphs)

similarities = []

print("Total paragraphs:", len(paragraphs))

for i in range(len(paragraphs) - 1):

    similarity = cosine_similarity(
        [embeddings[i]],
        [embeddings[i + 1]]
    )[0][0]

    similarities.append(similarity)

    print(f"P{i + 1} ↔ P{i + 2} : {similarity:.4f}")


print("\n--- Similarity Drops ---")

for i in range(1, len(similarities)):

    drop = similarities[i - 1] - similarities[i]

    print(
        f"Boundary after P{i + 1}: "
        f"drop = {drop:.4f}"
    )


    import numpy as np


mean_similarity = np.mean(similarities)
std_similarity = np.std(similarities)

threshold = mean_similarity - std_similarity

print("\n--- Adaptive Threshold ---")
print("Mean similarity:", round(mean_similarity, 4))
print("Standard deviation:", round(std_similarity, 4))
print("Candidate threshold:", round(threshold, 4))

print("\n--- Boundary Candidates ---")

for i, similarity in enumerate(similarities):

    if similarity < threshold:
        print(
            f"Boundary candidate between "
            f"P{i + 1} and P{i + 2} "
            f"(similarity = {similarity:.4f})"
        )