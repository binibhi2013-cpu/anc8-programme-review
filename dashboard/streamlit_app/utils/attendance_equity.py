"""Page 2: frozen descriptive ANC attendance and equity evidence."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils.presentation import ui as st

from utils.data_loader import (
    DashboardDataError,
    load_frozen_table,
    load_geography,
    load_indicator,
    load_specifications,
)


ATTENDANCE_SOURCE = (
    "dashboard_attendance/attendance_profile_reporting.csv"
)

ATTENDANCE_COLUMNS = [
    "ANC contacts",
    "Unweighted n",
    "Weighted n",
    "Weighted %",
    "SE %",
    "95% CI lower",
    "95% CI upper",
]

ATTENDANCE_ORDER = [
    "0",
    "1–3",
    "4–7",
    "8+",
]



PATHWAY_SOURCE = "dashboard_attendance/anc_pathway_reporting.csv"

PATHWAY_COLUMNS = [
    "stage",
    "transition",
    "eligible_population",
    "eligible_unweighted_n",
    "attained_unweighted_n",
    "weighted_attainment_percent",
    "ci_lower_percent",
    "ci_upper_percent",
    "weighted_nonattainment_percent",
]



WEALTH_ORDER = [
    "Poorest",
    "Poorer",
    "Middle",
    "Richer",
    "Richest",
]



TRAVEL_ORDER = [
    "0-30 min",
    "31-60 min",
    "61-120 min",
    ">120 min",
]



DIAGNOSTIC_SOURCE = "dashboard_attendance/regional_diagnostic.csv"

DIAGNOSTIC_PERCENT_COLUMNS = [
    "Any ANC %",
    "ANC4+ among ANC users %",
    "ANC8+ among ANC4+ %",
    "Early ANC %",
    "ANC8+ among early initiators %",
]

DIAGNOSTIC_GAP_COLUMNS = [
    "Any ANC gap pp",
    "Early ANC gap pp",
    "ANC4+ gap pp",
    "ANC8+ after ANC4 gap pp",
    "ANC8+ after early ANC gap pp",
]

DIAGNOSTIC_COLUMNS = (
    ["Region"]
    + DIAGNOSTIC_PERCENT_COLUMNS
    + DIAGNOSTIC_GAP_COLUMNS
)


def page2_contract():
    """Return the six ordered Page 2 visual contracts."""
    visual = load_specifications()["visual"]

    selected = visual.loc[
        visual["page_order"].eq("2")
    ].copy()

    if len(selected) != 6:
        raise DashboardDataError(
            "Page 2 must contain exactly six visual contracts."
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
        "P2_V1",
        "P2_V2",
        "P2_V3",
        "P2_V4",
        "P2_V5",
        "P2_V6",
    }

    if set(selected["visual_id"]) != expected_ids:
        raise DashboardDataError(
            "Page 2 visual IDs do not match the approved blueprint."
        )

    return selected


def attendance_profile_table():
    """Load and validate the untouched frozen attendance profile."""
    table = load_frozen_table(
        ATTENDANCE_SOURCE
    )

    missing = sorted(
        set(ATTENDANCE_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Attendance profile is missing columns: "
            + str(missing)
        )

    if len(table) != 4:
        raise DashboardDataError(
            "Attendance profile must contain four categories."
        )

    if table["ANC contacts"].tolist() != ATTENDANCE_ORDER:
        raise DashboardDataError(
            "Unexpected ANC-contact category order."
        )

    if table["ANC contacts"].duplicated().any():
        raise DashboardDataError(
            "ANC-contact categories must be unique."
        )

    numeric_columns = [
        "Unweighted n",
        "Weighted n",
        "Weighted %",
        "SE %",
        "95% CI lower",
        "95% CI upper",
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Attendance field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Attendance profile contains non-finite values."
        )

    percent_columns = [
        "Weighted %",
        "95% CI lower",
        "95% CI upper",
    ]

    if not (
        table[percent_columns]
        .ge(0)
        .all()
        .all()
        and
        table[percent_columns]
        .le(100)
        .all()
        .all()
    ):
        raise DashboardDataError(
            "Attendance percentages must lie between 0 and 100."
        )

    if not (
        table["95% CI lower"]
        <= table["Weighted %"]
    ).all():
        raise DashboardDataError(
            "Attendance estimate falls below its CI."
        )

    if not (
        table["Weighted %"]
        <= table["95% CI upper"]
    ).all():
        raise DashboardDataError(
            "Attendance estimate exceeds its CI."
        )

    if not table["Unweighted n"].gt(0).all():
        raise DashboardDataError(
            "Attendance counts must be positive."
        )

    if not table["Weighted n"].gt(0).all():
        raise DashboardDataError(
            "Weighted counts must be positive."
        )

    if not np.isclose(
        table["Weighted %"].sum(),
        100.0,
        atol=0.05,
    ):
        raise DashboardDataError(
            "Attendance categories do not sum to approximately 100%."
        )

    return table


def attendance_profile_figure(table):
    """Build the presentation-only attendance profile chart."""
    upper_error = (
        table["95% CI upper"]
        - table["Weighted %"]
    )

    lower_error = (
        table["Weighted %"]
        - table["95% CI lower"]
    )

    customdata = table[
        [
            "95% CI lower",
            "95% CI upper",
            "Unweighted n",
            "Weighted n",
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_bar(
        x=table["ANC contacts"],
        y=table["Weighted %"],
        customdata=customdata,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": upper_error,
            "arrayminus": lower_error,
            "visible": True,
        },
        hovertemplate=(
            "<b>ANC contacts: %{x}</b><br>"
            "Weighted: %{y:.1f}%<br>"
            "95% CI: %{customdata[0]:.1f}%–"
            "%{customdata[1]:.1f}%<br>"
            "Unweighted n: %{customdata[2]:,.0f}<br>"
            "Weighted n: %{customdata[3]:,.1f}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        xaxis_title="ANC contacts",
        yaxis_title="Weighted percent",
        yaxis_range=[
            0,
            max(
                40,
                float(
                    table["95% CI upper"].max()
                    + 5
                ),
            ),
        ],
        showlegend=False,
        height=430,
        margin={
            "l": 30,
            "r": 20,
            "t": 20,
            "b": 30,
        },
    )

    return figure



def anc_pathway_table():
    """Load and validate the frozen national ANC pathway."""
    table = load_frozen_table(PATHWAY_SOURCE)

    missing = sorted(
        set(PATHWAY_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "ANC pathway is missing columns: "
            + str(missing)
        )

    if len(table) != 3:
        raise DashboardDataError(
            "ANC pathway must contain exactly three stages."
        )

    if table["stage"].tolist() != [1, 2, 3]:
        raise DashboardDataError(
            "ANC pathway stages must be ordered 1, 2, 3."
        )

    if (
        table["stage"].duplicated().any()
        or table["transition"].duplicated().any()
    ):
        raise DashboardDataError(
            "ANC pathway stages and transitions must be unique."
        )

    if (
        table["eligible_population"]
        .astype(str)
        .str.strip()
        .eq("")
        .any()
    ):
        raise DashboardDataError(
            "ANC pathway contains a blank eligible population."
        )

    numeric_columns = [
        "eligible_unweighted_n",
        "attained_unweighted_n",
        "weighted_attainment_percent",
        "ci_lower_percent",
        "ci_upper_percent",
        "weighted_nonattainment_percent",
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"ANC pathway field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "ANC pathway contains non-finite numeric values."
        )

    if not table[
        "eligible_unweighted_n"
    ].gt(0).all():
        raise DashboardDataError(
            "Eligible pathway counts must be positive."
        )

    if not table[
        "attained_unweighted_n"
    ].ge(0).all():
        raise DashboardDataError(
            "Attained pathway counts cannot be negative."
        )

    if not (
        table["attained_unweighted_n"]
        <= table["eligible_unweighted_n"]
    ).all():
        raise DashboardDataError(
            "Attained count exceeds the eligible count."
        )

    percent_columns = [
        "weighted_attainment_percent",
        "ci_lower_percent",
        "ci_upper_percent",
        "weighted_nonattainment_percent",
    ]

    if not (
        table[percent_columns]
        .ge(0)
        .all()
        .all()
        and
        table[percent_columns]
        .le(100)
        .all()
        .all()
    ):
        raise DashboardDataError(
            "ANC pathway percentages must lie between 0 and 100."
        )

    if not (
        table["ci_lower_percent"]
        <= table["weighted_attainment_percent"]
    ).all():
        raise DashboardDataError(
            "Pathway estimate falls below its confidence interval."
        )

    if not (
        table["weighted_attainment_percent"]
        <= table["ci_upper_percent"]
    ).all():
        raise DashboardDataError(
            "Pathway estimate exceeds its confidence interval."
        )

    if not np.allclose(
        (
            table["weighted_attainment_percent"]
            + table["weighted_nonattainment_percent"]
        ),
        100.0,
        atol=0.05,
    ):
        raise DashboardDataError(
            "Attainment and non-attainment do not sum "
            "to approximately 100%."
        )

    return table


def anc_pathway_figure(table):
    """Build a presentation-only conditional attainment chart."""

    upper_error = (
        table["ci_upper_percent"]
        - table["weighted_attainment_percent"]
    )

    lower_error = (
        table["weighted_attainment_percent"]
        - table["ci_lower_percent"]
    )

    customdata = table[
        [
            "eligible_population",
            "eligible_unweighted_n",
            "attained_unweighted_n",
            "ci_lower_percent",
            "ci_upper_percent",
            "weighted_nonattainment_percent",
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_scatter(
        mode="markers+text",
        marker={"size": 12},
        x=table["weighted_attainment_percent"],
        y=table["transition"],
        customdata=customdata,
        error_x={
            "type": "data",
            "symmetric": False,
            "array": upper_error,
            "arrayminus": lower_error,
            "visible": True,
        },
        text=table["weighted_attainment_percent"],
        texttemplate="%{text:.1f}%",
        textposition="top center",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Attainment: %{x:.1f}%<br>"
            "95% CI: %{customdata[3]:.1f}%–"
            "%{customdata[4]:.1f}%<br>"
            "Eligible population: %{customdata[0]}<br>"
            "Eligible n: %{customdata[1]:,.0f}<br>"
            "Attained n: %{customdata[2]:,.0f}<br>"
            "Non-attainment: %{customdata[5]:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        xaxis_title="Conditional weighted attainment (%)",
        yaxis_title=None,
        xaxis_range=[0, 100],
        showlegend=False,
        height=390,
        margin={
            "l": 40,
            "r": 30,
            "t": 20,
            "b": 30,
        },
    )

    figure.update_yaxes(
        autorange="reversed"
    )

    return figure


def render_anc_pathway(selected):
    """Render P2_V2 from the frozen pathway table."""

    contract = selected.loc[
        selected["visual_id"].eq("P2_V2")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != PATHWAY_SOURCE
    ):
        raise DashboardDataError(
            "ANC pathway does not match "
            "the approved P2_V2 blueprint."
        )

    contract = contract.iloc[0]

    table = anc_pathway_table()

    st.header(
        "2. National ANC pathway"
    )

    st.caption(
        "Evidence population: "
        + contract["denominator_note"]
    )

    st.markdown(
        "Each bar uses its own eligible population. "
        "The display therefore shows conditional attainment "
        "at successive ANC thresholds rather than one common "
        "cohort being followed over time."
    )

    figure = anc_pathway_figure(
        table
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="national_anc_pathway_chart",
    )

    st.caption(
        "Points show frozen conditional weighted attainment. "
        "Error bars use the frozen 95% confidence-interval "
        "endpoints from Notebook 4."
    )

    st.info(
        contract["interpretation_boundary"]
    )

    with st.expander(
        "National ANC pathway: exact frozen values and source"
    ):
        st.dataframe(
            table[PATHWAY_COLUMNS]
            .reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + PATHWAY_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "The three rows use different eligible populations. "
            "The application does not reconstruct individual "
            "trajectories, calculate dropout or infer movement "
            "between stages."
        )



def wealth_equity_table(indicator):
    """Load and validate one frozen wealth-equity indicator."""

    table, metadata = load_indicator(
        "wealth",
        indicator,
    )

    group = metadata["group_column"]
    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    required = [
        group,
        denominator_n,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    missing = sorted(
        set(required)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Wealth table is missing columns: "
            + str(missing)
        )

    if len(table) != 5:
        raise DashboardDataError(
            "Wealth table must contain five quintiles."
        )

    if table[group].tolist() != WEALTH_ORDER:
        raise DashboardDataError(
            "Unexpected wealth-quintile order."
        )

    if table[group].duplicated().any():
        raise DashboardDataError(
            "Wealth quintiles must be unique."
        )

    numeric_columns = [
        denominator_n,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Wealth field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Wealth table contains non-finite values."
        )

    if not table[denominator_n].gt(0).all():
        raise DashboardDataError(
            "Wealth denominator counts must be positive."
        )

    if not table[numerator_n].ge(0).all():
        raise DashboardDataError(
            "Wealth numerator counts cannot be negative."
        )

    if not (
        table[numerator_n]
        <= table[denominator_n]
    ).all():
        raise DashboardDataError(
            "Wealth numerator exceeds denominator."
        )

    for column in [
        estimate,
        ci_lower,
        ci_upper,
    ]:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Wealth percentage outside 0–100: {column}"
            )

    if not (
        table[ci_lower]
        <= table[estimate]
    ).all():
        raise DashboardDataError(
            "Wealth estimate falls below its CI."
        )

    if not (
        table[estimate]
        <= table[ci_upper]
    ).all():
        raise DashboardDataError(
            "Wealth estimate exceeds its CI."
        )

    return table, metadata


def wealth_equity_figure(table, metadata):
    """Build a presentation-only wealth equity chart."""

    group = metadata["group_column"]
    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    upper_error = (
        table[ci_upper]
        - table[estimate]
    )

    lower_error = (
        table[estimate]
        - table[ci_lower]
    )

    customdata = table[
        [
            ci_lower,
            ci_upper,
            denominator_n,
            numerator_n,
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_scatter(
        mode="markers+text",
        marker={"size": 12},
        x=table[group],
        y=table[estimate],
        customdata=customdata,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": upper_error,
            "arrayminus": lower_error,
            "visible": True,
        },
        text=table[estimate],
        texttemplate="%{text:.1f}%",
        textposition="top center",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Weighted estimate: %{y:.1f}%<br>"
            "95% CI: %{customdata[0]:.1f}%–"
            "%{customdata[1]:.1f}%<br>"
            "Denominator n: %{customdata[2]:,.0f}<br>"
            "Numerator n: %{customdata[3]:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        xaxis_title="Wealth quintile",
        yaxis_title="Weighted percent",
        yaxis_range=[0, 100],
        showlegend=False,
        height=430,
        margin={
            "l": 30,
            "r": 20,
            "t": 20,
            "b": 30,
        },
    )

    return figure


def render_wealth_equity(selected):
    """Render P2_V3 using the five frozen wealth sources."""

    contract = selected.loc[
        selected["visual_id"].eq("P2_V3")
    ]

    if len(contract) != 1:
        raise DashboardDataError(
            "Expected one P2_V3 wealth contract."
        )

    contract = contract.iloc[0]

    specifications = load_specifications()
    registry = specifications["equity"]

    approved_sources = {
        item.strip()
        for item
        in contract["source_paths"].split(";")
        if item.strip()
    }

    registry_sources = set(
        registry["wealth_source"]
    )

    if approved_sources != registry_sources:
        raise DashboardDataError(
            "Wealth sources do not match "
            "the approved P2_V3 blueprint."
        )

    indicators = (
        registry["indicator"]
        .tolist()
    )

    st.header(
        "3. Wealth equity"
    )

    st.markdown(
        "Choose an ANC indicator. The denominator and "
        "corresponding frozen source change together."
    )

    indicator = st.selectbox(
        "Wealth indicator",
        indicators,
        key="wealth_indicator",
    )

    table, metadata = wealth_equity_table(
        indicator
    )

    st.caption(
        "Evidence denominator: "
        + metadata["denominator"]
    )

    figure = wealth_equity_figure(
        table,
        metadata,
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="wealth_equity_chart",
    )

    st.caption(
        "Points show frozen weighted percentages by wealth quintile. "
        "Error bars use the frozen 95% confidence intervals. "
        "Changing the selector switches between approved frozen "
        "tables; estimates are not recalculated."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Wealth equity: exact frozen values and source"
    ):
        st.markdown(
            "**Selected indicator:** "
            + indicator
        )

        st.markdown(
            "**Denominator:** "
            + metadata["denominator"]
        )

        st.dataframe(
            table.reset_index(
                drop=True
            ),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + metadata["wealth_source"]
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "This is descriptive subgroup evidence. "
            "The display does not estimate a wealth effect, "
            "adjust for other characteristics or establish causality."
        )



def travel_equity_table(indicator):
    """Load and validate one frozen travel-time indicator."""

    table, metadata = load_indicator(
        "travel",
        indicator,
    )

    group = metadata["group_column"]
    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    required = [
        group,
        denominator_n,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    missing = sorted(
        set(required)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Travel-time table is missing columns: "
            + str(missing)
        )

    if len(table) != 4:
        raise DashboardDataError(
            "Travel-time table must contain four categories."
        )

    if table[group].tolist() != TRAVEL_ORDER:
        raise DashboardDataError(
            "Unexpected travel-time category order."
        )

    if table[group].duplicated().any():
        raise DashboardDataError(
            "Travel-time categories must be unique."
        )

    numeric_columns = [
        denominator_n,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Travel-time field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Travel-time table contains non-finite values."
        )

    if not table[denominator_n].gt(0).all():
        raise DashboardDataError(
            "Travel-time denominator counts must be positive."
        )

    if not table[numerator_n].ge(0).all():
        raise DashboardDataError(
            "Travel-time numerator counts cannot be negative."
        )

    if not (
        table[numerator_n]
        <= table[denominator_n]
    ).all():
        raise DashboardDataError(
            "Travel-time numerator exceeds denominator."
        )

    for column in [
        estimate,
        ci_lower,
        ci_upper,
    ]:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Travel-time percentage outside 0-100: {column}"
            )

    if not (
        table[ci_lower]
        <= table[estimate]
    ).all():
        raise DashboardDataError(
            "Travel-time estimate falls below its CI."
        )

    if not (
        table[estimate]
        <= table[ci_upper]
    ).all():
        raise DashboardDataError(
            "Travel-time estimate exceeds its CI."
        )

    return table, metadata


def travel_equity_figure(table, metadata):
    """Build a presentation-only travel-time equity chart."""

    group = metadata["group_column"]
    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    upper_error = (
        table[ci_upper]
        - table[estimate]
    )

    lower_error = (
        table[estimate]
        - table[ci_lower]
    )

    customdata = table[
        [
            ci_lower,
            ci_upper,
            denominator_n,
            numerator_n,
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_bar(
        x=table[group],
        y=table[estimate],
        customdata=customdata,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": upper_error,
            "arrayminus": lower_error,
            "visible": True,
        },
        text=table[estimate],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        insidetextanchor="end",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Weighted estimate: %{y:.1f}%<br>"
            "95% CI: %{customdata[0]:.1f}%–"
            "%{customdata[1]:.1f}%<br>"
            "Denominator n: %{customdata[2]:,.0f}<br>"
            "Numerator n: %{customdata[3]:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        xaxis_title="Travel time",
        yaxis_title="Weighted percent",
        yaxis_range=[0, 100],
        showlegend=False,
        height=430,
        margin={
            "l": 30,
            "r": 20,
            "t": 20,
            "b": 30,
        },
    )

    return figure


def render_travel_equity(selected):
    """Render P2_V4 using the five frozen travel-time sources."""

    contract = selected.loc[
        selected["visual_id"].eq("P2_V4")
    ]

    if len(contract) != 1:
        raise DashboardDataError(
            "Expected one P2_V4 travel-time contract."
        )

    contract = contract.iloc[0]

    specifications = load_specifications()
    registry = specifications["equity"]

    approved_sources = {
        item.strip()
        for item
        in contract["source_paths"].split(";")
        if item.strip()
    }

    registry_sources = set(
        registry["travel_source"]
    )

    if approved_sources != registry_sources:
        raise DashboardDataError(
            "Travel-time sources do not match "
            "the approved P2_V4 blueprint."
        )

    indicators = (
        registry["indicator"]
        .tolist()
    )

    st.header(
        "4. Travel-time equity"
    )

    st.markdown(
        "Choose an ANC indicator. The denominator and "
        "corresponding frozen source change together."
    )

    indicator = st.selectbox(
        "Travel-time indicator",
        indicators,
        key="travel_indicator",
    )

    table, metadata = travel_equity_table(
        indicator
    )

    st.caption(
        "Evidence denominator: "
        + metadata["denominator"]
    )

    figure = travel_equity_figure(
        table,
        metadata,
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="travel_equity_chart",
    )

    st.caption(
        "Bars show frozen weighted percentages by empirical "
        "travel-time category. Error bars use the frozen "
        "95% confidence intervals. Categories are presentation "
        "bands rather than clinical thresholds."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Travel-time equity: exact frozen values and source"
    ):
        st.markdown(
            "**Selected indicator:** "
            + indicator
        )

        st.markdown(
            "**Denominator:** "
            + metadata["denominator"]
        )

        st.dataframe(
            table.reset_index(
                drop=True
            ),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + metadata["travel_source"]
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "Travel-time groups are empirical categories from "
            "the frozen evidence package. The display does not "
            "estimate a causal travel-time effect or define "
            "clinical accessibility thresholds."
        )



def regional_equity_table(indicator):
    """Load and validate one frozen regional ANC indicator."""

    table, metadata = load_indicator(
        "region",
        indicator,
    )

    geography, crosswalk = load_geography()

    group = metadata["group_column"]
    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    psu = metadata["psu_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    required = [
        group,
        denominator_n,
        psu,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    missing = sorted(
        set(required)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Regional table is missing columns: "
            + str(missing)
        )

    if len(table) != 14:
        raise DashboardDataError(
            "Regional table must contain 14 analytical regions."
        )

    if (
        table[group].isna().any()
        or table[group].duplicated().any()
    ):
        raise DashboardDataError(
            "Regional labels must be complete and unique."
        )

    numeric_columns = [
        denominator_n,
        psu,
        numerator_n,
        estimate,
        ci_lower,
        ci_upper,
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Regional field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Regional table contains non-finite values."
        )

    if not table[denominator_n].gt(0).all():
        raise DashboardDataError(
            "Regional denominator counts must be positive."
        )

    if not table[numerator_n].ge(0).all():
        raise DashboardDataError(
            "Regional numerator counts cannot be negative."
        )

    if not (
        table[numerator_n]
        <= table[denominator_n]
    ).all():
        raise DashboardDataError(
            "Regional numerator exceeds denominator."
        )

    if not table[psu].gt(0).all():
        raise DashboardDataError(
            "Regional PSU counts must be positive."
        )

    for column in [
        estimate,
        ci_lower,
        ci_upper,
    ]:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Regional percentage outside 0-100: {column}"
            )

    if not (
        table[ci_lower]
        <= table[estimate]
    ).all():
        raise DashboardDataError(
            "Regional estimate falls below its CI."
        )

    if not (
        table[estimate]
        <= table[ci_upper]
    ).all():
        raise DashboardDataError(
            "Regional estimate exceeds its CI."
        )

    analytical = (
        crosswalk.loc[
            crosswalk["analytical_region"]
        ]
        .copy()
    )

    nonanalytical = (
        crosswalk.loc[
            ~crosswalk["analytical_region"]
        ]
        .copy()
    )

    if len(analytical) != 14:
        raise DashboardDataError(
            "Expected 14 analytical map regions."
        )

    if len(nonanalytical) != 1:
        raise DashboardDataError(
            "Expected one non-analytical map feature."
        )

    if set(table[group]) != set(
        analytical["nb4_region"]
    ):
        raise DashboardDataError(
            "Regional evidence does not match "
            "the analytical geography crosswalk."
        )

    map_table = analytical[
        [
            "dashboard_region",
            "nb4_region",
        ]
    ].merge(
        table,
        left_on="nb4_region",
        right_on=group,
        how="left",
        validate="one_to_one",
    )

    if len(map_table) != 14:
        raise DashboardDataError(
            "Regional map join did not retain 14 analytical regions."
        )

    if map_table[estimate].isna().any():
        raise DashboardDataError(
            "Regional map join produced a missing estimate."
        )

    return table, metadata, geography, crosswalk, map_table


def regional_equity_figure(
    table,
    metadata,
    geography,
    crosswalk,
    map_table,
):
    """Build the display-only regional choropleth."""

    estimate = metadata["estimate_column"]
    denominator_n = metadata["denominator_n_column"]
    numerator_n = metadata["numerator_n_column"]
    psu = metadata["psu_column"]
    ci_lower = metadata["ci_lower_column"]
    ci_upper = metadata["ci_upper_column"]

    customdata = map_table[
        [
            "nb4_region",
            ci_lower,
            ci_upper,
            denominator_n,
            numerator_n,
            psu,
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_trace(
        go.Choropleth(
            geojson=geography,
            featureidkey="properties.region",
            locations=map_table["dashboard_region"],
            z=map_table[estimate],
            zmin=0,
            zmax=100,
            colorscale="Blues",
            colorbar={
                "title": "Weighted %",
            },
            customdata=customdata,
            marker_line_width=0.7,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Weighted estimate: %{z:.1f}%<br>"
                "95% CI: %{customdata[1]:.1f}%–"
                "%{customdata[2]:.1f}%<br>"
                "Denominator n: %{customdata[3]:,.0f}<br>"
                "Numerator n: %{customdata[4]:,.0f}<br>"
                "PSUs: %{customdata[5]:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    nonanalytical = (
        crosswalk.loc[
            ~crosswalk["analytical_region"]
        ]
        .copy()
    )

    figure.add_trace(
        go.Choropleth(
            geojson=geography,
            featureidkey="properties.region",
            locations=nonanalytical["dashboard_region"],
            z=[0] * len(nonanalytical),
            zmin=0,
            zmax=1,
            colorscale=[
                [0.0, "lightgray"],
                [1.0, "lightgray"],
            ],
            showscale=False,
            marker_line_width=0.7,
            hovertemplate=(
                "<b>%{location}</b><br>"
                "No analytical ANC estimate assigned"
                "<extra></extra>"
            ),
        )
    )

    figure.update_geos(
        fitbounds="locations",
        visible=False,
    )

    figure.update_layout(
        height=650,
        margin={
            "l": 0,
            "r": 0,
            "t": 10,
            "b": 0,
        },
    )

    return figure


def render_regional_equity(selected):
    """Render P2_V5 using the five frozen regional sources."""

    contract = selected.loc[
        selected["visual_id"].eq("P2_V5")
    ]

    if len(contract) != 1:
        raise DashboardDataError(
            "Expected one P2_V5 regional-map contract."
        )

    contract = contract.iloc[0]

    specifications = load_specifications()
    registry = specifications["regional"]

    approved_sources = {
        item.strip()
        for item
        in contract["source_paths"].split(";")
        if item.strip()
    }

    regional_sources = set(
        registry["region_source"]
    )

    geography_sources = {
        "geography/ethiopia_admin1_dashboard.geojson",
        "geography/region_name_crosswalk.csv",
    }

    if not regional_sources.issubset(
        approved_sources
    ):
        raise DashboardDataError(
            "Regional indicator sources do not match "
            "the approved P2_V5 blueprint."
        )

    if not geography_sources.issubset(
        approved_sources
    ):
        raise DashboardDataError(
            "Regional map geography is not fully registered "
            "in the approved P2_V5 blueprint."
        )

    indicators = (
        registry["indicator"]
        .tolist()
    )

    st.header(
        "5. Regional equity map"
    )

    st.markdown(
        "Choose an ANC indicator. The denominator and "
        "corresponding frozen regional estimates change together."
    )

    indicator = st.selectbox(
        "Regional indicator",
        indicators,
        key="regional_indicator",
    )

    (
        table,
        metadata,
        geography,
        crosswalk,
        map_table,
    ) = regional_equity_table(
        indicator
    )

    st.caption(
        "Evidence denominator: "
        + metadata["denominator"]
    )

    figure = regional_equity_figure(
        table,
        metadata,
        geography,
        crosswalk,
        map_table,
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="regional_equity_map",
    )

    st.caption(
        "Map shading shows frozen weighted regional estimates "
        "on a common 0–100% scale. Hover for the frozen 95% CI, "
        "denominator, numerator and PSU count."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Regional equity map: exact frozen values and source"
    ):
        st.markdown(
            "**Selected indicator:** "
            + indicator
        )

        st.markdown(
            "**Denominator:** "
            + metadata["denominator"]
        )

        st.dataframe(
            table.reset_index(
                drop=True
            ),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Regional source:** `"
            + metadata["region_source"]
            + "`"
        )

        st.markdown(
            "**Geography:** "
            "`geography/ethiopia_admin1_dashboard.geojson` "
            "with `geography/region_name_crosswalk.csv`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "The map assigns only the 14 analytical Notebook 4 "
            "regional estimates. The separate non-analytical "
            "boundary feature remains visible without an ANC estimate. "
            "No interpolation, spatial modelling or geographic "
            "reassignment is performed."
        )



def regional_diagnostic_table():
    """Load and validate the frozen regional diagnostic synthesis."""

    table = load_frozen_table(
        DIAGNOSTIC_SOURCE
    )

    missing = sorted(
        set(DIAGNOSTIC_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Regional diagnostic table is missing columns: "
            + str(missing)
        )

    if len(table) != 14:
        raise DashboardDataError(
            "Regional diagnostic table must contain 14 regions."
        )

    if (
        table["Region"].isna().any()
        or table["Region"].duplicated().any()
    ):
        raise DashboardDataError(
            "Regional diagnostic labels must be complete and unique."
        )

    numeric_columns = (
        DIAGNOSTIC_PERCENT_COLUMNS
        + DIAGNOSTIC_GAP_COLUMNS
    )

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Regional diagnostic field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Regional diagnostic table contains non-finite values."
        )

    for column in DIAGNOSTIC_PERCENT_COLUMNS:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Regional percentage outside 0-100: {column}"
            )

    for column in DIAGNOSTIC_GAP_COLUMNS:
        if not table[column].between(
            -100,
            100,
        ).all():
            raise DashboardDataError(
                f"Regional gap outside -100 to 100 pp: {column}"
            )

    geography, crosswalk = load_geography()

    analytical = crosswalk.loc[
        crosswalk["analytical_region"]
    ]

    if set(table["Region"]) != set(
        analytical["nb4_region"]
    ):
        raise DashboardDataError(
            "Regional diagnostic table does not match "
            "the 14 analytical geography regions."
        )

    return table


def render_regional_diagnostic(selected):
    """Render P2_V6 from the frozen regional diagnostic table."""

    contract = selected.loc[
        selected["visual_id"].eq("P2_V6")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != DIAGNOSTIC_SOURCE
    ):
        raise DashboardDataError(
            "Regional diagnostic table does not match "
            "the approved P2_V6 blueprint."
        )

    contract = contract.iloc[0]

    table = regional_diagnostic_table()

    st.header(
        "6. Regional diagnostic table"
    )

    st.caption(
        "Evidence population: "
        + contract["denominator_note"]
    )

    st.markdown(
        "The table brings the five approved regional indicators "
        "and their frozen percentage-point gap fields together "
        "for review. Regions remain in the source order; no "
        "composite score or ranking is created."
    )

    st.dataframe(
        table[DIAGNOSTIC_COLUMNS]
        .reset_index(drop=True),
        hide_index=True,
        width="stretch",
        height=540,
        column_config={
            **{
                column: st.column_config.NumberColumn(
                    column,
                    format="%.1f%%",
                )
                for column
                in DIAGNOSTIC_PERCENT_COLUMNS
            },
            **{
                column: st.column_config.NumberColumn(
                    column,
                    format="%+.1f pp",
                )
                for column
                in DIAGNOSTIC_GAP_COLUMNS
            },
        },
    )

    st.caption(
        "Percentage columns are frozen regional estimates. "
        "Gap columns are frozen percentage-point fields from "
        "Notebook 4. Positive and negative signs are retained "
        "as supplied; the dashboard does not recompute them."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Regional diagnostic table: source and interpretation"
    ):
        st.markdown(
            "**Source:** `"
            + DIAGNOSTIC_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "This table supports regional review only. "
            "It does not construct a league table, overall "
            "performance score or causal programme assessment."
        )




def render_attendance_equity():
    """Render Page 2, currently implemented through P2_V1."""
    st.caption(
        "ANC8+ Programme Review · Page 2 of 4"
    )

    st.title(
        "Attendance and equity"
    )

    st.markdown(
        "### Where are the observed ANC attendance "
        "and equity gaps?"
    )

    st.info(
        "Each indicator has its own denominator. "
        "Descriptive differences are not causal effects; "
        "Contested geography remains non-analytical."
    )

    st.caption(
        "Development preview · all six Attendance and Equity "
        "displays are implemented. Pages 3–4 remain development previews."
    )

    try:
        selected = page2_contract()

        contract = selected.loc[
            selected["visual_id"].eq("P2_V1")
        ]

        if (
            len(contract) != 1
            or contract.iloc[0]["source_paths"]
            != ATTENDANCE_SOURCE
        ):
            raise DashboardDataError(
                "Attendance profile does not match "
                "the approved P2_V1 blueprint."
            )

        contract = contract.iloc[0]

        table = attendance_profile_table()

        st.header(
            "1. Final ANC attendance profile"
        )

        st.caption(
            "Evidence population: "
            + contract["denominator_note"]
        )

        st.markdown(
            "The four categories describe the final distribution "
            "of ANC contacts in the resolved analytical population."
        )

        figure = attendance_profile_figure(
            table
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key="attendance_profile_chart",
        )

        st.caption(
            "Bars show frozen weighted percentages. "
            "Error bars use the frozen 95% confidence-interval "
            "endpoints from Notebook 4."
        )

        st.info(
            contract["interpretation_boundary"]
        )

        with st.expander(
            "Attendance profile: exact frozen values and source"
        ):
            st.dataframe(
                table[ATTENDANCE_COLUMNS]
                .reset_index(drop=True),
                hide_index=True,
                width="stretch",
            )

            st.markdown(
                "**Source:** `"
                + ATTENDANCE_SOURCE
                + "`"
            )

            st.markdown(
                "**Interpretation boundary:** "
                + contract[
                    "interpretation_boundary"
                ]
            )

            st.markdown(
                "The application reads the saved aggregate "
                "distribution only. It does not reconstruct "
                "individual ANC trajectories or estimate "
                "longitudinal dropout."
            )

        st.divider()

        render_anc_pathway(
            selected
        )

        st.divider()

        render_wealth_equity(
            selected
        )

        st.divider()

        render_travel_equity(
            selected
        )

        st.divider()

        render_regional_equity(
            selected
        )

        st.divider()

        render_regional_diagnostic(
            selected
        )

    except (
        DashboardDataError,
        OSError,
        KeyError,
        ValueError,
    ) as exc:
        st.error(
            "The Attendance and Equity evidence could not "
            "be displayed. Please contact the dashboard maintainer."
        )

        with st.expander(
            "Validation details"
        ):
            st.code(str(exc))

        st.stop()
