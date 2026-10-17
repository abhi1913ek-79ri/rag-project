import os
import re
from dotenv import load_dotenv
from google import genai
import json


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def generate_answer(prompt):
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text

def verify_citation_support(claim, source_text):
    prompt = f"""
You are a citation support verification assistant.

Determine how the source relates to the claim.

CLAIM:
{claim}

SOURCE:
{source_text}

Choose exactly one verdict:

SUPPORTED:
The source provides evidence that directly supports the claim.

CONTRADICTED:
The source provides evidence that directly contradicts
the claim.

NOT_SUPPORTED:
The source neither supports nor directly contradicts
the claim. Relevant information may be absent.

UNCERTAIN:
The source is ambiguous, unclear, or insufficient
to determine the relationship reliably.

Return your result in this exact format:

Verdict: SUPPORTED
Reason: Brief explanation.

Replace SUPPORTED with the appropriate verdict.
Do not use information outside the provided source.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text


def extract_claims_and_citations(answer):
    prompt = f"""
You are a claim and citation extraction assistant.

Analyze the answer below and extract its factual claims
along with their explicitly associated citations.

ANSWER:
{answer}

INSTRUCTIONS:
1. Extract factual claims from the answer.
2. Split a sentence into separate claims when it contains
   multiple independent factual claims.
3. Associate each claim with the citation references that
   support or are explicitly associated with that claim.
4. Preserve citation references exactly, such as [1], [2].
5. Do not invent citations or claim that a citation supports
   something unless the answer associates it with that claim.
6. If a factual claim has no explicit citation, return an
   empty citations list for that claim.
7. Ignore headings and non-factual conversational text.
8. Do not verify whether the claims are actually true.
9. Return valid JSON only. Do not use Markdown code fences.

Required JSON format:

[
    {{
        "claim": "A factual claim",
        "citations": ["[1]"]
    }},
    {{
        "claim": "Another factual claim",
        "citations": ["[2]"]
    }}
]

If no factual claims exist, return an empty JSON array.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    raw_response = response.text.strip()

    # Handle Markdown code fences if the model returns them.
    raw_response = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw_response,
        flags=re.IGNORECASE
    ).strip()

    try:
        claims = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Failed to parse claim extraction response as JSON."
        ) from error

    if not isinstance(claims, list):
        raise ValueError("Expected a JSON list of claims.")

    for item in claims:
        if not isinstance(item, dict):
            raise ValueError("Each extracted claim must be an object.")

        if not isinstance(item.get("claim"), str):
            raise ValueError("Each claim must contain a string.")

        if not isinstance(item.get("citations"), list):
            raise ValueError(
                "Each claim must contain a citations list."
            )

    return claims



def parse_verification_result(result_text):
    verdict_match = re.search(
        r"Verdict:\s*(SUPPORTED|NOT_SUPPORTED|UNCERTAIN)",
        result_text,
        re.IGNORECASE
    )

    reason_match = re.search(
        r"Reason:\s*(.*)",
        result_text,
        re.IGNORECASE | re.DOTALL
    )

    if not verdict_match:
        raise ValueError(
            "Verification result contains an invalid or missing verdict."
        )

    verdict = verdict_match.group(1).upper()

    reason = (
        reason_match.group(1).strip()
        if reason_match
        else "No explanation provided."
    )

    return {
        "verdict": verdict,
        "reason": reason
    }