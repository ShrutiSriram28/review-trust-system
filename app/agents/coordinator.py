from datetime import datetime, timezone

from app.agents.review_quality_agent import (
    ReviewQualityAgent,
    evaluate_business_reviews,
)
from app.agents.summary_agent import SummaryAgent
from app.rag.pinecone import (
    insert_review_vectors,
    retrieve_relevant_reviews,
)
from app.tools.database_tool import (
    find_businesses,
    get_reviews,
    insert_businesses,
    insert_reviews,
)
from app.tools.internet_tool import (
    search_businesses,
    search_recent_reviews,
)
from app.tools.scoring_tool import check_freshness


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


class CoordinatorAgent:
    def __init__(self) -> None:
        self.review_quality_agent = ReviewQualityAgent()
        self.summary_agent = SummaryAgent()

    def recommend(self, facility_type: str, location: str, description: str | None = None, top_k: int = 5, business_limit: int = 5, review_limit: int  = 5) -> list[dict]:
        businesses = find_businesses.invoke(
            {
                "facility_type": facility_type,
                "location": location,
            }
        )
        businesses = businesses[:business_limit]

        if not businesses:
            discovered_businesses = search_businesses(
                facility_type = facility_type,
                location = location,
                business_limit = business_limit,
            )

            if not discovered_businesses:
                return []

            businesses = insert_businesses.invoke(
                {
                    "businesses": discovered_businesses,
                }
            )

        business_ids = [
            business["id"]
            for business in businesses
        ]

        stored_reviews = get_reviews.invoke(
            {
                "business_ids": business_ids,
            }
        )

        reviews_by_business: dict[int, list[dict]] = {
            business_id: []
            for business_id in business_ids
        }

        for review in stored_reviews:
            reviews_by_business[review["business_id"]].append(review)

        for business in businesses:
            business_id = business["id"]
            business_reviews = reviews_by_business[business_id]

            review_dates = [
                parse_datetime(review["published_at"])
                for review in business_reviews
            ]

            if review_dates:
                freshness = check_freshness(review_dates)
                refresh_required = freshness["refresh_required"]
                latest_review_date = max(review_dates)
            else:
                refresh_required = True
                latest_review_date = None

            if not refresh_required:
                continue

            new_reviews = search_recent_reviews(
                business_id = business_id,
                business_name = business["name"],
                location = business["location"],
                published_after = latest_review_date,
                review_limit = review_limit,
                place_id = business.get("place_id"),
            )

            if not new_reviews:
                continue

            reviews_to_insert = [
                {
                    **review,
                    "published_at": (
                        review["published_at"].isoformat()
                    ),
                }
                for review in new_reviews
            ]

            inserted_reviews = insert_reviews.invoke(
                {
                    "reviews": reviews_to_insert,
                }
            )

            reviews_for_pinecone = [
                {
                    **review,
                    "published_at": parse_datetime(
                        review["published_at"]
                    ),
                }
                for review in inserted_reviews
            ]

            insert_review_vectors(reviews_for_pinecone)

        stored_reviews = get_reviews.invoke(
            {
                "business_ids": business_ids,
            }
        )

        all_reviews_by_business: dict[int, list[dict]] = {
            business_id: []
            for business_id in business_ids
        }

        for review in stored_reviews:
            all_reviews_by_business[review["business_id"]].append(review)

        preference_scores: dict[int, float] = {
            business_id: 0.0
            for business_id in business_ids
        }

        if description:
            relevant_reviews = retrieve_relevant_reviews(
                description=description,
                business_ids=business_ids,
            )

            for review in relevant_reviews:
                business_id = review["business_id"]
                similarity = float(review["similarity"])

                preference_scores[business_id] = max(
                    preference_scores[business_id],
                    similarity,
                )

        results: list[dict] = []

        for business in businesses:
            business_id = business["id"]

            # Development limit.
            all_business_reviews = all_reviews_by_business[
                business_id
            ][:review_limit]

            if not all_business_reviews:
                continue

            print(
                f"Scoring {business['name']} "
                f"({len(all_business_reviews)} reviews)"
            )

            scored = evaluate_business_reviews(
                reviews=all_business_reviews,
                facility_type=business["facility_type"],
                agent=self.review_quality_agent,
            )

            print(f"Finished scoring {business['name']}")
            print(f"Generating summary for {business['name']}")

            # The overall summary always uses all scored reviews.
            summary = self.summary_agent.summarize(
                business_name=business["name"],
                facility_type=business["facility_type"],
                weighted_rating=scored["weighted_rating"],
                effective_review_count=scored[
                    "effective_review_count"
                ],
                confidence=scored["confidence"],
                scored_reviews=scored["reviews"],
            )

            confidence_statement = (
                f"The evidence supports this summary with "
                f"{scored['confidence'].lower()} confidence."
            )

            print(f"Finished summary for {business['name']}")

            weighted_rating = scored["weighted_rating"]
            effective_review_count = scored[
                "effective_review_count"
            ]

            results.append(
                {
                    "business_id": business_id,
                    "name": business["name"],
                    "facility_type": business["facility_type"],
                    "location": business["location"],
                    "price": business["price"],
                    "weighted_rating": (
                        round(weighted_rating, 2)
                        if weighted_rating is not None
                        else None
                    ),
                    "effective_review_count": round(effective_review_count, 2),
                    "confidence": scored["confidence"],
                    "preference_match_score": round(preference_scores[business_id], 3),
                    "summary": summary.summary,
                    "positive_themes": summary.positive_themes,
                    "negative_themes": summary.negative_themes,
                    # "confidence_statement": summary.confidence_statement,
                    "confidence_statement": confidence_statement,
                    "limitations": summary.limitations,
                }
            )

        confidence_rank = {
            "High": 3,
            "Medium": 2,
            "Low": 1,
        }

        results.sort(
            key=lambda result: (
                confidence_rank[result["confidence"]],
                result["preference_match_score"],
                result["weighted_rating"] or 0,
            ),
            reverse=True,
        )

        return results[:top_k]