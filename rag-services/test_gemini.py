from services.semantic_chunker import build_prompt
from services.llm_service import generate_answer


query = "What is authorization?"

context = """
[1] Authorization means checking what the authenticated user
is allowed to access.

[2] Authentication verifies the identity of a user,
while authorization determines what that user is allowed to do.
"""


prompt = build_prompt(query, context)

print("Generated Prompt:")
print(prompt)

print("\n" + "=" * 60 + "\n")

answer = generate_answer(prompt)

print("Gemini Answer:")
print(answer)