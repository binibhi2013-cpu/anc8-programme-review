"""Page 3: frozen timing and continuation evidence."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils.presentation import ui as st

from utils.data_loader import (
    DashboardDataError,
    load_frozen_table,
    load_specifications,
)


TIMING_ANC8_SOURCE = (
    "dashboard_attendance/timing_anc8_reporting.csv"
)

TIMING_ANC8_COLUMNS = [
    "timing_group",
    "unweighted_n",
    "anc8plus_n",
    "below_anc8_n",
    "anc8plus_percent",
    "ci_lower_percent",
    "ci_upper_percent",
    "below_anc8_percent",
]

TIMING_GROUP_ORDER = [
    "Later initiation",
    "Early initiation",
]



TIMING_PATHWAY_SOURCE = (
    "dashboard_attendance/timing_pathway_reporting.csv"
)

TIMING_PATHWAY_COLUMNS = [
    "timing_group",
    "timing_unweighted_n",
    "anc4plus_n",
    "anc4plus_percent",
    "anc4plus_ci_lower",
    "anc4plus_ci_upper",
    "anc8plus_n",
    "anc8_given_anc4_percent",
    "anc8_given_anc4_ci_lower",
    "anc8_given_anc4_ci_upper",
    "below_anc8_after_anc4_percent",
]



REGION_TIMING_SOURCE = (
    "dashboard_attendance/region_timing_synthesis.csv"
)

REGION_TIMING_COLUMNS = [
    "Region",
    "Any ANC %",
    "ANC4+ among ANC users %",
    "ANC8+ among ANC4+ %",
    "Early ANC %",
    "ANC8+ among early initiators %",
]


def page3_contract():
    """Return the three ordered Page 3 visual contracts."""

    visual = load_specifications()["visual"]

    selected = visual.loc[
        visual["page_order"].eq("3")
    ].copy()

    if len(selected) != 3:
        raise DashboardDataError(
            "Page 3 must contain exactly three visual contracts."
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
        "P3_V1",
        "P3_V2",
        "P3_V3",
    }

    if set(selected["visual_id"]) != expected_ids:
        raise DashboardDataError(
            "Page 3 visual IDs do not match the approved blueprint."
        )

    return selected


def timing_anc8_table():
    """Load and validate the frozen initiation-timing ANC8 table."""

    table = load_frozen_table(
        TIMING_ANC8_SOURCE
    )

    missing = sorted(
        set(TIMING_ANC8_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Timing ANC8 table is missing columns: "
            + str(missing)
        )

    if len(table) != 2:
        raise DashboardDataError(
            "Timing ANC8 table must contain two groups."
        )

    if (
        table["timing_group"].tolist()
        != TIMING_GROUP_ORDER
    ):
        raise DashboardDataError(
            "Unexpected initiation-timing group order."
        )

    if table["timing_group"].duplicated().any():
        raise DashboardDataError(
            "Timing groups must be unique."
        )

    numeric_columns = [
        "unweighted_n",
        "anc8plus_n",
        "below_anc8_n",
        "anc8plus_percent",
        "ci_lower_percent",
        "ci_upper_percent",
        "below_anc8_percent",
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Timing field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Timing ANC8 table contains non-finite values."
        )

    if not table["unweighted_n"].gt(0).all():
        raise DashboardDataError(
            "Timing denominators must be positive."
        )

    if not (
        table["anc8plus_n"]
        + table["below_anc8_n"]
        == table["unweighted_n"]
    ).all():
        raise DashboardDataError(
            "Timing ANC8 counts do not reconcile with denominator."
        )

    for column in [
        "anc8plus_percent",
        "ci_lower_percent",
        "ci_upper_percent",
        "below_anc8_percent",
    ]:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Timing percentage outside 0-100: {column}"
            )

    if not (
        table["ci_lower_percent"]
        <= table["anc8plus_percent"]
    ).all():
        raise DashboardDataError(
            "Timing ANC8 estimate falls below its CI."
        )

    if not (
        table["anc8plus_percent"]
        <= table["ci_upper_percent"]
    ).all():
        raise DashboardDataError(
            "Timing ANC8 estimate exceeds its CI."
        )

    if not np.allclose(
        (
            table["anc8plus_percent"]
            + table["below_anc8_percent"]
        ),
        100.0,
        atol=0.05,
    ):
        raise DashboardDataError(
            "ANC8+ and below-ANC8 percentages "
            "do not sum to approximately 100%."
        )

    return table


def timing_anc8_figure(table):
    """Build the presentation-only early/later ANC8 chart."""

    upper_error = (
        table["ci_upper_percent"]
        - table["anc8plus_percent"]
    )

    lower_error = (
        table["anc8plus_percent"]
        - table["ci_lower_percent"]
    )

    customdata = table[
        [
            "ci_lower_percent",
            "ci_upper_percent",
            "unweighted_n",
            "anc8plus_n",
            "below_anc8_n",
            "below_anc8_percent",
        ]
    ].to_numpy()

    figure = go.Figure()

    figure.add_bar(
        x=table["timing_group"],
        y=table["anc8plus_percent"],
        customdata=customdata,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": upper_error,
            "arrayminus": lower_error,
            "visible": True,
        },
        text=table["anc8plus_percent"],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        insidetextanchor="end",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "ANC8+: %{y:.1f}%<br>"
            "95% CI: %{customdata[0]:.1f}%–"
            "%{customdata[1]:.1f}%<br>"
            "Unweighted n: %{customdata[2]:,.0f}<br>"
            "ANC8+ n: %{customdata[3]:,.0f}<br>"
            "Below ANC8 n: %{customdata[4]:,.0f}<br>"
            "Below ANC8: %{customdata[5]:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        xaxis_title="ANC initiation timing",
        yaxis_title="ANC8+ weighted percent",
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



def timing_pathway_table():
    """Load and validate the frozen timing-specific pathway."""

    table = load_frozen_table(
        TIMING_PATHWAY_SOURCE
    )

    missing = sorted(
        set(TIMING_PATHWAY_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Timing pathway is missing columns: "
            + str(missing)
        )

    if len(table) != 2:
        raise DashboardDataError(
            "Timing pathway must contain two timing groups."
        )

    if (
        table["timing_group"].tolist()
        != TIMING_GROUP_ORDER
    ):
        raise DashboardDataError(
            "Unexpected timing-pathway group order."
        )

    if table["timing_group"].duplicated().any():
        raise DashboardDataError(
            "Timing-pathway groups must be unique."
        )

    numeric_columns = [
        "timing_unweighted_n",
        "anc4plus_n",
        "anc4plus_percent",
        "anc4plus_ci_lower",
        "anc4plus_ci_upper",
        "anc8plus_n",
        "anc8_given_anc4_percent",
        "anc8_given_anc4_ci_lower",
        "anc8_given_anc4_ci_upper",
        "below_anc8_after_anc4_percent",
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Timing-pathway field must be numeric: {column}"
            )

    if not np.isfinite(
        table[numeric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Timing pathway contains non-finite values."
        )

    if not table["timing_unweighted_n"].gt(0).all():
        raise DashboardDataError(
            "Timing-group denominators must be positive."
        )

    if not (
        table["anc4plus_n"]
        <= table["timing_unweighted_n"]
    ).all():
        raise DashboardDataError(
            "ANC4+ count exceeds timing-group denominator."
        )

    if not (
        table["anc8plus_n"]
        <= table["anc4plus_n"]
    ).all():
        raise DashboardDataError(
            "ANC8+ count exceeds ANC4+ denominator."
        )

    percent_columns = [
        "anc4plus_percent",
        "anc4plus_ci_lower",
        "anc4plus_ci_upper",
        "anc8_given_anc4_percent",
        "anc8_given_anc4_ci_lower",
        "anc8_given_anc4_ci_upper",
        "below_anc8_after_anc4_percent",
    ]

    for column in percent_columns:
        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Timing-pathway percentage outside 0-100: {column}"
            )

    if not (
        table["anc4plus_ci_lower"]
        <= table["anc4plus_percent"]
    ).all():
        raise DashboardDataError(
            "ANC4+ estimate falls below its CI."
        )

    if not (
        table["anc4plus_percent"]
        <= table["anc4plus_ci_upper"]
    ).all():
        raise DashboardDataError(
            "ANC4+ estimate exceeds its CI."
        )

    if not (
        table["anc8_given_anc4_ci_lower"]
        <= table["anc8_given_anc4_percent"]
    ).all():
        raise DashboardDataError(
            "Conditional ANC8+ estimate falls below its CI."
        )

    if not (
        table["anc8_given_anc4_percent"]
        <= table["anc8_given_anc4_ci_upper"]
    ).all():
        raise DashboardDataError(
            "Conditional ANC8+ estimate exceeds its CI."
        )

    if not np.allclose(
        (
            table["anc8_given_anc4_percent"]
            + table["below_anc8_after_anc4_percent"]
        ),
        100.0,
        atol=0.05,
    ):
        raise DashboardDataError(
            "Conditional ANC8+ and below-ANC8 percentages "
            "do not sum to approximately 100%."
        )

    return table


def timing_pathway_figure(table):
    """Build grouped conditional-attainment bars."""

    figure = go.Figure()

    anc4_upper = (
        table["anc4plus_ci_upper"]
        - table["anc4plus_percent"]
    )

    anc4_lower = (
        table["anc4plus_percent"]
        - table["anc4plus_ci_lower"]
    )

    anc8_upper = (
        table["anc8_given_anc4_ci_upper"]
        - table["anc8_given_anc4_percent"]
    )

    anc8_lower = (
        table["anc8_given_anc4_percent"]
        - table["anc8_given_anc4_ci_lower"]
    )

    anc4_custom = table[
        [
            "timing_unweighted_n",
            "anc4plus_n",
            "anc4plus_ci_lower",
            "anc4plus_ci_upper",
        ]
    ].to_numpy()

    anc8_custom = table[
        [
            "anc4plus_n",
            "anc8plus_n",
            "anc8_given_anc4_ci_lower",
            "anc8_given_anc4_ci_upper",
            "below_anc8_after_anc4_percent",
        ]
    ].to_numpy()

    figure.add_bar(
        name="ANC4+ among timing group",
        x=table["timing_group"],
        y=table["anc4plus_percent"],
        customdata=anc4_custom,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": anc4_upper,
            "arrayminus": anc4_lower,
            "visible": True,
        },
        text=table["anc4plus_percent"],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "ANC4+: %{y:.1f}%<br>"
            "95% CI: %{customdata[2]:.1f}%–"
            "%{customdata[3]:.1f}%<br>"
            "Timing-group denominator n: %{customdata[0]:,.0f}<br>"
            "ANC4+ n: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.add_bar(
        name="ANC8+ among ANC4+",
        x=table["timing_group"],
        y=table["anc8_given_anc4_percent"],
        customdata=anc8_custom,
        error_y={
            "type": "data",
            "symmetric": False,
            "array": anc8_upper,
            "arrayminus": anc8_lower,
            "visible": True,
        },
        text=table["anc8_given_anc4_percent"],
        texttemplate="%{text:.1f}%",
        textposition="inside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "ANC8+ among ANC4+: %{y:.1f}%<br>"
            "95% CI: %{customdata[2]:.1f}%–"
            "%{customdata[3]:.1f}%<br>"
            "ANC4+ denominator n: %{customdata[0]:,.0f}<br>"
            "ANC8+ n: %{customdata[1]:,.0f}<br>"
            "Below ANC8 after ANC4+: %{customdata[4]:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        barmode="group",
        xaxis_title="ANC initiation timing",
        yaxis_title="Conditional weighted attainment (%)",
        yaxis_range=[0, 100],
        height=460,
        legend_title_text="Conditional stage",
        margin={
            "l": 30,
            "r": 20,
            "t": 20,
            "b": 30,
        },
    )

    return figure


def render_timing_pathway(selected):
    """Render P3_V2 from the frozen timing pathway."""

    contract = selected.loc[
        selected["visual_id"].eq("P3_V2")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != TIMING_PATHWAY_SOURCE
    ):
        raise DashboardDataError(
            "Timing pathway does not match "
            "the approved P3_V2 blueprint."
        )

    contract = contract.iloc[0]

    table = timing_pathway_table()

    st.header(
        "2. Timing-specific ANC pathway"
    )

    st.caption(
        "Evidence population: "
        + contract["denominator_note"]
    )

    st.markdown(
        "The two bars within each timing group use different "
        "eligible populations. ANC4+ is conditional on membership "
        "in the timing group, while ANC8+ is conditional on already "
        "having attained ANC4+."
    )

    figure = timing_pathway_figure(
        table
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="timing_pathway_chart",
    )

    st.caption(
        "Bars show frozen conditional weighted attainment. "
        "Confidence intervals and counts are copied from Notebook 4."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Timing-specific pathway: exact frozen values and source"
    ):

        st.dataframe(
            table[
                TIMING_PATHWAY_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
        )

        st.markdown(
            "**Source:** `"
            + TIMING_PATHWAY_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "The two stages use different denominators. "
            "These conditional estimates are not directly "
            "observed dropout, mediation effects or causal "
            "effects of initiation timing."
        )



def regional_timing_table():
    """Load and validate the frozen regional timing synthesis."""

    table = load_frozen_table(
        REGION_TIMING_SOURCE
    )

    missing = sorted(
        set(REGION_TIMING_COLUMNS)
        - set(table.columns)
    )

    if missing:
        raise DashboardDataError(
            "Regional timing synthesis is missing columns: "
            + str(missing)
        )

    if len(table) != 14:
        raise DashboardDataError(
            "Regional timing synthesis must contain 14 regions."
        )

    if (
        table["Region"].isna().any()
        or table["Region"].duplicated().any()
    ):
        raise DashboardDataError(
            "Regional timing labels must be complete and unique."
        )

    metric_columns = REGION_TIMING_COLUMNS[1:]

    for column in metric_columns:

        if not pd.api.types.is_numeric_dtype(
            table[column]
        ):
            raise DashboardDataError(
                f"Regional timing field must be numeric: {column}"
            )

        if not table[column].between(
            0,
            100,
        ).all():
            raise DashboardDataError(
                f"Regional timing percentage outside 0-100: {column}"
            )

    if not np.isfinite(
        table[metric_columns].to_numpy()
    ).all():
        raise DashboardDataError(
            "Regional timing synthesis contains non-finite values."
        )

    return table


def regional_timing_figure(table):
    """Build the descriptive regional synthesis heatmap."""

    metric_columns = REGION_TIMING_COLUMNS[1:]

    z = table[
        metric_columns
    ].to_numpy()

    text = np.vectorize(
        lambda value: f"{value:.1f}%"
    )(z)

    figure = go.Figure(
        data=go.Heatmap(
            z=z,
            x=metric_columns,
            y=table["Region"],
            zmin=0,
            zmax=100,
            colorscale="Blues",
            colorbar={
                "title": "Weighted %",
            },
            text=text,
            texttemplate="%{text}",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x}: %{z:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        height=650,
        margin={
            "l": 40,
            "r": 20,
            "t": 20,
            "b": 80,
        },
    )

    figure.update_xaxes(
        tickangle=-25
    )

    return figure


def render_regional_timing(selected):
    """Render P3_V3 from the frozen regional synthesis."""

    contract = selected.loc[
        selected["visual_id"].eq("P3_V3")
    ]

    if (
        len(contract) != 1
        or contract.iloc[0]["source_paths"]
        != REGION_TIMING_SOURCE
    ):
        raise DashboardDataError(
            "Regional timing synthesis does not match "
            "the approved P3_V3 blueprint."
        )

    contract = contract.iloc[0]

    table = regional_timing_table()

    st.header(
        "3. Regional timing and continuation synthesis"
    )

    st.caption(
        "Evidence population: "
        + contract["denominator_note"]
    )

    st.markdown(
        "The heatmap places five frozen ANC indicators side by "
        "side across the 14 analytical regions. It is intended "
        "for descriptive pattern review rather than regional ranking."
    )

    figure = regional_timing_figure(
        table
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="regional_timing_heatmap",
    )

    st.caption(
        "Cells show frozen weighted percentages. "
        "This synthesis table does not contain confidence intervals."
    )

    st.info(
        contract[
            "interpretation_boundary"
        ]
    )

    with st.expander(
        "Regional timing synthesis: exact frozen values and source"
    ):

        st.dataframe(
            table[
                REGION_TIMING_COLUMNS
            ].reset_index(drop=True),
            hide_index=True,
            width="stretch",
            column_config={
                column:
                    st.column_config.NumberColumn(
                        column,
                        format="%.1f%%",
                    )
                for column
                in REGION_TIMING_COLUMNS[1:]
            },
        )

        st.markdown(
            "**Source:** `"
            + REGION_TIMING_SOURCE
            + "`"
        )

        st.markdown(
            "**Interpretation boundary:** "
            + contract[
                "interpretation_boundary"
            ]
        )

        st.markdown(
            "Confidence intervals are not included in this "
            "synthesis source. Region-specific uncertainty should "
            "be reviewed using the corresponding frozen regional "
            "source tables on Page 2."
        )




def render_timing_continuation():
    """Render Page 3, currently implemented through P3_V1."""

    st.caption(
        "ANC8+ Programme Review · Page 3 of 4"
    )

    st.title(
        "Timing and continuation"
    )

    st.markdown(
        "### How do ANC initiation timing and "
        "subsequent attainment relate?"
    )

    st.info(
        "Observed survey associations and hypothetical "
        "model-response contrasts are separate evidence types. "
        "Conditional attainment is not observed longitudinal dropout."
    )

    st.caption(
        "Development preview · all three "
        "Timing and Continuation displays are implemented. Page 4 remains a development preview."
    )

    try:
        selected = page3_contract()

        contract = selected.loc[
            selected["visual_id"].eq("P3_V1")
        ]

        if (
            len(contract) != 1
            or contract.iloc[0]["source_paths"]
            != TIMING_ANC8_SOURCE
        ):
            raise DashboardDataError(
                "Timing ANC8 display does not match "
                "the approved P3_V1 blueprint."
            )

        contract = contract.iloc[0]

        table = timing_anc8_table()

        st.header(
            "1. Early versus later initiation and ANC8+"
        )

        st.caption(
            "Evidence population: "
            + contract["denominator_note"]
        )

        st.markdown(
            "The bars compare frozen ANC8+ attainment estimates "
            "for women classified as later and early ANC initiators. "
            "They describe observed subgroup differences only."
        )

        figure = timing_anc8_figure(
            table
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key="timing_anc8_chart",
        )

        st.caption(
            "Bars show frozen ANC8+ weighted percentages. "
            "Error bars use the frozen 95% confidence intervals "
            "from Notebook 4."
        )

        st.info(
            contract[
                "interpretation_boundary"
            ]
        )

        with st.expander(
            "Initiation timing and ANC8+: exact frozen values and source"
        ):

            st.dataframe(
                table[
                    TIMING_ANC8_COLUMNS
                ].reset_index(drop=True),
                hide_index=True,
                width="stretch",
            )

            st.markdown(
                "**Source:** `"
                + TIMING_ANC8_SOURCE
                + "`"
            )

            st.markdown(
                "**Interpretation boundary:** "
                + contract[
                    "interpretation_boundary"
                ]
            )

            st.markdown(
                "The application does not estimate an adjusted "
                "timing effect, intervention benefit or causal "
                "effect of early initiation."
            )

        st.divider()

        render_timing_pathway(
            selected
        )

        st.divider()

        render_regional_timing(
            selected
        )

    except (
        DashboardDataError,
        OSError,
        KeyError,
        ValueError,
    ) as exc:

        st.error(
            "The Timing and Continuation evidence could not "
            "be displayed. Please contact the dashboard maintainer."
        )

        with st.expander(
            "Validation details"
        ):
            st.code(str(exc))

        st.stop()
