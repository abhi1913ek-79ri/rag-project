import json
import re

from services.llm_service import generate_answer
from services.rag_pipeline import document_cache, process_pdf


summary_cache = {}
MAX_CHUNK_CHARACTERS = 12000


def _strip_json_fence(value):
    return re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        value.strip(),
        flags=re.IGNORECASE,
    ).strip()


def _parse_summary_json(value):
    try:
        parsed = json.loads(_strip_json_fence(value))
    except json.JSONDecodeError as error:
        raise ValueError("The summarization model returned invalid JSON.") from error

    if not isinstance(parsed, dict):
        raise ValueError("The summarization model returned an invalid object.")

    return parsed


def _source_reference(chunk, filename):
    return {
        "filename": filename,
        "page": chunk["page"],
        "chunk_id": chunk["chunk_id"],
        "text": chunk["text"],
    }


def _summarize_chunk(chunk, filename, text=None):
    source_text = chunk["text"] if text is None else text
    prompt = f"""
You are a document summarization assistant. Summarize ONLY the source below.
Do not use outside knowledge, infer missing facts, correct spelling, or invent
details. Preserve exact names, project titles, technologies, dates, and numbers.
Return plain text with the important facts from this source section.

SOURCE FILE: {filename}
SOURCE PAGE: {chunk["page"]}
SOURCE CHUNK: {chunk["chunk_id"]}

SOURCE TEXT:
{source_text}
""".strip()
    return generate_answer(prompt).strip()


def _build_final_summary(filename, intermediate_summaries):
    source_text = "\n\n".join(
        f"SOURCE {index}\n"
        f"Filename: {item['filename']}\n"
        f"Page: {item['page']}\n"
        f"Chunk ID: {item['chunk_id']}\n"
        f"Summary: {item['summary']}"
        for index, item in enumerate(intermediate_summaries, start=1)
    )
    prompt = f"""
You are a strict, document-grounded summarization assistant.
Create a complete structured summary of ONLY the provided source summaries.
Never add external knowledge or inferred facts. Preserve original spelling for
names, project titles, technologies, organizations, dates, and numbers.
If a requested detail is unavailable, say it is not available in the document.
Every item must include source_refs containing only SOURCE page/chunk pairs
that support it. Do not invent references.

Return valid JSON only, with this exact shape:
{{
  "overview": "Document purpose and main information.",
  "short_summary": "A concise overview.",
  "detailed_summary": [
    {{"heading": "Section or topic", "summary": "Grounded explanation.", "source_refs": [{{"page": 1, "chunk_id": "id"}}]}}
  ],
  "key_points": [
    {{"point": "Important grounded point.", "source_refs": [{{"page": 1, "chunk_id": "id"}}]}}
  ],
  "entities": [
    {{"name": "Exact name or term", "type": "PERSON|PROJECT|TECHNOLOGY|ORGANIZATION|DATE|OTHER", "context": "How it appears in the document.", "source_refs": [{{"page": 1, "chunk_id": "id"}}]}}
  ]
}}

SOURCE FILE: {filename}

{source_text}
""".strip()
    return _parse_summary_json(generate_answer(prompt))


def _attach_sources(summary, sources):
    source_lookup = {
        (source["page"], source["chunk_id"]): source
        for source in sources
    }

    def expand_refs(item):
        refs = []
        for ref in item.get("source_refs", []):
            source = source_lookup.get((ref.get("page"), ref.get("chunk_id")))
            if source:
                refs.append(source)
        item["source_refs"] = refs
        return item

    for key in ("detailed_summary", "key_points", "entities"):
        summary[key] = [
            expand_refs(item)
            for item in summary.get(key, [])
            if isinstance(item, dict)
        ]
    summary["source_references"] = sources
    return summary


def summarize_document(document_id, pdf_path, filename, force=False):
    if not force and document_id in summary_cache:
        return summary_cache[document_id]

    if document_id in document_cache:
        chunks = document_cache[document_id]["chunks"]
    else:
        chunks = process_pdf(pdf_path)
        document_cache[document_id] = {"chunks": chunks}

    if not chunks:
        raise ValueError("No readable text was found in the PDF.")

    intermediate_summaries = []
    for chunk in chunks:
        text = chunk["text"]
        parts = [
            text[index:index + MAX_CHUNK_CHARACTERS]
            for index in range(0, len(text), MAX_CHUNK_CHARACTERS)
        ]
        for part in parts:
            summarized = _summarize_chunk(chunk, filename, part)
            intermediate_summaries.append({
                "filename": filename,
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"],
                "summary": summarized,
            })

    summary = _build_final_summary(filename, intermediate_summaries)
    sources = [
        _source_reference(chunk, filename)
        for chunk in chunks
    ]
    summary = _attach_sources(summary, sources)
    summary["document_id"] = document_id
    summary["filename"] = filename
    summary_cache[document_id] = summary
    return summary


def invalidate_summary(document_id):
    summary_cache.pop(document_id, None)
