from nicegui import run, ui

from app.agents.coordinator import CoordinatorAgent


coordinator = CoordinatorAgent()


def confidence_color(confidence: str) -> str:
    return {
        "High": "positive",
        "Medium": "warning",
        "Low": "negative",
    }.get(confidence, "grey")


def theme_chips(
    title: str,
    themes: list[str],
    icon: str,
) -> None:
    if not themes:
        return

    with ui.column().classes("w-full gap-2"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon).classes("text-lg")
            ui.label(title).classes(
                "text-sm font-semibold text-slate-700"
            )

        with ui.row().classes("gap-2 flex-wrap"):
            for theme in themes:
                ui.chip(theme).props("outline").classes(
                    "text-sm"
                )


def display_result(
    result: dict,
    rank: int,
) -> None:
    rating = result["weighted_rating"]
    match_score = result["preference_match_score"]
    confidence = result["confidence"]

    with ui.card().classes(
        "w-full p-6 rounded-2xl shadow-sm border "
        "border-slate-200 bg-white"
    ):
        with ui.row().classes(
            "w-full items-start justify-between gap-4"
        ):
            with ui.row().classes("items-start gap-4"):
                ui.label(str(rank)).classes(
                    "w-10 h-10 rounded-full bg-slate-900 "
                    "text-white flex items-center justify-center "
                    "text-lg font-bold"
                )

                with ui.column().classes("gap-1"):
                    ui.label(result["name"]).classes(
                        "text-xl font-bold text-slate-900"
                    )
                    ui.label(result["location"]).classes(
                        "text-sm text-slate-500"
                    )

            ui.badge(
                confidence,
                color=confidence_color(confidence),
            ).classes("text-sm px-3 py-1")

        with ui.row().classes(
            "w-full gap-6 flex-wrap mt-4"
        ):
            with ui.column().classes("gap-0"):
                ui.label("Weighted rating").classes(
                    "text-xs uppercase tracking-wide "
                    "text-slate-500"
                )
                ui.label(
                    f"{rating:.2f} / 5"
                    if rating is not None
                    else "Unavailable"
                ).classes("text-lg font-semibold")

            with ui.column().classes("gap-0"):
                ui.label("Effective reviews").classes(
                    "text-xs uppercase tracking-wide "
                    "text-slate-500"
                )
                ui.label(
                    str(result["effective_review_count"])
                ).classes("text-lg font-semibold")

            with ui.column().classes("gap-0"):
                ui.label("Preference match").classes(
                    "text-xs uppercase tracking-wide "
                    "text-slate-500"
                )
                ui.label(
                    f"{match_score * 100:.1f}%"
                ).classes("text-lg font-semibold")

            with ui.column().classes("gap-0"):
                ui.label("Price").classes(
                    "text-xs uppercase tracking-wide "
                    "text-slate-500"
                )
                ui.label(result["price"]).classes(
                    "text-lg font-semibold"
                )

        ui.separator().classes("my-4")

        ui.label("Review summary").classes(
            "text-sm font-semibold text-slate-700"
        )
        ui.label(result["summary"]).classes(
            "text-base leading-7 text-slate-700"
        )

        with ui.row().classes(
            "w-full gap-8 items-start mt-4"
        ):
            with ui.column().classes(
                "flex-1 min-w-[280px]"
            ):
                theme_chips(
                    title="Positive themes",
                    themes=result["positive_themes"],
                    icon="thumb_up",
                )

            with ui.column().classes(
                "flex-1 min-w-[280px]"
            ):
                theme_chips(
                    title="Negative themes",
                    themes=result["negative_themes"],
                    icon="thumb_down",
                )

        with ui.expansion(
            "Confidence and limitations",
            icon="info",
        ).classes("w-full mt-4"):
            ui.label(
                result["confidence_statement"]
            ).classes(
                "text-sm text-slate-700 leading-6 mb-3"
            )

            for limitation in result["limitations"]:
                with ui.row().classes(
                    "items-start gap-2 mb-2"
                ):
                    ui.icon("warning_amber").classes(
                        "text-amber-600 mt-1"
                    )
                    ui.label(limitation).classes(
                        "text-sm text-slate-600 flex-1"
                    )


