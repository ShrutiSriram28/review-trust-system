import os
from dotenv import load_dotenv
from pinecone import Pinecone
from app.rag.embeddings import embedding_model

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing from .env")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing from .env")

pinecone_client = Pinecone(api_key = PINECONE_API_KEY)
index = pinecone_client.Index(PINECONE_INDEX_NAME)

def insert_review_vectors(reviews: list[dict]) -> None:
    if not reviews:
        return
    
    texts = [review["review"] for review in reviews]
    embeddings = embedding_model.embed_documents(texts)

    vectors = []

    for review, embedding in zip(reviews, embeddings):
        vectors.append(
            {
                "id": str(review["id"]),
                "values": embedding,
                "metadata": {
                    "review_id": review["id"],
                    "business_id": review["business_id"],
                    "review": review["review"],
                    "rating": review["rating"],
                    "published_at": review["published_at"].isoformat(),
                },
            }
        )
    
    index.upsert(vectors = vectors)

def retrieve_relevant_reviews(description: str, business_ids: list[int], top_k: int = 20) -> list[dict]:
    if not description or not business_ids:
        return []
    
    query_embedding = embedding_model.embed_query(description)
    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter={
            "business_id": {
                "$in": business_ids,
            }
        },
    )

    return [
        {
            "id": int(match.metadata["review_id"]),
            "business_id": int(match.metadata["business_id"]),
            "review": match.metadata["review"],
            "rating": float(match.metadata["rating"]),
            "published_at": match.metadata["published_at"],
            "similarity": match.score,
        }
        for match in result.matches
    ]