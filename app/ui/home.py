import ast

from nicegui import run, ui

from app.agents.coordinator import CoordinatorAgent
from app.tools.internet_tool import InvalidLocationError

coordinator = CoordinatorAgent()


def confidence_color(confidence: str) -> str:
    return {
        "High": "positive",
        "Medium": "warning",
        "Low": "negative",
    }.get(confidence, "grey")


def normalize_theme_list(
    themes: list[str],
) -> list[str]:
    normalized: list[str] = []

    for theme in themes:
        if not isinstance(theme, str):
            continue

        stripped = theme.strip()

        try:
            parsed = ast.literal_eval(stripped)

            if isinstance(
                parsed,
                (list, tuple),
            ):
                normalized.extend(
                    str(item).strip()
                    for item in parsed
                    if str(item).strip()
                )
                continue

        except (ValueError, SyntaxError):
            pass

        if stripped:
            normalized.append(stripped)

    return normalized


def theme_chips(
    title: str,
    themes: list[str],
    icon: str,
) -> None:
    themes = normalize_theme_list(themes)

    if not themes:
        return

    with ui.column().classes(
        "w-full gap-2"
    ):
        with ui.row().classes(
            "items-center gap-2"
        ):
            ui.icon(
                icon
            ).classes(
                "text-lg"
            )

            ui.label(
                title
            ).classes(
                "text-sm font-semibold "
                "text-slate-700"
            )

        with ui.row().classes(
            "gap-2 flex-wrap"
        ):
            for theme in themes:
                ui.chip(
                    theme
                ).props(
                    "outline"
                ).classes(
                    "text-sm"
                )


def preference_fit_label(
    match_score: float | None,
) -> tuple[str, str]:

    if match_score is None:
        return "No preference", "grey"

    if match_score < 0.4:
        return "Low fit", "negative"

    if match_score < 0.7:
        return "Moderate fit", "warning"

    return "High fit", "positive"


