# from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field
from datetime import datetime
from app.rag.embeddings import calculate_independence_scores
from app.tools.scoring_tool import (
    calculate_business_rating,
    calculate_confidence, 
    calculate_information_quality, 
    calculate_recency_score, 
    calculate_review_weight
)

class ReviewQualityResult(BaseModel):
    specificity: float = Field(ge = 0, le = 1)
    experience: float = Field(ge = 0, le = 1)
    relevance: float = Field(ge = 0, le = 1)
    clarity: float = Field(ge = 0, le = 1)
    aspects: list[str]
    reason: str

class ReviewQualityAgent:
    # def __init__(self, model_name: str = "qwen3:8b") -> None:
    #     model = ChatOllama(
    #         model = model_name,
    #         temperature = 0,
    #     )

    #     self.structured_model = model.with_structured_output(ReviewQualityResult)

    def __init__(self, model_name: str = "amazon.nova-lite-v1:0") -> None:
        model = ChatBedrockConverse(
            model = model_name,
            region_name = "us-east-1",
            temperature = 0,
        )

        self.structured_model = model.with_structured_output(ReviewQualityResult)

    def evaluate(self, review: str, facility_type: str) -> ReviewQualityResult:
        prompt = f"""
You are evaluating the information quality of a customer review.

Facility type: {facility_type}
Review: {review}

Score each field from 0 to 1.

specificity:
Does the review mention concrete details or aspects of the facility?

experience:
Does the review describe an actual customer experience rather than
only generic praise or criticism?

relevance:
Is the review relevant to the facility being reviewed?

clarity:
Is the review understandable and internally coherent?

Also return:

aspects:
A list of concrete topics mentioned in the review.

reason:
A brief explanation of the assigned scores.

You must return every required field:
specificity, experience, relevance, clarity, aspects, and reason.

Do not omit any field.
All four scores must be numeric values between 0 and 1.
"""
        return self.structured_model.invoke(prompt)
    
def evaluate_business_reviews(reviews: list[dict], facility_type: str, agent: ReviewQualityAgent) -> dict:
    review_texts = [review["review"] for review in reviews]
    independence_scores = calculate_independence_scores(review_texts)
    scored_reviews = []

    for review, independence_score in zip(reviews, independence_scores):
        quality_result = agent.evaluate(
            review = review["review"],
            facility_type = facility_type,
        )

        information_quality = calculate_information_quality(
            specificity = quality_result.specificity,
            experience = quality_result.experience,
            relevance = quality_result.relevance,
            clarity = quality_result.clarity,
        )

        published_at = review["published_at"]

        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            )

        recency_score = calculate_recency_score(published_at)

        weight = calculate_review_weight(
            information_quality=information_quality,
            recency_score=recency_score,
            independence_score=independence_score,
        )

        scored_reviews.append(
            {
                **review,
                "information_quality": information_quality,
                "independence_score": independence_score,
                "recency_score": recency_score,
                "weight": weight,
                "aspects": quality_result.aspects,
                "quality_reason": quality_result.reason,
            }
        )

    rating_result = calculate_business_rating(scored_reviews)

    confidence = calculate_confidence(
        rating_result["effective_review_count"]
    )

    return {
        "weighted_rating": rating_result["weighted_rating"],
        "effective_review_count": rating_result[
            "effective_review_count"
        ],
        "confidence": confidence,
        "reviews": scored_reviews,
    }