from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib


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
    page,
    start_chunk_index=1
):
    chunks = []

    start = 0
    chunk_index = start_chunk_index

    for boundary in boundaries:

        chunk_text = "\n\n".join(
            paragraphs[start:boundary]
        )

        chunks.append({
            "chunk_id": generate_chunk_id(
                            document_id,
                            chunk_index
                        ),
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
            "chunk_id": generate_chunk_id(
                            document_id,
                            chunk_index
                        ),
            "document_id": document_id,
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "text": chunk_text
        })

    return chunks


def generate_document_id(filename):
    document_id = hashlib.sha256(
        filename.encode("utf-8")
    ).hexdigest()

    return document_id

def generate_document_id_from_file(file_path):
    with open(file_path, "rb") as file:
        file_content = file.read()

    document_id = hashlib.sha256(
        file_content
    ).hexdigest()

    return document_id


def generate_chunk_id(document_id, chunk_index):
    return f"{document_id}_chunk_{chunk_index}"


def create_citation(chunk):
    return {
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"],
        "filename": chunk["filename"],
        "page": chunk["page"],
        "chunk_index": chunk["chunk_index"]
    }


def create_citation_map(chunks):
    citation_map = {}

    for index, chunk in enumerate(chunks, start=1):
        citation_key = f"[{index}]"

        citation_map[citation_key] = create_citation(chunk)

    return citation_map


def format_citation(citation_number, citation):
    return {
        "citation": f"[{citation_number}]",
        "source": citation["filename"],
        "page": citation["page"],
        "chunk": citation["chunk_index"],
        "chunk_id": citation["chunk_id"]
    }


def retrieve_similar_chunks(
    query_embedding,
    chunk_embeddings,
    chunks,
    top_k=3
):
    similarities = []

    for i, chunk_embedding in enumerate(chunk_embeddings):
        similarity = cosine_similarity(
            [query_embedding],
            [chunk_embedding]
        )[0][0]

        similarities.append({
            "chunk": chunks[i],
            "similarity": float(similarity)
        })

    similarities.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return similarities[:top_k]


def generate_query_embedding(query):
    return model.encode(query)


def filter_by_similarity(results, threshold=0.30):
    filtered_results = []

    for result in results:
        if result["similarity"] >= threshold:
            filtered_results.append(result)

    return filtered_results


def has_relevant_chunks(results):
    return len(results) > 0

def create_retrieval_citation(result):
    citation = create_citation(result["chunk"])
    citation["similarity"] = result["similarity"]
    return citation\

def create_retrieval_citation_map(results):
    citation_map = {}

    for index, result in enumerate(results, start=1):
        citation_key = f"[{index}]"

        citation_map[citation_key] = create_retrieval_citation(
            result
        )

    return citation_map


def build_context(results):
    context_parts = []

    for index, result in enumerate(results, start=1):
        chunk_text = result["chunk"]["text"]

        context_parts.append(
            f"[{index}] {chunk_text}"
        )

    return "\n\n".join(context_parts)


def build_prompt(query, context):
    prompt = f"""
    You are a document question-answering assistant.

    Answer the user's question using only the provided context.

    If the context does not contain enough information to answer the question, clearly say that the information is not available in the provided documents.

    User Question:
    {query}

    Context:
    {context}

    Answer with citations like [1], [2], etc. based on the provided context.
    """

    return prompt.strip()

def build_response(answer, citation_map):
    return {
        "answer": answer,
        "citations": citation_map
    }

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