def recommendation_info_dialog() -> ui.dialog:
    dialog = ui.dialog()

    with dialog:
        with ui.card().classes(
            "w-full max-w-3xl p-6 "
            "rounded-2xl max-h-[85vh] "
            "overflow-y-auto"
        ):

            # --------------------------------
            # Header
            # --------------------------------

            with ui.row().classes(
                "w-full items-center "
                "justify-between gap-4"
            ):

                ui.label(
                    "How recommendations are calculated"
                ).classes(
                    "text-2xl font-bold "
                    "text-slate-900"
                )

                ui.button(
                    icon="close",
                    on_click=dialog.close,
                ).props(
                    "flat round dense"
                )

            ui.label(
                "PIVOT evaluates both the quality of the "
                "available review evidence and how well "
                "that evidence matches what you asked for."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Weighted rating
            # --------------------------------

            ui.label(
                "Weighted rating"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "The weighted rating is the business's "
                "star rating after giving stronger reviews "
                "more influence than weaker reviews."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Weighted rating = "
                "Σ(review weight × rating) / "
                "Σ(review weight)"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.label(
                "Each review receives a weight based on "
                "information quality, recency, and "
                "independence from other reviews."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Review weight = "
                "0.5 × information quality + "
                "0.3 × recency + "
                "0.2 × independence"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.label(
                "Information quality is calculated from "
                "specificity, experience, relevance, "
                "and clarity."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Information quality = "
                "(specificity + experience + "
                "relevance + clarity) / 4"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Effective review count
            # --------------------------------

            ui.label(
                "Effective review count"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "The effective review count represents "
                "how much usable review evidence remains "
                "after quality, recency, and independence "
                "have been taken into account."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Effective review count = "
                "Σ(review weights)"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.label(
                "The value may be lower than the raw "
                "number of reviews because older, vague, "
                "or highly similar reviews contribute "
                "less evidence."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Preference fit
            # --------------------------------

            ui.label(
                "Preference fit"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "Preference fit measures how strongly "
                "the review evidence supports what you "
                "entered under 'What matters to you?'."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Semantic similarity first identifies "
                "reviews related to your preference. "
                "The system then evaluates whether each "
                "review supports, contradicts, or is "
                "neutral toward that preference."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Evidence contribution = "
                "semantic similarity × review weight × "
                "preference relevance × "
                "preference alignment"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.label(
                "Preference alignment ranges from -1 to +1. "
                "Supporting evidence contributes positively, "
                "contradicting evidence contributes negatively, "
                "and neutral evidence contributes little or no "
                "directional preference signal."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "The signed preference score is then "
                "mapped onto a 0–100% preference-fit scale."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            with ui.column().classes(
                "w-full gap-2 mt-2"
            ):

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "Low fit",
                        color="negative",
                    )

                    ui.label(
                        "Below 40% — the evidence generally "
                        "does not satisfy the preference."
                    ).classes(
                        "text-sm text-slate-600"
                    )

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "Moderate fit",
                        color="warning",
                    )

                    ui.label(
                        "40% to below 70% — evidence is "
                        "mixed or partially supportive."
                    ).classes(
                        "text-sm text-slate-600"
                    )

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "High fit",
                        color="positive",
                    )

                    ui.label(
                        "70% or above — the evidence "
                        "strongly supports the preference."
                    ).classes(
                        "text-sm text-slate-600"
                    )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Evidence confidence
            # --------------------------------

            ui.label(
                "Evidence confidence"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "Evidence confidence describes how much "
                "usable evidence remains from the reviews "
                "that were analyzed. It does not mean that "
                "the business itself is good or bad."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Evidence ratio = "
                "effective review count / "
                "number of reviews analyzed"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            with ui.column().classes(
                "w-full gap-2 mt-2"
            ):

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "Low",
                        color="negative",
                    )

                    ui.label(
                        "Less than 40% effective evidence."
                    ).classes(
                        "text-sm text-slate-600"
                    )

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "Medium",
                        color="warning",
                    )

                    ui.label(
                        "40% to below 80% effective evidence."
                    ).classes(
                        "text-sm text-slate-600"
                    )

                with ui.row().classes(
                    "items-center gap-3"
                ):
                    ui.badge(
                        "High",
                        color="positive",
                    )

                    ui.label(
                        "80% or more effective evidence."
                    ).classes(
                        "text-sm text-slate-600"
                    )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Fit vs confidence
            # --------------------------------

            ui.label(
                "Preference fit and confidence "
                "measure different things"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "Preference fit asks whether the business "
                "matches what you want. Evidence confidence "
                "asks how strongly the available review "
                "evidence supports the system's conclusion."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "A business can therefore have low "
                "preference fit and high evidence confidence. "
                "That means there is strong review evidence "
                "that the business is a poor match for your "
                "stated preference."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            with ui.row().classes(
                "items-center gap-2 mt-1 flex-wrap"
            ):

                ui.badge(
                    "Low fit",
                    color="negative",
                )

                ui.badge(
                    "Evidence confidence: High",
                    color="positive",
                )

                ui.label(
                    "Strong evidence of a poor match."
                ).classes(
                    "text-sm text-slate-600"
                )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Positive and negative themes
            # --------------------------------

            ui.label(
                "Positive and negative themes"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "Themes are recurring aspects identified "
                "from the review evidence. Positive themes "
                "represent favorable recurring observations, "
                "while negative themes represent recurring "
                "concerns."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Themes are descriptive. They do not "
                "directly determine ranking unless they "
                "relate to the user's stated preference."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Conflicting evidence
            # --------------------------------

            ui.label(
                "Conflicting evidence"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "When a preference is provided, PIVOT "
                "surfaces review evidence that contradicts "
                "that preference. This helps explain why a "
                "business may receive a lower preference-fit "
                "score even when its overall rating is high."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Ranking
            # --------------------------------

            ui.label(
                "How recommendations are ranked"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "When you provide a preference, businesses "
                "are ranked primarily by preference fit. "
                "Evidence confidence, weighted rating, and "
                "effective review count are then used as "
                "tie-breakers."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.label(
                "Preference fit → "
                "Evidence confidence → "
                "Weighted rating → "
                "Effective review count"
            ).classes(
                "text-sm font-mono "
                "bg-slate-100 rounded-lg "
                "px-3 py-2"
            )

            ui.label(
                "When no preference is supplied, preference "
                "fit is not calculated. Results are ranked "
                "using evidence confidence, weighted rating, "
                "and effective review count."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            ui.separator().classes(
                "my-3"
            )

            # --------------------------------
            # Price
            # --------------------------------

            ui.label(
                "Price"
            ).classes(
                "text-lg font-semibold "
                "text-slate-900"
            )

            ui.label(
                "Price is sourced from the available business "
                "listing data. It is not calculated by PIVOT "
                "and may be unavailable for some businesses."
            ).classes(
                "text-sm text-slate-600 leading-6"
            )

            # --------------------------------
            # Close
            # --------------------------------

            with ui.row().classes(
                "w-full justify-end mt-4"
            ):
                ui.button(
                    "Close",
                    on_click=dialog.close,
                ).props(
                    "outline"
                )

    return dialog


def display_result(
    result: dict,
    rank: int,
) -> None:

    rating = result[
        "weighted_rating"
    ]

    match_score = result[
        "preference_match_score"
    ]

    match_text = (
        f"{match_score * 100:.1f}%"
        if match_score is not None
        else "—"
    )

    confidence = result[
        "confidence"
    ]

    fit_label, fit_color = (
        preference_fit_label(
            match_score
        )
    )

    with ui.card().classes(
        "w-full p-6 rounded-2xl "
        "shadow-sm border "
        "border-slate-200 bg-white"
    ):

        # --------------------------------
        # Header
        # --------------------------------

        with ui.row().classes(
            "w-full items-start "
            "justify-between gap-4"
        ):

            with ui.row().classes(
                "items-start gap-4"
            ):

                ui.label(
                    str(rank)
                ).classes(
                    "w-10 h-10 rounded-full "
                    "bg-slate-900 text-white "
                    "flex items-center "
                    "justify-center "
                    "text-lg font-bold"
                )

                with ui.column().classes(
                    "gap-1"
                ):

                    ui.label(
                        result["name"]
                    ).classes(
                        "text-xl font-bold "
                        "text-slate-900"
                    )

                    ui.label(
                        result["location"]
                    ).classes(
                        "text-sm text-slate-500"
                    )

            with ui.row().classes(
                "items-center gap-2 "
                "flex-wrap justify-end"
            ):

                if match_score is not None:
                    ui.badge(
                        fit_label,
                        color=fit_color,
                    ).classes(
                        "text-sm px-3 py-1"
                    )

                ui.badge(
                    (
                        "Evidence confidence: "
                        f"{confidence}"
                    ),
                    color=confidence_color(
                        confidence
                    ),
                ).classes(
                    "text-sm px-3 py-1"
                )

        # --------------------------------
        # Metrics
        # --------------------------------

        with ui.row().classes(
            "w-full gap-6 flex-wrap mt-4"
        ):

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "Weighted rating"
                ).classes(
                    "text-xs uppercase "
                    "tracking-wide "
                    "text-slate-500"
                )

                ui.label(
                    (
                        f"{rating:.2f} / 5"
                        if rating is not None
                        else "Unavailable"
                    )
                ).classes(
                    "text-lg font-semibold"
                )

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "Effective review count"
                ).classes(
                    "text-xs uppercase "
                    "tracking-wide "
                    "text-slate-500"
                )

                ui.label(
                    str(
                        result[
                            "effective_review_count"
                        ]
                    )
                ).classes(
                    "text-lg font-semibold"
                )

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "Preference fit"
                ).classes(
                    "text-xs uppercase "
                    "tracking-wide "
                    "text-slate-500"
                )

                ui.label(
                    match_text
                ).classes(
                    "text-lg font-semibold"
                )

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "Price"
                ).classes(
                    "text-xs uppercase "
                    "tracking-wide "
                    "text-slate-500"
                )

                ui.label(
                    result["price"]
                ).classes(
                    "text-lg font-semibold"
                )

        ui.separator().classes(
            "my-4"
        )

        # --------------------------------
        # Review summary
        # --------------------------------

        ui.label(
            "Review summary"
        ).classes(
            "text-sm font-semibold "
            "text-slate-700"
        )

        ui.label(
            result["summary"]
        ).classes(
            "text-base leading-7 "
            "text-slate-700"
        )

        # --------------------------------
        # Preference assessment
        # --------------------------------

        if result.get(
            "preference_assessment"
        ):

            with ui.column().classes(
                "w-full mt-4 p-4 "
                "rounded-xl bg-slate-50 "
                "border border-slate-200 gap-2"
            ):

                ui.label(
                    "Preference fit"
                ).classes(
                    "text-sm font-semibold "
                    "text-slate-700"
                )

                ui.label(
                    result[
                        "preference_assessment"
                    ]
                ).classes(
                    "text-sm leading-6 "
                    "text-slate-700"
                )

                conflicts = result.get(
                    "preference_conflicts",
                    [],
                )

                if conflicts:

                    ui.label(
                        "Conflicting evidence"
                    ).classes(
                        "text-sm font-semibold "
                        "text-red-700 mt-1"
                    )

                    with ui.column().classes(
                        "w-full gap-2"
                    ):

                        for conflict in conflicts:

                            with ui.row().classes(
                                "w-full items-start gap-2"
                            ):

                                ui.icon(
                                    "warning_amber"
                                ).classes(
                                    "text-red-600 mt-1"
                                )

                                ui.label(
                                    conflict
                                ).classes(
                                    "text-sm text-red-700 "
                                    "leading-6 "
                                    "whitespace-normal flex-1"
                                )

        # --------------------------------
        # Themes
        # --------------------------------

        with ui.row().classes(
            "w-full gap-8 "
            "items-start mt-4"
        ):

            with ui.column().classes(
                "flex-1 min-w-[280px]"
            ):

                theme_chips(
                    title="Positive themes",
                    themes=result[
                        "positive_themes"
                    ],
                    icon="thumb_up",
                )

            with ui.column().classes(
                "flex-1 min-w-[280px]"
            ):

                theme_chips(
                    title="Negative themes",
                    themes=result[
                        "negative_themes"
                    ],
                    icon="thumb_down",
                )

        # --------------------------------
        # Confidence and limitations
        # --------------------------------

        with ui.expansion(
            "Confidence and limitations",
            icon="info",
        ).classes(
            "w-full mt-4"
        ):

            ui.label(
                result[
                    "confidence_statement"
                ]
            ).classes(
                "text-sm text-slate-700 "
                "leading-6 mb-3"
            )

            for limitation in result[
                "limitations"
            ]:

                with ui.row().classes(
                    "items-start gap-2 mb-2"
                ):

                    ui.icon(
                        "warning_amber"
                    ).classes(
                        "text-amber-600 mt-1"
                    )

                    ui.label(
                        limitation
                    ).classes(
                        "text-sm text-slate-600 "
                        "flex-1"
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

    info_dialog = (
        recommendation_info_dialog()
    )

    with ui.column().classes(
        "w-full max-w-6xl mx-auto "
        "px-6 py-10 gap-8"
    ):

        # --------------------------------
        # Page heading
        # --------------------------------

        with ui.column().classes(
            "gap-2"
        ):

            ui.label(
                "PIVOT!!!"
            ).classes(
                "text-4xl font-bold "
                "tracking-tight "
                "text-slate-900"
            )

            ui.label(
                "Trust-aware recommendations "
                "from recent, "
                "quality-weighted reviews."
            ).classes(
                "text-lg text-slate-600"
            )

        # --------------------------------
        # Search card
        # --------------------------------

        with ui.card().classes(
            "w-full p-6 rounded-2xl "
            "shadow-sm border "
            "border-slate-200"
        ):

            ui.label(
                "Find a local service"
            ).classes(
                "text-xl font-semibold "
                "text-slate-900 mb-3"
            )

            with ui.row().classes(
                "w-full gap-4 "
                "items-end flex-wrap"
            ):

                facility_input = ui.input(
                    "Facility type",
                    placeholder=(
                        "Gym, cafe, clinic..."
                    ),
                ).classes(
                    "flex-1 min-w-[220px]"
                ).props(
                    "outlined"
                )

                location_input = ui.input(
                    "Location",
                    placeholder=(
                        "Austin, Texas"
                    ),
                ).classes(
                    "flex-1 min-w-[220px]"
                ).props(
                    "outlined"
                )

            with ui.row().classes(
                "w-full gap-4 "
                "items-end flex-wrap mt-4"
            ):

                top_k_input = ui.number(
                    "Results",
                    value=5,
                ).classes(
                    "w-32"
                ).props(
                    "outlined"
                )

                business_limit_input = (
                    ui.number(
                        "Businesses to analyze",
                        value=5,
                    ).classes(
                        "w-48"
                    ).props(
                        "outlined"
                    )
                )

                review_limit_input = (
                    ui.number(
                        "Reviews per business",
                        value=5,
                    ).classes(
                        "w-48"
                    ).props(
                        "outlined"
                    )
                )

            description_input = (
                ui.textarea(
                    "What matters to you?",
                    placeholder=(
                        "For example: good equipment, "
                        "low crowding, friendly staff"
                    ),
                ).classes(
                    "w-full mt-4"
                ).props(
                    "outlined autogrow"
                )
            )

            search_button = ui.button(
                "Find recommendations",
                icon="search",
            ).classes(
                "mt-4 px-6 py-3 "
                "rounded-xl"
            )

        # --------------------------------
        # Dynamic containers
        # --------------------------------

        status_container = (
            ui.column().classes(
                "w-full items-center hidden"
            )
        )

        results_container = (
            ui.column().classes(
                "w-full gap-5"
            )
        )

        # --------------------------------
        # Search
        # --------------------------------

        async def search() -> None:

            facility_type = (
                facility_input.value
                or ""
            ).strip()

            location = (
                location_input.value
                or ""
            ).strip()

            description = (
                description_input.value
                or ""
            ).strip()

            top_k = int(
                top_k_input.value
                or 5
            )

            business_limit = int(
                business_limit_input.value
                or 5
            )

            review_limit = int(
                review_limit_input.value
                or 5
            )

            # ----------------------------
            # Validation
            # ----------------------------

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
                    "Results must be "
                    "greater than zero.",
                    type="warning",
                )

                return

            if business_limit <= 0:

                ui.notify(
                    "Businesses to analyze "
                    "must be greater than zero.",
                    type="warning",
                )

                return

            if review_limit <= 0:

                ui.notify(
                    "Reviews per business "
                    "must be greater than zero.",
                    type="warning",
                )

                return

            if top_k > business_limit:

                ui.notify(
                    "Results cannot exceed "
                    "the number of businesses "
                    "analyzed.",
                    type="warning",
                )

                return

            # ----------------------------
            # Loading state
            # ----------------------------

            search_button.disable()

            results_container.clear()

            status_container.clear()

            status_container.classes(
                remove="hidden"
            )

            with status_container:

                ui.spinner(
                    size="lg"
                )

                ui.label(
                    "Fetching and evaluating reviews. "
                    "Review analysis may take "
                    "a few moments."
                ).classes(
                    "text-slate-600 "
                    "text-center"
                )

                ui.label(
                    f"Analyzing up to "
                    f"{business_limit} businesses "
                    f"and {review_limit} reviews "
                    f"per business."
                ).classes(
                    "text-sm text-slate-500 "
                    "text-center"
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

                status_container.classes(
                    add="hidden"
                )

                if not results:

                    with results_container:

                        ui.label(
                            "No matching businesses "
                            "were found."
                        ).classes(
                            "text-lg text-slate-600"
                        )

                    return

                # ------------------------
                # Results
                # ------------------------

                with results_container:

                    with ui.row().classes(
                        "items-center gap-2"
                    ):

                        ui.label(
                            f"Top {len(results)} "
                            f"recommendations"
                        ).classes(
                            "text-2xl font-bold "
                            "text-slate-900"
                        )

                        with ui.button(
                            icon="info_outline",
                            on_click=(
                                info_dialog.open
                            ),
                        ).props(
                            "flat round dense"
                        ).classes(
                            "text-slate-500"
                        ):

                            ui.tooltip(
                                "How recommendations "
                                "are calculated"
                            )

                    for rank, result in enumerate(
                        results,
                        start=1,
                    ):

                        display_result(
                            result=result,
                            rank=rank,
                        )

            except InvalidLocationError as error:
                status_container.clear()
                status_container.classes(add="hidden")
                ui.notify(
                    f"{error}",
                    type="negative",
                    close_button=True,
                )

            except Exception as error:

                status_container.clear()

                status_container.classes(
                    add="hidden"
                )

                ui.notify(
                    (
                        "Recommendation search "
                        f"failed: {error}"
                    ),
                    type="negative",
                    multi_line=True,
                    close_button=True,
                )

            finally:

                search_button.enable()

        search_button.on_click(
            search
        )