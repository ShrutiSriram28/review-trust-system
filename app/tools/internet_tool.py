import os 
from datetime import datetime 
import serpapi
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY is missing from .env")

client = serpapi.Client(api_key=SERPAPI_API_KEY)

def _find_place_id(business_name: str, location: str) -> str:
    results = client.search(
        {
            "engine": "google_maps",
            "q": f"{business_name}, {location}",
            "type": "search",
            "hl": "en",
        }
    )

    if "error" in results:
        raise RuntimeError(results["error"])
    
    candidates = results.get("local_results", [])

    if not candidates and results.get("place_results"):
        candidates = [results["place_results"]]

    if not candidates:
        raise ValueError(f"Could not find Google Maps listing for {business_name} in {location}")
    
    place_id = candidates[0].get("place_id")
    if not place_id:
        raise ValueError(f"Google Maps result for {business_name} did not include a place_id")
    
    return place_id

def search_recent_reviews(business_id: int, business_name: str,location: str, published_after: datetime | None, review_limit: int = 5, place_id: str | None = None) -> list[dict]:
    if place_id is None:
        place_id = _find_place_id(business_name, location)

    results = client.search(
        {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "sort_by": "newestFirst",
            "hl": "en",
        }
    )

    if "error" in results:
        raise RuntimeError(results["error"])
    
    recent_reviews = []

    for result in results.get("reviews", [])[:review_limit]:
        review_text = (
            result.get("extracted_snippet", {}).get("original")
            or result.get("snippet")
            or ""
        ).strip()

        rating = result.get("rating")
        iso_date = result.get("iso_date")

        if not review_text or rating is None or not iso_date:
            continue

        published_at = datetime.fromisoformat(
            iso_date.replace("Z", "+00:00")
        )

        if published_after is not None and published_at <= published_after:
            continue

        recent_reviews.append(
            {
                "business_id": business_id,
                "review": review_text,
                "rating": float(rating),
                "published_at": published_at,
                "source": "google",
            }
        )

    return recent_reviews

# If there is nothing in the database
def search_businesses(facility_type: str, location: str, business_limit: int = 5) -> list[dict]:
    results = client.search(
        {
            "engine": "google_maps",
            "q": f"{facility_type} in {location}",
            "type": "search",
            "hl": "en",
        }
    )

    if "error" in results:
        raise RuntimeError(results["error"])

    businesses = []

    for result in results.get("local_results", [])[:business_limit]:
        name = result.get("title")
        place_id = result.get("place_id")

        if not name or not place_id:
            continue

        businesses.append(
            {
                "name": name,
                "facility_type": facility_type,
                "location": result.get("address", location),
                "price": result.get("price", "Unknown"),
                "place_id": place_id,
            }
        )

    return businesses