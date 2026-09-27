from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embeddings(paragraphs):
    return model.encode(paragraphs)

def calculate_similarities(embeddings):
    similarities = []

    for i in range(len(embeddings) - 1):
        similarity = cosine_similarity(
            [embeddings[i]],
            [embeddings[i + 1]]
        )[0][0]

        similarities.append(similarity)

    return similarities


def calculate_threshold(similarities):
    if not similarities:
        return 0

    mean_similarity = np.mean(similarities)
    std_similarity = np.std(similarities)

    threshold = mean_similarity - std_similarity

    return threshold

def find_boundaries(similarities, threshold):
    boundaries = []

    for i, similarity in enumerate(similarities):
        if similarity < threshold:
            boundaries.append(i + 1)

    return boundaries

def find_semantic_boundaries(similarities, min_strength=0.30):
    boundaries = []

    for i in range(1, len(similarities) - 1):

        current = similarities[i]
        left = similarities[i - 1]
        right = similarities[i + 1]

        # Check for local minimum
        if current < left and current < right:

            neighbor_avg = (left + right) / 2

            strength = neighbor_avg - current

            # Keep only meaningful boundaries
            if strength >= min_strength:
                boundaries.append(i + 1)

    return boundaries


def create_chunks(
    paragraphs,
    boundaries,
    document_id,
    filename,
    page
):
    chunks = []

    start = 0
    chunk_index = 1

    for boundary in boundaries:

        chunk_text = "\n\n".join(
            paragraphs[start:boundary]
        )

        chunks.append({
            "document_id": document_id,
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "text": chunk_text
        })

        chunk_index += 1
        start = boundary

    if start < len(paragraphs):

        chunk_text = "\n\n".join(
            paragraphs[start:]
        )

        chunks.append({
            "document_id": document_id,
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "text": chunk_text
        })

    return chunks


""" 
Paragraphs
   ↓
generate_embeddings()
   ↓
Embeddings
   ↓
calculate_similarities()
   ↓
Similarities
   ↓
calculate_threshold()
   ↓
Threshold
   ↓
find_boundaries()
   ↓
Boundaries
   ↓
create_chunks()
   ↓
Semantic Chunks
"""
