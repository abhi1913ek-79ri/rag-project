import time
from sentence_transformers import SentenceTransformer

start = time.time()

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Model load time:", time.time() - start)

start = time.time()

text = "Next.js provides server-side rendering and file-based routing."

embedding = model.encode(text)

print("Embedding time:", time.time() - start)
print("Vector dimensions:", len(embedding))