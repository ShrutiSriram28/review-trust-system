# from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field
import ast

class SummaryResult(BaseModel):
    summary: str
    positive_themes: list[str]
    negative_themes: list[str]
    # confidence_statement: str
    preference_assessment: str | None = None
    preference_conflicts: list[str] = Field(default_factory = list)
    limitations: list[str]

def normalize_theme_list(themes: list[str]) -> list[str]:
    normalized: list[str] = []
    for theme in themes:
        if not isinstance(theme, str):
            continue
        theme = theme.strip()

        try:
            parsed = ast.literal_eval(theme)
            if isinstance(parsed, (list, tuple)):
                normalized.extend(
                    str(item).strip() 
                    for item in parsed 
                    if str(item).strip()
                )
                continue
        except (ValueError, SyntaxError):
            pass
        if theme:
            normalized.append(theme)
    
    return normalized

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

    def summarize(self, business_name: str, facility_type: str, weighted_rating: float | None, effective_review_count: float, confidence: str, scored_reviews: list[dict], user_preference: str | None = None, preference_match_score: float | None = None) -> SummaryResult:
        review_evidence = [
            {
                "review": review["review"],
                "rating": review["rating"],
                "weight": review["weight"],
                "aspects": review["aspects"],
                "quality_reason": review["quality_reason"],
                "preference_relevance": review.get("preference_relevance", 0),
                "preference_alignment": review.get("preference_alignment", 0),
            }
            for review in scored_reviews
        ]

        preference_text = user_preference or "No user preference was provided."
        prompt = f"""
You are generating a grounded summary of customer reviews for a local business.

User preference:
{preference_text}

Computed preference match score:
{preference_match_score}

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

preference_assessment:
If the user supplied a preference, give a short direct assessment of whether
the review evidence supports, contradicts, or is mixed with respect to that
preference. If no preference was supplied, return null.

preference_conflicts:
If the user supplied a preference, list concrete recurring evidence that
contradicts the preference. Otherwise return an empty list.

Rules:
- Do not invent claims.
- Do not call any review fake.
- Do not make strong claims when confidence is low.
- Preserve both positive and negative evidence.
- Do not treat one isolated comment as a recurring theme.
- Do not treat a review as supporting the user's preference merely because it discusses the same topic.
- Respect negation and polarity.
- If evidence contradicts the user's preference, say so explicitly.
"""

        result = self.structured_model.invoke(prompt)
        result.positive_themes = normalize_theme_list(result.positive_themes)
        result.negative_themes = normalize_theme_list(result.negative_themes)
        return result