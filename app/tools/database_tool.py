from datetime import datetime 
from langchain.tools import tool
from sqlalchemy import select
from app.database.models import Business, Review
from app.database.session import SessionLocal

@tool
def find_businesses(facility_type: str, location: str) -> list[dict]:
    """Find businesses matching a facility type and location."""
    normalized_facility_type = facility_type.strip().lower()
    normalized_location = location.strip().lower()

    with SessionLocal() as session:
        statement = (
            select(Business)
            .where(
                Business.facility_type.ilike(normalized_facility_type), 
                Business.location.ilike(f"%{normalized_location}%"),
            )
            .order_by(Business.name)
        )

        businesses = session.scalars(statement).all()

    return [
        {
            "id": business.id,
            "name": business.name,
            "facility_type": business.facility_type,
            "location": business.location,
            "price": business.price,
        }
        for business in businesses
    ]

@tool
def get_reviews(business_ids: list[int]):
    """Retrieve reviews for the specified business IDs."""
    if not business_ids:
        return []
    
    with SessionLocal() as session:
        statement = (
            select(Review)
            .where(Review.business_id.in_(business_ids))
            .order_by(
                Review.business_id,
                Review.published_at.desc(),
            )
        )

        reviews = session.scalars(statement).all()

        return [
            {
                "id": review.id,
                "business_id": review.business_id,
                "review": review.review,
                "rating": review.rating,
                "published_at": review.published_at.isoformat(),
                "source": review.source,
            }

            for review in reviews
        ]

@tool
def get_latest_review_date(business_id: int) -> str | None:
    """Return the most recent review date for a business."""
    with SessionLocal() as session:
        statement = (
            select(Review.published_at)
            .where(Review.business_id == business_id)
            .order_by(Review.published_at.desc())
            .limit(1)
        )
        latest_date = session.scalar(statement)

        return latest_date.isoformat() if latest_date else None

@tool
def insert_reviews(reviews: list[dict]):
    """Insert new reviews into the database."""
    if not reviews:
        return []
    
    created_reviews: list[Review] = []

    with SessionLocal() as session:
        try:
            for review_data in reviews:
                business_id = review_data.get("business_id")
                review_text = str(review_data.get("review", "")).strip()
                rating = review_data.get("rating")
                published_at = review_data.get("published_at")
                source = review_data.get("source")

                if not business_id:
                    raise ValueError("Every review must include business_id")

                if not review_text:
                    raise ValueError("Every review must include review_text")

                if rating is None:
                    raise ValueError("Every review must include business_id")
                numeric_rating = float(rating)
                if not (1 <= numeric_rating <= 5):
                    raise ValueError("Review rating must be between 1 and 5")
                
                if not published_at:
                    raise ValueError("Every review must include published_at")
                
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )

                if not isinstance(published_at, datetime):
                    raise ValueError("published_at must be a datetime or ISO datetime string")

                if not source:
                    raise ValueError("Every review must include source")
                
                statement = (
                    select(Business.id).where(Business.id == business_id)
                )
                business_exists = session.scalar(statement)
                if business_exists is None:
                    raise ValueError(f"Business with ID {business_id} does not exist")
                
                review = Review(
                    business_id = int(business_id),
                    review = review_text,
                    rating = numeric_rating,
                    published_at = published_at,
                    source = source,
                )

                session.add(review)
                created_reviews.append(review)

            session.commit()

            for review in created_reviews:
                session.refresh(review)

            return [
                {
                    "id": review.id,
                    "business_id": review.business_id,
                    "review": review.review,
                    "rating": review.rating,
                    "published_at": review.published_at.isoformat(),
                    "source": review.source,
                }

                for review in created_reviews
            ]
        
        except Exception:
            session.rollback()
            raise

@tool
def insert_businesses(
    businesses: list[dict],
) -> list[dict]:
    """Insert newly discovered businesses into the database."""

    if not businesses:
        return []

    inserted_businesses = []

    with SessionLocal() as session:
        for business_data in businesses:
            business = Business(
                name=business_data["name"],
                facility_type=business_data["facility_type"],
                location=business_data["location"],
                price=business_data["price"],
            )

            session.add(business)
            inserted_businesses.append(
                {
                    "model": business,
                    "place_id": business_data["place_id"],
                }
            )

        session.commit()

        results = []

        for item in inserted_businesses:
            business = item["model"]
            session.refresh(business)

            results.append(
                {
                    "id": business.id,
                    "name": business.name,
                    "facility_type": business.facility_type,
                    "location": business.location,
                    "price": business.price,
                    "place_id": item["place_id"],
                }
            )

        return results