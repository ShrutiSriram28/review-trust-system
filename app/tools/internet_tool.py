import os 
from datetime import datetime 
from urllib.parse import parse_qs, urlparse
import serpapi
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY is missing from .env")

client = serpapi.Client(api_key=SERPAPI_API_KEY)

class InvalidLocationError(ValueError):
    pass


def validate_location(location: str) -> None:
    """Validate that a location can be found on Google Maps."""
    try:
        results = client.search(
            {
                "engine": "google_maps",
                "q": location,
                "type": "search",
                "hl": "en",
            }
        )
    except Exception as error:
        if "hasn't returned any results" in str(error):
            raise InvalidLocationError(
                f"'{location}' does not appear to be a valid location. Please enter a valid city, area, or location."
            ) from error

        raise

    if "error" in results:
        error_message = str(results["error"])

        if "hasn't returned any results" in error_message:
            raise InvalidLocationError(
                f"'{location}' does not appear to be a valid location. Please enter a valid city, area, or location."
            )

        raise RuntimeError(error_message)

    place_result = results.get("place_results")
    local_results = results.get("local_results", [])

    if not place_result and not local_results:
        raise InvalidLocationError(
            f"'{location}' does not appear to be a valid location. Please enter a valid city, area, or location."
        )

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

def search_recent_reviews(business_id: int, business_name: str, location: str, published_after: datetime | None, review_limit: int = 5, place_id: str | None = None, excluded_published_at: set[str] | None = None) -> list[dict]:
    if place_id is None:
        place_id = _find_place_id(business_name, location)

    excluded_published_at = excluded_published_at or set()
    recent_reviews = []
    next_page_token = None

    while len(recent_reviews) < review_limit:
        search_parameters = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "sort_by": "newestFirst",
            "hl": "en",
        }

        if next_page_token:
            search_parameters["next_page_token"] = next_page_token
            search_parameters["num"] = min(20, review_limit - len(recent_reviews))

        results = client.search(search_parameters)

        if "error" in results:
            raise RuntimeError(results["error"])

        reviews = results.get("reviews", [])

        if not reviews:
            break

        reached_published_after = False

        for result in reviews:
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
                reached_published_after = True
                break

            if published_at.isoformat() in excluded_published_at:
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

            if len(recent_reviews) >= review_limit:
                break

        if len(recent_reviews) >= review_limit or reached_published_after:
            break

        next_page_token = results.get("serpapi_pagination", {}).get("next_page_token")

        if not next_page_token:
            break

    return recent_reviews

# If there is nothing in the database
def search_businesses(facility_type: str, location: str, business_limit: int = 5, excluded_business_names: set[str] | None = None) -> list[dict]:
    excluded_business_names = excluded_business_names or set()
    businesses = []
    seen_place_ids = set()
    search_parameters = {
        "engine": "google_maps",
        "q": f"{facility_type} in {location}",
        "type": "search",
        "hl": "en",
    }

    while len(businesses) < business_limit:
        results = client.search(search_parameters)

        if "error" in results:
            raise RuntimeError(results["error"])

        local_results = results.get("local_results", [])

        if not local_results:
            break

        for result in local_results:
            name = result.get("title")
            place_id = result.get("place_id")

            if not name or not place_id:
                continue

            if name.strip().lower() in excluded_business_names:
                continue

            if place_id in seen_place_ids:
                continue

            seen_place_ids.add(place_id)

            businesses.append(
                {
                    "name": name,
                    "facility_type": facility_type,
                    "location": result.get("address", location),
                    "price": result.get("price", "Unknown"),
                    "place_id": place_id,
                }
            )

            if len(businesses) >= business_limit:
                break

        if len(businesses) >= business_limit:
            break

        next_url = results.get("serpapi_pagination", {}).get("next")

        if not next_url:
            break

        search_parameters = {
            key: values[-1]
            for key, values in parse_qs(urlparse(next_url).query).items()
            if key != "api_key"
        }

    return businesses