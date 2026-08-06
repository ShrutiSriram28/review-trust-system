import math
# from langchain_ollama import OllamaEmbeddings
from langchain_aws import BedrockEmbeddings

# embedding_model = OllamaEmbeddings(model = 'nomic-embed-text')
embedding_model  = BedrockEmbeddings(
    model_id = "amazon.titan-embed-text-v2:0",
    region_name = "us-east-1",
    # credentials_profile_name = "iam-user",
    model_kwargs = {
        "dimensions": 512,
        "normalize": True,
    }
)

def cosine_similarity(first_embedding: list[float], second_embedding: list[float]) -> float:
    dot_product = sum(
        first * second 
        for first, second in zip(first_embedding, second_embedding)
    )

    first_magnitude = math.sqrt(
        sum(value * value for value in first_embedding)
    )

    second_magnitude = math.sqrt(
        sum(value * value for value in second_embedding)
    )

    if first_magnitude == 0 or second_magnitude == 0:
        return 0.0
    
    return dot_product / (first_magnitude * second_magnitude)

# D_i​ = 1 − max_(j!=i) ​cos(e_i​, e_j​)
# ​cos(e_i​, e_j​) = x => similarity is x
# We want reviews to be independent. So (1 - x)
def calculate_independence_scores(reviews: list[str]) -> list[float]:
    if not reviews:
        return []
    
    if len(reviews) == 1:
        return [1.0]
    
    embeddings = embedding_model.embed_documents(reviews)
    independence_scores: list[float] = []

    for current_index, current_embedding in enumerate(embeddings):
        highest_similarity = 0.0

        for other_index, other_embedding in enumerate(embeddings):
            if current_index == other_index:
                continue

            similarity = cosine_similarity(
                current_embedding,
                other_embedding,
            )

            highest_similarity = max(
                highest_similarity,
                similarity,
            )

        independence_score = 1 - highest_similarity
        independence_scores.append(independence_score)

    return independence_scores