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
    validate_location,
)
from app.tools.scoring_tool import check_freshness


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)

def calculate_preference_match(scored_reviews: list[dict], similarity_by_review_id: dict[int, float]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    total_preference_relevance = 0.0

    for review in scored_reviews:
        review_id = int(review["id"])

        if review_id not in similarity_by_review_id:
            continue

        semantic_similarity = max(0.0, float(similarity_by_review_id[review_id]))

        preference_relevance = float(review.get("preference_relevance", 0.0))
        preference_alignment = float(review.get("preference_alignment", 0.0))

        base_weight = semantic_similarity * float(review["weight"])

        denominator += base_weight

        total_preference_relevance += base_weight * preference_relevance

        numerator += base_weight * preference_relevance * preference_alignment

        if denominator == 0 or total_preference_relevance == 0:
            return None
        
        signed_score = numerator / denominator

        signed_score = max(-1, min(1, signed_score))

        return 0.5 + 0.5 * signed_score

class CoordinatorAgent:
    def __init__(self) -> None:
        self.review_quality_agent = ReviewQualityAgent()
        self.summary_agent = SummaryAgent()

    def recommend(self, facility_type: str, location: str, description: str | None = None, top_k: int = 5, business_limit: int = 5, review_limit: int  = 5) -> list[dict]:
        # description = description.strip() if description else None
        businesses = find_businesses.invoke(
            {
                "facility_type": facility_type,
                "location": location,
            }
        )

        if len(businesses) < business_limit:
            validate_location(location)

            businesses_needed = business_limit - len(businesses)
            existing_business_names = {
                business["name"].strip().lower()
                for business in businesses
            }
            
            discovered_businesses = search_businesses(
                facility_type = facility_type,
                location = location,
                business_limit = businesses_needed,
                excluded_business_names = existing_business_names,
            )

            if discovered_businesses:
                inserted_businesses = insert_businesses.invoke(
                    {
                        "businesses": discovered_businesses,
                    }
                )

                businesses.extend(inserted_businesses)

        businesses = businesses[:business_limit]

        if not businesses:
            return []

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

            reviews_needed = max(0, review_limit - len(business_reviews))

            if reviews_needed == 0 and not refresh_required:
                continue

            existing_review_dates = {
                parse_datetime(review["published_at"]).isoformat()
                for review in business_reviews
            }

            new_reviews = search_recent_reviews(
                business_id = business_id,
                business_name = business["name"],
                location = business["location"],
                published_after = latest_review_date if reviews_needed == 0 else None,
                review_limit = review_limit if reviews_needed == 0 else reviews_needed,
                place_id = business.get("place_id"),
                excluded_published_at = existing_review_dates,
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

        # preference_scores: dict[int, float] = {
        #     business_id: 0.0
        #     for business_id in business_ids
        # }

        # if description:
        #     relevant_reviews = retrieve_relevant_reviews(
        #         description=description,
        #         business_ids=business_ids,
        #     )

        #     for review in relevant_reviews:
        #         business_id = review["business_id"]
        #         similarity = float(review["similarity"])

        #         preference_scores[business_id] = max(
        #             preference_scores[business_id],
        #             similarity,
        #         )

        similarity_by_review_id: dict[int, float] = {}
        description = description.strip() if description else None

        if description:
            relevant_reviews = retrieve_relevant_reviews(
                description = description,
                business_ids = business_ids,
                top_k_per_business = review_limit,
            )

            similarity_by_review_id = {
                int(review["id"]): float(review["similarity"])
                for review in relevant_reviews
            }

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
                user_preference = description,
            )

            preference_match_score = None

            if description:
                preference_match_score = calculate_preference_match(
                    scored_reviews = scored["reviews"],
                    similarity_by_review_id = similarity_by_review_id,
                )

            print(f"Finished scoring {business['name']}")
            print(f"Generating summary for {business['name']}")

            # The overall summary always uses all scored reviews.
            summary = self.summary_agent.summarize(
                business_name = business["name"],
                facility_type = business["facility_type"],
                weighted_rating = scored["weighted_rating"],
                effective_review_count = scored["effective_review_count"],
                confidence = scored["confidence"],
                scored_reviews = scored["reviews"],
                user_preference = description,
                preference_match_score = preference_match_score,
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
                    "preference_match_score": (
                        round(preference_match_score, 3)
                        if preference_match_score is not None
                        else None
                    ),
                    "summary": summary.summary,
                    "positive_themes": summary.positive_themes,
                    "negative_themes": summary.negative_themes,
                    # "confidence_statement": summary.confidence_statement,
                    "confidence_statement": confidence_statement,
                    "limitations": summary.limitations,
                    "preference_assessment": summary.preference_assessment,
                    "preference_conflicts": summary.preference_conflicts,
                }
            )

        confidence_rank = {
            "High": 3,
            "Medium": 2,
            "Low": 1,
        }

        if description:  
            results.sort(
                key=lambda result: (
                    (
                        result["preference_match_score"]
                        if result["preference_match_score"] is not None
                        else -1.0
                    ),
                    confidence_rank[result["confidence"]],
                    result["weighted_rating"] or 0,
                    result["effective_review_count"],
                ),
                reverse=True,
            )
        else:
            results.sort(
                key=lambda result: (
                    confidence_rank[result["confidence"]],
                    result["weighted_rating"] or 0,
                    result["effective_review_count"],
                ),
                reverse=True,
            )

        return results[:top_k]