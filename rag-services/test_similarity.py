from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

text1 = "Next.js provides server-side rendering."
text2 = "Next.js supports rendering pages on the server."
text3 = "MongoDB stores data in documents."

embeddings = model.encode([text1, text2, text3])

similarity_1_2 = cosine_similarity(
    [embeddings[0]],
    [embeddings[1]]
)[0][0]

similarity_1_3 = cosine_similarity(
    [embeddings[0]],
    [embeddings[2]]
)[0][0]

print("Similarity between Text 1 and Text 2:", similarity_1_2)
print("Similarity between Text 1 and Text 3:", similarity_1_3)