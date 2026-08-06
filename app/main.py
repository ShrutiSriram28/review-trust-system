from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.agents.coordinator import CoordinatorAgent
from nicegui import ui
import app.ui.home

app = FastAPI(
    title = "Review Trust System",
    version = "1.0.0",
)

coordinator = CoordinatorAgent()

class RecommendationRequest(BaseModel):
    facility_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    description: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)


@app.get("/api/health")
def health() -> dict:
    return {"status": "healthy"}

@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest) -> dict:
    try:
        results = coordinator.recommend(
            facility_type=request.facility_type,
            location=request.location,
            description=request.description,
            top_k=request.top_k,
        )

        return {
            "facility_type": request.facility_type,
            "location": request.location,
            "description": request.description,
            "results": results,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {error}",
        ) from error

ui.run_with(
    app,
    title="PIVOT",
    favicon="🎯",
)