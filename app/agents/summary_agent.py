# from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel

class SummaryResult(BaseModel):
    summary: str
    positive_themes: list[str]
    negative_themes: list[str]
    # confidence_statement: str
    limitations: list[str]

class SummaryAgent:
    # def __init__(self, model_name: str = "qwen3:8b") -> None:
    #     model = ChatOllama(
    #         model = model_name,
    #         temperature = 0,
    #     )

    #     self.structured_model = model.with_structured_output(SummaryResult)

    def __init__(self, model_name: str = "amazon.nova-micro-v1:0") -> None:
        model = ChatBedrockConverse(
            model = model_name,
            region_name = "us-east-1",
            temperature = 0,
        )

        self.structured_model = model.with_structured_output(SummaryResult)

    def summarize(self, business_name: str, facility_type: str, weighted_rating: float | None, effective_review_count: float, confidence: str, scored_reviews: list[dict]) -> SummaryResult:
        review_evidence = [
            {
                "review": review["review"],
                "rating": review["rating"],
                "weight": review["weight"],
                "aspects": review["aspects"],
                "quality_reason": review["quality_reason"],
            }
            for review in scored_reviews
        ]

        prompt = f"""
You are generating a grounded summary of customer reviews for a local business.

Business name:
{business_name}

Facility type:
{facility_type}

Weighted rating:
{weighted_rating}

Effective review count:
{effective_review_count}

Review evidence:
{review_evidence}

Return:

summary:
A short overall summary based only on the supplied review evidence.

positive_themes:
A list of recurring positive themes.

negative_themes:
A list of recurring negative themes.

confidence_statement:
A short sentence explaining how strongly the evidence supports the summary.

limitations:
A list of important limitations, such as low review volume, conflicting reviews, duplicate wording, or missing evidence.

Rules:
- Do not invent claims.
- Do not call any review fake.
- Do not make strong claims when confidence is low.
- Preserve both positive and negative evidence.
- Do not treat one isolated comment as a recurring theme.
"""

        return self.structured_model.invoke(prompt)