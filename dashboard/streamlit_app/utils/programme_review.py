"""Page 4: frozen programme-review synthesis and review cues."""

import pandas as pd
from utils.presentation import ui as st

from utils.data_loader import (
    DashboardDataError,
    load_frozen_table,
    load_specifications,
)


PROGRAMME_BRIEF_SOURCE = (
    "programme_review/programme_review_brief.csv"
)

PROGRAMME_BRIEF_COLUMNS = [
    "Review domain",
    "Observed evidence",
    "Model evidence",
    "Programme-review cue",
    "Contextual lenses",
    "Key caution",
]

PROGRAMME_BRIEF_ORDER = [
    "Equity: household wealth",
    "Access: travel time",
    "Geographic heterogeneity: region",
    "Timing and continuity: early ANC",
]



CORE_REVIEW_SOURCE = (
    "programme_review/core_programme_review.csv"
)

CORE_REVIEW_COLUMNS = [
    "Core signal",
    "What Notebook 4 shows",
    "Programme-review focus",
    "Options/issues to examine",
    "Guidance anchor",
    "Local verification needed",
    "Boundary",
]

CORE_REVIEW_ORDER = [
    "Household wealth",
    "Travel time",
    "Region",
    "Early ANC initiation",
]



CONTEXTUAL_SOURCE = (
    "programme_review/contextual_overlays.csv"
)

CONTEXTUAL_COLUMNS = [
    "Contextual signal",
    "Observed Notebook 4 pattern",
    "How to use in programme review",
    "Most relevant core domains",
    "Evidence needed before interpretation",
    "Boundary",
]

CONTEXTUAL_ORDER = [
    "Maternal occupation",
    "Religion",
    "Pregnancy intention",
]



GUIDANCE_SOURCE = (
    "programme_review/programme_guidance_register.csv"
)

GUIDANCE_COLUMNS = [
    "Source",
    "Guidance anchor",
    "Relevant Notebook 4 signals",
    "Programme relevance",
    "Interpretation boundary",
]

GUIDANCE_SOURCE_ORDER = [
    "Ethiopia National Antenatal Care Guideline (2022)",
    "Ethiopia National Antenatal Care Guideline (2022)",
    "WHO Recommendations on Antenatal Care for a Positive Pregnancy Experience (2016)",
    "WHO ANC health-system implementation guidance",
    "WHO ANC implementation considerations",
    "WHO community mobilization guidance for maternal and newborn health",
]



REGIONAL_CUES_SOURCE = (
    "programme_review/regional_review_cues.csv"
)

REGIONAL_CUES_COLUMNS = [
    "Region",
    "Observed pattern",
    "Programme-review question",
]


def page4_contract():
    """Return the five ordered Page 4 visual contracts."""

    visual = load_specifications()["visual"]

    selected = visual.loc[
        visual["page_order"].eq("4")
    ].copy()

    if len(selected) != 5:
        raise DashboardDataError(
            "Page 4 must contain exactly five visual contracts."
        )

    selected["display_order"] = (
        selected["visual_order"].astype(int)
    )

    selected = (
        selected
        .sort_values("display_order")
        .reset_index(drop=True)
    )

    expected_ids = {
        "P4_V1",
        "P4_V2",
        "P4_V3",
        "P4_V4",
        "P4_V5",
    }

    if set(selected["visual_id"]) != expected_ids:
        raise DashboardDataError(
            "Page 4 visual IDs do not match the approved blueprint."
        )

    return selected


