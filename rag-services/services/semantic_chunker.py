from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib
import re
from services.llm_service import generate_answer

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

def classify_query_intent(query: str) -> str:
    """
    Lightweight intent classification without an API call.
    """

    query_lower = query.lower().strip()

    overview_phrases = [
        "summarize",
        "summary",
        "overview",
        "gist",
        "what is this pdf about",
        "what is this document about",
        "what does this pdf contain",
        "what does this document contain",
        "main topics",
        "key takeaways",
        "brief me about",
        "give me an overview",
        "provide an overview",
        "tell me about this document",
        "tell me about this pdf",
    ]

    if any(
        phrase in query_lower
        for phrase in overview_phrases
    ):
        return "DOCUMENT_OVERVIEW"

    return "SPECIFIC_QUESTION"
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


def validate_citation_references(answer, citation_map):
    # Find references such as [1], [2], [3]
    references = re.findall(r"\[(\d+)\]", answer)

    # Remove duplicate references while preserving order
    references = list(dict.fromkeys(references))

    # Check whether each reference exists in the citation map
    valid_references = []
    invalid_references = []

    for reference in references:
        citation_key = f"[{reference}]"

        if citation_key in citation_map:
            valid_references.append(citation_key)
        else:
            invalid_references.append(citation_key)

    return {
        "valid": len(invalid_references) == 0,
        "valid_references": valid_references,
        "invalid_references": invalid_references
    }


def find_unused_citations(answer, citation_map):
    # Extract citation references used in the answer
    references = re.findall(r"\[(\d+)\]", answer)

    used_references = {
        f"[{reference}]"
        for reference in references
    }

    # Find citations that exist in the map but were not used
    unused_references = []

    for citation_key in citation_map:
        if citation_key not in used_references:
            unused_references.append(citation_key)

    return unused_references

def get_source_text_for_citation(citation_number, results):
    """
    Retrieve the original source text associated with a citation.

    Example:
    citation_number = "[1]"
    results = filtered retrieval results
    """

    try:
        index = int(citation_number.strip("[]")) - 1
    except ValueError:
        return None

    if index < 0 or index >= len(results):
        return None

    return results[index]["chunk"]["text"]

def summarize_verification_results(verification_results):
    summary = {
        "total_claims": len(verification_results),
        "supported": 0,
        "not_supported": 0,
        "uncertain": 0
    }

    for result in verification_results:
        verification_items = result.get("verification", [])

        # A claim without verification results is uncertain.
        if not verification_items:
            summary["uncertain"] += 1
            continue

        verdicts = [
            item.get("verdict", "UNCERTAIN").upper()
            for item in verification_items
        ]

        # A claim is supported if at least one cited source
        # supports it and no cited source contradicts it.
        if "NOT_SUPPORTED" in verdicts:
            summary["not_supported"] += 1

        elif "SUPPORTED" in verdicts:
            summary["supported"] += 1

        else:
            summary["uncertain"] += 1

    return summary

def calculate_citation_usage(answer, citation_map):
    import re

    used_references = set(
        re.findall(r"\[(\d+)\]", answer)
    )

    available_references = {
        key.strip("[]")
        for key in citation_map
    }

    valid_used = used_references & available_references
    unused = available_references - used_references
    invalid = used_references - available_references

    return {
        "total_available": len(available_references),
        "total_used": len(valid_used),
        "unused_citations": [
            f"[{ref}]" for ref in sorted(unused, key=int)
        ],
        "invalid_citations": [
            f"[{ref}]" for ref in sorted(invalid, key=int)
        ]
    }

def compare_cited_source_with_retrieved(
    citation,
    citation_map,
    retrieved_results
):
    cited_metadata = citation_map.get(citation)

    if cited_metadata is None:
        return {
            "citation": citation,
            "found": False,
            "reason": "Citation not found in citation map."
        }

    cited_chunk_id = cited_metadata.get("chunk_id")

    cited_score = cited_metadata.get("similarity")

    comparisons = []

    for result in retrieved_results:
        chunk = result["chunk"]

        comparisons.append({
            "chunk_id": chunk.get("chunk_id"),
            "filename": chunk.get("filename"),
            "page": chunk.get("page"),
            "similarity": result.get("similarity")
        })

    comparisons.sort(
        key=lambda item: item["similarity"] or 0,
        reverse=True
    )

    cited_rank = next(
        (
            index + 1
            for index, item in enumerate(comparisons)
            if item["chunk_id"] == cited_chunk_id
        ),
        None
    )

    return {
        "citation": citation,
        "found": cited_rank is not None,
        "cited_similarity": cited_score,
        "cited_rank": cited_rank,
        "retrieved_chunks": comparisons
    }


def determine_overall_verdict(verification_items):
    if not verification_items:
        return "UNCERTAIN"

    verdicts = [
        item.get("verdict", "UNCERTAIN").upper()
        for item in verification_items
    ]

    allowed_verdicts = {
        "SUPPORTED",
        "NOT_SUPPORTED",
        "CONTRADICTED",
        "UNCERTAIN"
    }

    if any(v not in allowed_verdicts for v in verdicts):
        return "UNCERTAIN"

    # Actual contradiction takes priority.
    if "CONTRADICTED" in verdicts:
        return "CONTRADICTED"

    # At least one source supports the claim.
    if "SUPPORTED" in verdicts:
        return "SUPPORTED"

    # No source supports the claim, but at least one
    # source directly contradicts it: handled above.
    if "NOT_SUPPORTED" in verdicts:
        return "NOT_SUPPORTED"

    return "UNCERTAIN"

def summarize_claim_audit(claim_audit_results):
    summary = {
        "total_claims": len(claim_audit_results),
        "supported": 0,
        "not_supported": 0,
        "uncertain": 0,
        "conflicting": 0
    }

    for result in claim_audit_results:
        verdict = result.get(
            "overall_verdict",
            "UNCERTAIN"
        ).upper()

        if verdict == "SUPPORTED":
            summary["supported"] += 1

        elif verdict == "NOT_SUPPORTED":
            summary["not_supported"] += 1

        elif verdict == "CONFLICTING":
            summary["conflicting"] += 1

        else:
            summary["uncertain"] += 1

    return summary

if __name__ == "__main__":
    test_queries = [
        "Summarize this PDF",
        "What is this PDF about?",
        "Give me the gist of this document",
        "What is JavaScript?",
        "Explain closures"
    ]

    for query in test_queries:
        intent = classify_query_intent(query)
        print(f"Query: {query}")
        print(f"Intent: {intent}\n")


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
