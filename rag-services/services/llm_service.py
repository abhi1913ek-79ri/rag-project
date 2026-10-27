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


def verify_multiple_claims(claims, source_text):
    """
    Verify multiple claims against the same source
    using a single Gemini API request.
    """

    if not claims:
        return []

    claims_text = "\n".join(
        f"{index}. {claim}"
        for index, claim in enumerate(claims, start=1)
    )

    prompt = f"""
You are a citation support verification assistant.

Verify each claim independently using ONLY the source below.

SOURCE:
{source_text}

CLAIMS:
{claims_text}

For each claim, choose exactly one verdict:

SUPPORTED:
The source directly supports the claim.

CONTRADICTED:
The source directly contradicts the claim.

NOT_SUPPORTED:
The source neither supports nor directly contradicts the claim.

UNCERTAIN:
The source is ambiguous or insufficient to decide.

Return one result for every claim, preserving their order.

Use this exact format:

Claim 1
Verdict: SUPPORTED
Reason: Brief explanation.

Claim 2
Verdict: NOT_SUPPORTED
Reason: Brief explanation.

Do not use information outside the provided source.
Do not omit or merge claims.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text

def parse_multiple_verification_results(response_text, expected_count):
    """
    Parse batch verification text into structured results.
    """

    import re

    pattern = (
        r"Claim\s+(\d+)\s*"
        r"Verdict:\s*(SUPPORTED|CONTRADICTED|NOT_SUPPORTED|UNCERTAIN)\s*"
        r"Reason:\s*(.*?)(?=\n\s*Claim\s+\d+|\Z)"
    )

    matches = re.findall(
        pattern,
        response_text,
        flags=re.IGNORECASE | re.DOTALL
    )

    results = {}

    for claim_number, verdict, reason in matches:
        results[int(claim_number)] = {
            "verdict": verdict.upper(),
            "reason": reason.strip()
        }

    # Validate that every expected claim was returned.
    if len(results) != expected_count:
        raise ValueError(
            f"Expected {expected_count} verification results, "
            f"but parsed {len(results)}."
        )

    return results

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

if __name__ == "__main__":
    source_text = """
    JavaScript is a programming language used to add
    behavior and interactivity to web pages.
    JavaScript was created in 1995.
    """

    claims = [
        "JavaScript adds interactivity to web pages.",
        "JavaScript was created in 1995.",
        "JavaScript was created in 2010."
    ]

    import time

    start = time.perf_counter()

    result = verify_multiple_claims(
        claims=claims,
        source_text=source_text
    )

    print("\nVerification Results:")
    print(result)

    print(
        f"\nTotal verification time: "
        f"{time.perf_counter() - start:.2f} seconds"
    )

    print("\nVerification Results:")
    print(result)

    parsed_results = parse_multiple_verification_results(
        result,
        expected_count=len(claims)
    )

    print("\nParsed Results:")

    for claim_number, verification in parsed_results.items():
        print(f"Claim {claim_number}: {verification}")