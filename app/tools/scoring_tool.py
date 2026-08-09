from datetime import datetime, timezone

# Check how recent the latest review is for a given business to determine internet access for reviews
def check_freshness(review_dates: list[datetime]) -> dict:
    if len(review_dates) < 2:
        return {
            "refresh_required": True,
            "median_gap": None,
            "current_gap": None,
        }
    
    review_dates = [
        review_date.replace(tzinfo=timezone.utc)
        if review_date.tzinfo is None
        else review_date.astimezone(timezone.utc)
        for review_date in review_dates
    ]

    review_dates = sorted(review_dates)

    gaps = [
        (review_dates[i] - review_dates[i - 1]).days
        for i in range(1, len(review_dates))
    ]

    gaps.sort()
    n = len(gaps)

    if n % 2 == 1:
        median_gap = gaps[n // 2]
    else: 
        median_gap = (gaps[n // 2 - 1] + gaps[n // 2]) / 2
    
    current_gap = (datetime.now(timezone.utc) - review_dates[-1]).days

    return {
        "refresh_required": current_gap >= median_gap,
        "median_gap": median_gap,
        "current_gap": current_gap,
    }

# Calculating information quality to get review weight
def calculate_information_quality(specificity: float, experience: float, relevance: float, clarity: float) -> float:
    return (specificity + experience + relevance + clarity) / 4

# Recency score for review weight
def calculate_recency_score(published_at: datetime, current_date: datetime | None = None) -> float:
    if current_date is None:
        current_date = datetime.now(timezone.utc)
    
    if published_at.tzinfo is None:
        published_at = published_at.replace(
            tzinfo=timezone.utc
        )
    else:
        published_at = published_at.astimezone(
            timezone.utc
        )

    if current_date is None:
        current_date = datetime.now(timezone.utc)
    elif current_date.tzinfo is None:
        current_date = current_date.replace(
            tzinfo=timezone.utc
        )
    else:
        current_date = current_date.astimezone(
            timezone.utc
        )

    age_days = (current_date - published_at).days

    # 6 months
    if age_days <= 180:
        return 1.0
    
    # 1 year
    if age_days <= 365:
        return 0.8
    
    # 2 years
    if age_days <= 730:
        return 0.5
    
    return 0.0

# Returns the weight for each review 
def calculate_review_weight(information_quality: float, recency_score: float, independence_score: float) -> float:
    return 0.5 * information_quality + 0.3 * recency_score + 0.2 * independence_score

# Returns the overall weighted rating for a given business -> ∑ (Wi * Ri) / ∑ Wi
def calculate_business_rating(reviews: list[dict]) -> dict:
    if not reviews:
        return {
            "weighted_rating": None,
            "effective_review_count": 0.0,
        }
    
    total_weight = sum(review["weight"] for review in reviews)

    if total_weight == 0:
        return {
            "weighted_rating": None,
            "effective_review_count": 0.0,
        }
    
    weighted_rating = sum(
        review["rating"] * review["weight"]
        for review in reviews
    ) / total_weight

    return {
        "weighted_rating": weighted_rating,
        "effective_review_count": total_weight,
    }

# Confidence based on the number of reviews for a given business
def calculate_confidence(effective_review_count: float, total_reviews: int) -> str:
    if total_reviews == 0:
        return "Low"
    effective_ratio = effective_review_count / total_reviews
    if effective_ratio < 0.4:
        return "Low"
    if effective_ratio < 0.7:
        return "Medium"
    return "High"