@ui.page("/")
def home_page() -> None:
    ui.add_head_html(
        """
        <style>
            body {
                background:
                    linear-gradient(
                        180deg,
                        #f8fafc 0%,
                        #eef2f7 100%
                    );
            }
        </style>
        """
    )

    with ui.column().classes(
        "w-full max-w-6xl mx-auto px-6 py-10 gap-8"
    ):
        with ui.column().classes("gap-2"):
            ui.label("PIVOT!!!").classes(
                "text-4xl font-bold tracking-tight "
                "text-slate-900"
            )
            ui.label(
                "Trust-aware recommendations from recent, "
                "quality-weighted reviews."
            ).classes("text-lg text-slate-600")

        with ui.card().classes(
            "w-full p-6 rounded-2xl shadow-sm "
            "border border-slate-200"
        ):
            ui.label("Find a local service").classes(
                "text-xl font-semibold text-slate-900 mb-3"
            )

            with ui.row().classes(
                "w-full gap-4 items-end flex-wrap"
            ):
                facility_input = ui.input(
                    "Facility type",
                    placeholder="Gym, cafe, clinic...",
                ).classes("flex-1 min-w-[220px]").props(
                    "outlined"
                )

                location_input = ui.input(
                    "Location",
                    placeholder="Austin, Texas",
                ).classes("flex-1 min-w-[220px]").props(
                    "outlined"
                )

            with ui.row().classes(
                "w-full gap-4 items-end flex-wrap mt-4"
            ):
                top_k_input = ui.number(
                    "Results",
                    value=5,
                ).classes("w-32").props("outlined")

                business_limit_input = ui.number(
                    "Businesses to analyze",
                    value=5,
                ).classes("w-48").props("outlined")

                review_limit_input = ui.number(
                    "Reviews per business",
                    value=5,
                ).classes("w-48").props("outlined")

            description_input = ui.textarea(
                "What matters to you?",
                placeholder=(
                    "For example: good equipment, "
                    "low crowding, friendly staff"
                ),
            ).classes("w-full mt-4").props(
                "outlined autogrow"
            )

            search_button = ui.button(
                "Find recommendations",
                icon="search",
            ).classes(
                "mt-4 px-6 py-3 rounded-xl"
            )

        status_container = ui.column().classes(
            "w-full items-center hidden"
        )

        results_container = ui.column().classes(
            "w-full gap-5"
        )

        async def search() -> None:
            facility_type = (
                facility_input.value or ""
            ).strip()

            location = (
                location_input.value or ""
            ).strip()

            description = (
                description_input.value or ""
            ).strip()

            top_k = int(
                top_k_input.value or 5
            )

            business_limit = int(
                business_limit_input.value or 5
            )

            review_limit = int(
                review_limit_input.value or 5
            )

            if not facility_type:
                ui.notify(
                    "Facility type is required.",
                    type="warning",
                )
                return

            if not location:
                ui.notify(
                    "Location is required.",
                    type="warning",
                )
                return

            if top_k <= 0:
                ui.notify(
                    "Results must be greater than zero.",
                    type="warning",
                )
                return

            if business_limit <= 0:
                ui.notify(
                    "Businesses to analyze must be "
                    "greater than zero.",
                    type="warning",
                )
                return

            if review_limit <= 0:
                ui.notify(
                    "Reviews per business must be "
                    "greater than zero.",
                    type="warning",
                )
                return

            if top_k > business_limit:
                ui.notify(
                    "Results cannot exceed the number "
                    "of businesses analyzed.",
                    type="warning",
                )
                return

            search_button.disable()
            results_container.clear()
            status_container.clear()
            status_container.classes(remove="hidden")

            with status_container:
                ui.spinner(size="lg")

                ui.label(
                    "Fetching and evaluating reviews. "
                    "Local model analysis may take a few minutes."
                ).classes(
                    "text-slate-600 text-center"
                )

                ui.label(
                    f"Analyzing up to {business_limit} businesses "
                    f"and {review_limit} reviews per business."
                ).classes(
                    "text-sm text-slate-500 text-center"
                )

            try:
                results = await run.io_bound(
                    coordinator.recommend,
                    facility_type,
                    location,
                    description or None,
                    top_k,
                    business_limit,
                    review_limit,
                )

                status_container.clear()
                status_container.classes(add="hidden")

                if not results:
                    with results_container:
                        ui.label(
                            "No matching businesses were found."
                        ).classes(
                            "text-lg text-slate-600"
                        )
                    return

                with results_container:
                    ui.label(
                        f"Top {len(results)} recommendations"
                    ).classes(
                        "text-2xl font-bold text-slate-900"
                    )

                    for rank, result in enumerate(
                        results,
                        start=1,
                    ):
                        display_result(
                            result=result,
                            rank=rank,
                        )

            except Exception as error:
                status_container.clear()
                status_container.classes(add="hidden")

                ui.notify(
                    f"Recommendation search failed: {error}",
                    type="negative",
                    multi_line=True,
                    close_button=True,
                )

            finally:
                search_button.enable()

        search_button.on_click(search)