def programme_brief_table():
    """Load and validate the frozen Programme Review Brief."""

    table = load_frozen_table(
        PROGRAMME_BRIEF_SOURCE
    )

    missing = sorted(
        set(PROGRAMME_BRIEF_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Programme Review Brief is missing columns: "
            + str(missing)
        )

    if len(table) != 4:
        raise DashboardDataError(
            "Programme Review Brief must contain four domains."
        )

    if (
        table["Review domain"].tolist()
        != PROGRAMME_BRIEF_ORDER
    ):
        raise DashboardDataError(
            "Unexpected Programme Review Brief domain order."
        )

    if table["Review domain"].duplicated().any():
        raise DashboardDataError(
            "Programme-review domains must be unique."
        )

    for column in PROGRAMME_BRIEF_COLUMNS:

        values = (
            table[column]
            .astype(str)
            .str.strip()
        )

        if values.eq("").any():
            raise DashboardDataError(
                f"Programme Review Brief contains blank text: {column}"
            )

    return table


def render_programme_brief(selected):
    """Render P4_V1 from the frozen programme-review synthesis."""

    contract = selected.loc[
        selected["visual_id"].eq("P4_V1")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != PROGRAMME_BRIEF_SOURCE
    ):
        raise DashboardDataError(
            "Programme Review Brief does not match "
            "the approved P4_V1 blueprint."
        )

    contract = contract.iloc[0]

    table = programme_brief_table()

    st.header(
        "1. Programme review brief"
    )

    st.caption(
        "Evidence layer: "
        + contract["denominator_note"]
    )

    st.markdown(
        "Four review domains bring together the frozen observed "
        "patterns and predictive evidence. Each domain ends with "
        "a programme-review cue and an explicit caution."
    )

    for _, row in table.iterrows():

        with st.container(border=True):

            st.markdown(
                "### " + row["Review domain"]
            )

            observed_col, model_col = st.columns(2)

            with observed_col:

                st.markdown(
                    "**Observed evidence**"
                )

                st.write(
                    row["Observed evidence"]
                )

            with model_col:

                st.markdown(
                    "**Model evidence**"
                )

                st.write(
                    row["Model evidence"]
                )

            st.markdown(
                "**Programme-review cue**"
            )

            st.decision_cue(
                row["Programme-review cue"]
            )

            st.markdown(
                "**Contextual lenses:** "
                + row["Contextual lenses"]
            )

            st.warning(
                row["Key caution"]
            )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Programme Review Brief: exact frozen values and source"
    ):

        st.dataframe(
            table[
                PROGRAMME_BRIEF_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + PROGRAMME_BRIEF_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "Observed evidence, predictive evidence and review cues "
            "are kept as distinct evidence types. The dashboard does "
            "not translate these rows into intervention effects, "
            "recommendations or programme priorities."
        )



def core_review_table():
    """Load and validate the frozen core programme-review matrix."""

    table = load_frozen_table(
        CORE_REVIEW_SOURCE
    )

    missing = sorted(
        set(CORE_REVIEW_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Core programme-review matrix is missing columns: "
            + str(missing)
        )

    if len(table) != 4:
        raise DashboardDataError(
            "Core programme-review matrix must contain four signals."
        )

    if (
        table["Core signal"].tolist()
        != CORE_REVIEW_ORDER
    ):
        raise DashboardDataError(
            "Unexpected core programme-review signal order."
        )

    if table["Core signal"].duplicated().any():
        raise DashboardDataError(
            "Core programme-review signals must be unique."
        )

    for column in CORE_REVIEW_COLUMNS:

        values = (
            table[column]
            .astype(str)
            .str.strip()
        )

        if values.eq("").any():
            raise DashboardDataError(
                f"Core programme-review matrix contains blank text: {column}"
            )

    return table


def render_core_review(selected):
    """Render P4_V2 from the frozen core programme-review matrix."""

    contract = selected.loc[
        selected["visual_id"].eq("P4_V2")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != CORE_REVIEW_SOURCE
    ):
        raise DashboardDataError(
            "Core programme-review matrix does not match "
            "the approved P4_V2 blueprint."
        )

    contract = contract.iloc[0]

    table = core_review_table()

    st.header(
        "2. Core programme review matrix"
    )

    st.caption(
        "Evidence layer: "
        + contract["denominator_note"]
    )

    st.markdown(
        "The four core signals are shown as parallel review domains. "
        "Their ordering follows the frozen source and does not represent "
        "a priority ranking."
    )

    for _, row in table.iterrows():

        with st.container(border=True):

            st.markdown(
                "### " + row["Core signal"]
            )

            st.markdown(
                "**What Notebook 4 shows**"
            )

            st.write(
                row["What Notebook 4 shows"]
            )

            st.markdown(
                "**Programme-review focus**"
            )

            st.decision_cue(
                row["Programme-review focus"]
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "**Options/issues to examine**"
                )

                st.write(
                    row["Options/issues to examine"]
                )

                st.markdown(
                    "**Guidance anchor**"
                )

                st.write(
                    row["Guidance anchor"]
                )

            with col2:

                st.markdown(
                    "**Local verification needed**"
                )

                st.write(
                    row["Local verification needed"]
                )

                st.markdown(
                    "**Interpretation boundary**"
                )

                st.warning(
                    row["Boundary"]
                )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Core programme review matrix: exact frozen values and source"
    ):

        st.dataframe(
            table[
                CORE_REVIEW_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + CORE_REVIEW_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "The matrix preserves review questions and evidence "
            "boundaries from Notebook 4. It does not create a composite "
            "score, rank programme priorities or prescribe interventions."
        )



def contextual_overlays_table():
    """Load and validate the frozen contextual overlays."""

    table = load_frozen_table(
        CONTEXTUAL_SOURCE
    )

    missing = sorted(
        set(CONTEXTUAL_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Contextual overlays are missing columns: "
            + str(missing)
        )

    if len(table) != 3:
        raise DashboardDataError(
            "Contextual overlays must contain three signals."
        )

    if (
        table["Contextual signal"].tolist()
        != CONTEXTUAL_ORDER
    ):
        raise DashboardDataError(
            "Unexpected contextual-signal order."
        )

    if table["Contextual signal"].duplicated().any():
        raise DashboardDataError(
            "Contextual signals must be unique."
        )

    for column in CONTEXTUAL_COLUMNS:

        values = (
            table[column]
            .astype(str)
            .str.strip()
        )

        if values.eq("").any():
            raise DashboardDataError(
                f"Contextual overlays contain blank text: {column}"
            )

    return table


def render_contextual_overlays(selected):
    """Render P4_V3 from the frozen contextual synthesis."""

    contract = selected.loc[
        selected["visual_id"].eq("P4_V3")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != CONTEXTUAL_SOURCE
    ):
        raise DashboardDataError(
            "Contextual overlays do not match "
            "the approved P4_V3 blueprint."
        )

    contract = contract.iloc[0]

    table = contextual_overlays_table()

    st.header(
        "3. Contextual overlays"
    )

    st.caption(
        "Evidence layer: "
        + contract["denominator_note"]
    )

    st.markdown(
        "These signals provide additional context for interpreting "
        "the core programme-review domains. They are secondary lenses "
        "for investigation rather than stand-alone programme targets."
    )

    for _, row in table.iterrows():

        with st.container(border=True):

            st.markdown(
                "### " + row["Contextual signal"]
            )

            st.markdown(
                "**Observed Notebook 4 pattern**"
            )

            st.write(
                row[
                    "Observed Notebook 4 pattern"
                ]
            )

            st.markdown(
                "**How to use in programme review**"
            )

            st.decision_cue(
                row[
                    "How to use in programme review"
                ]
            )

            left, right = st.columns(2)

            with left:

                st.markdown(
                    "**Most relevant core domains**"
                )

                st.write(
                    row[
                        "Most relevant core domains"
                    ]
                )

            with right:

                st.markdown(
                    "**Evidence needed before interpretation**"
                )

                st.write(
                    row[
                        "Evidence needed before interpretation"
                    ]
                )

            st.warning(
                row["Boundary"]
            )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Contextual overlays: exact frozen values and source"
    ):

        st.dataframe(
            table[
                CONTEXTUAL_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + CONTEXTUAL_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "Contextual signals support interpretation and local "
            "investigation. They are not treated as intrinsic barriers, "
            "causal mechanisms or intervention targets."
        )



def guidance_register_table():
    """Load and validate the frozen programme-guidance register."""

    table = load_frozen_table(
        GUIDANCE_SOURCE
    )

    missing = sorted(
        set(GUIDANCE_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Programme guidance register is missing columns: "
            + str(missing)
        )

    if len(table) != 6:
        raise DashboardDataError(
            "Programme guidance register must contain six entries."
        )

    if (
        table["Source"].tolist()
        != GUIDANCE_SOURCE_ORDER
    ):
        raise DashboardDataError(
            "Unexpected programme-guidance source order."
        )

    for column in GUIDANCE_COLUMNS:

        values = (
            table[column]
            .astype(str)
            .str.strip()
        )

        if values.eq("").any():
            raise DashboardDataError(
                f"Programme guidance register contains blank text: {column}"
            )

    return table


def render_guidance_register(selected):
    """Render P4_V4 as a distinct external-guidance layer."""

    contract = selected.loc[
        selected["visual_id"].eq("P4_V4")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != GUIDANCE_SOURCE
    ):
        raise DashboardDataError(
            "Programme guidance register does not match "
            "the approved P4_V4 blueprint."
        )

    contract = contract.iloc[0]

    table = guidance_register_table()

    st.header(
        "4. Programme guidance register"
    )

    st.caption(
        "Evidence layer: "
        + contract["denominator_note"]
    )

    st.markdown(
        "This register keeps external programme guidance distinct "
        "from the observed survey and predictive-model evidence. "
        "Repeated source names represent separate guidance anchors."
    )

    for _, row in table.iterrows():

        with st.container(border=True):

            st.markdown(
                "### " + row["Source"]
            )

            st.markdown(
                "**Guidance anchor**"
            )

            st.write(
                row["Guidance anchor"]
            )

            left, right = st.columns(2)

            with left:

                st.markdown(
                    "**Relevant Notebook 4 signals**"
                )

                st.write(
                    row[
                        "Relevant Notebook 4 signals"
                    ]
                )

            with right:

                st.markdown(
                    "**Programme relevance**"
                )

                st.write(
                    row[
                        "Programme relevance"
                    ]
                )

            st.warning(
                row[
                    "Interpretation boundary"
                ]
            )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Programme guidance register: exact frozen values and source"
    ):

        st.dataframe(
            table[
                GUIDANCE_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + GUIDANCE_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "External guidance is retained as a separate evidence "
            "layer. It may frame issues or options for programme "
            "review but does not transform Notebook 4 associations "
            "into intervention-effect estimates."
        )



def regional_review_cues_table():
    """Load and validate the frozen regional review cues."""

    table = load_frozen_table(
        REGIONAL_CUES_SOURCE
    )

    missing = sorted(
        set(REGIONAL_CUES_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Regional review cues are missing columns: "
            + str(missing)
        )

    if len(table) != 14:
        raise DashboardDataError(
            "Regional review cues must contain 14 regions."
        )

    if (
        table["Region"].isna().any()
        or table["Region"].duplicated().any()
    ):
        raise DashboardDataError(
            "Regional review labels must be complete and unique."
        )

    for column in REGIONAL_CUES_COLUMNS:

        values = (
            table[column]
            .astype(str)
            .str.strip()
        )

        if values.eq("").any():
            raise DashboardDataError(
                f"Regional review cues contain blank text: {column}"
            )

    return table


def render_regional_review_cues(selected):
    """Render P4_V5 from the frozen regional narrative layer."""

    contract = selected.loc[
        selected["visual_id"].eq("P4_V5")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != REGIONAL_CUES_SOURCE
    ):
        raise DashboardDataError(
            "Regional review cues do not match "
            "the approved P4_V5 blueprint."
        )

    contract = contract.iloc[0]

    table = regional_review_cues_table()

    st.header(
        "5. Regional review cues"
    )

    st.caption(
        "Evidence layer: "
        + contract["denominator_note"]
    )

    st.markdown(
        "The regional cues identify questions that programme teams "
        "may investigate using local routine, service-readiness and "
        "qualitative evidence. Their order follows the frozen source "
        "and is not a regional ranking."
    )

    region_view = st.selectbox(
        "Region view",
        options=[
            "All regions",
            *table["Region"].tolist(),
        ],
        key="regional_review_region",
    )

    if region_view == "All regions":

        display = table.copy()

    else:

        display = table.loc[
            table["Region"].eq(
                region_view
            )
        ].copy()

    st.dataframe(
        display[
            REGIONAL_CUES_COLUMNS
        ].reset_index(drop=True),
        hide_index=True,
        width="stretch",
    )

    st.caption(
        "Selecting a region filters the existing frozen review cue. "
        "It does not calculate a new estimate or subgroup."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Regional review cues: source and interpretation"
    ):

        st.markdown(
            "**Source:** `"
            + REGIONAL_CUES_SOURCE
            + "`"
        )

        st.markdown(
            "**Rows in frozen source:** "
            + str(len(table))
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "The regional prompts are descriptive review aids. "
            "They do not rank regions, assign operational priority "
            "or identify causal mechanisms."
        )




def render_programme_review():
    """Render Page 4, currently implemented through P4_V1."""

    st.caption(
        "ANC8+ Programme Review · Page 4 of 4"
    )

    st.title(
        "Programme review"
    )

    st.markdown(
        "### What should programme teams examine next?"
    )

    st.info(
        "Review cues are questions for local investigation. "
        "Guidance and associations do not by themselves establish "
        "intervention effects or operational priorities."
    )

    st.caption(
        "Complete · all five "
        "Programme Review displays are implemented."
    )

    try:

        selected = page4_contract()

        render_programme_brief(
            selected
        )

        st.divider()

        render_core_review(
            selected
        )

        st.divider()

        render_contextual_overlays(
            selected
        )

        st.divider()

        render_guidance_register(
            selected
        )

        st.divider()

        render_regional_review_cues(
            selected
        )

    except (
        DashboardDataError,
        OSError,
        KeyError,
        ValueError,
    ) as exc:

        st.error(
            "The Programme Review evidence could not be displayed. "
            "Please contact the dashboard maintainer."
        )

        with st.expander(
            "Validation details"
        ):
            st.code(str(exc))

        st.stop()
