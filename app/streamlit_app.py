"""Streamlit presentation layer for measured US liquidity data."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from open_global_liquidity.dashboard import (
    COMPONENT_LABELS,
    DashboardDataError,
    latest_readings,
    load_dashboard_data,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "us_fred_series.parquet"
SNAPSHOT_DATA_PATH = PROJECT_ROOT / "data" / "reference" / "us_fred_series_snapshot.parquet"
COMPONENT_ORDER = list(COMPONENT_LABELS)
COLORS = {
    "Fed total assets": "#2563EB",
    "Treasury General Account": "#D97706",
    "ON reverse repo": "#7C3AED",
    "Reserve balances": "#059669",
}


@st.cache_data(show_spinner=False)
def _load_data(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache processed data until its file modification timestamp changes."""
    del modified_ns
    return load_dashboard_data(Path(path))


def _format_billions(value: float) -> str:
    return f"${value:,.1f}bn"


def _history_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="value_usd_billions",
        color="label",
        color_discrete_map=COLORS,
        labels={"date": "", "value_usd_billions": "USD billions", "label": "Series"},
        title=title,
    )
    figure.update_traces(line={"width": 2})
    figure.update_layout(
        hovermode="x unified",
        legend_title_text="",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"gridcolor": "rgba(128,128,128,0.18)", "tickprefix": "$", "ticksuffix": "bn"},
    )
    return figure


st.set_page_config(
    page_title="Open Global Liquidity",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 3.5rem; padding-bottom: 3rem; max-width: 1500px;}
    [data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.22); padding: 1rem; border-radius: .75rem;
    }
    [data-testid="stMetricValue"] {font-size: clamp(1.45rem, 2.2vw, 2rem);}
    .ogli-kicker {
        color: #64748b; font-size: .78rem; font-weight: 700; letter-spacing: .12em;
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="ogli-kicker">Measured data monitor · v0.1</div>', unsafe_allow_html=True)
st.title("Open Global Liquidity")
st.caption(
    "A transparent public-data research dashboard. This measured-data view is not yet OGLI and "
    "does not reproduce CrossBorder Capital's proprietary GLI."
)

try:
    if PROCESSED_DATA_PATH.is_file():
        data_path = PROCESSED_DATA_PATH
        data_origin = "Local processed data"
    elif SNAPSHOT_DATA_PATH.is_file():
        data_path = SNAPSHOT_DATA_PATH
        data_origin = "Bundled public snapshot"
    else:
        raise DashboardDataError(
            "No dashboard data is available. Run the pipeline locally or publish a dashboard "
            "snapshot."
        )
except DashboardDataError as data_path_error:
    st.error(str(data_path_error))
    st.code(
        "uv run python -m open_global_liquidity.pipeline --start 2020-01-01 "
        "--publish-dashboard-snapshot",
        language="zsh",
    )
    st.stop()

try:
    data = _load_data(str(data_path), data_path.stat().st_mtime_ns)
except DashboardDataError as exc:
    st.error(str(exc))
    st.stop()

latest = latest_readings(data).set_index("component")
last_retrieved = pd.to_datetime(data["retrieved_at"].max(), utc=True)

with st.sidebar:
    st.header("View controls")
    window = st.radio("History", ["1 year", "3 years", "5 years", "All"], index=2)
    selected_label = st.selectbox(
        "Component explorer",
        [COMPONENT_LABELS[item] for item in COMPONENT_ORDER if item in set(data["component"])],
    )
    st.divider()
    st.caption(f"Data mode: {data_origin}")
    st.caption(f"Data retrieved {last_retrieved:%Y-%m-%d %H:%M UTC}")
    st.caption("Source: FRED and the named originating Federal Reserve releases.")

max_date = data["date"].max()
window_days = {"1 year": 365, "3 years": 3 * 365, "5 years": 5 * 365}
if window == "All":
    visible = data
else:
    visible = data.loc[data["date"] >= max_date - timedelta(days=window_days[window])]

overview_tab, explorer_tab, data_tab, methodology_tab = st.tabs(
    ["Overview", "Component explorer", "Latest data", "Methodology"]
)

with overview_tab:
    st.subheader("Latest measured balances")
    metric_columns = st.columns(4)
    for column, component in zip(metric_columns, COMPONENT_ORDER, strict=True):
        if component not in latest.index:
            column.metric(COMPONENT_LABELS[component], "Unavailable")
            continue
        row = latest.loc[component]
        change = row["change_usd_billions"]
        delta = None if pd.isna(change) else f"{change:+,.1f}bn vs prior obs."
        column.metric(row["label"], _format_billions(row["value_usd_billions"]), delta)
        column.caption(f"{row['series_id']} · {row['date']:%Y-%m-%d}")

    st.plotly_chart(
        _history_figure(visible, f"US liquidity-related balance-sheet series · {window}"),
        width="stretch",
        config={"displaylogo": False},
    )
    st.info(
        "Values are converted to USD billions only for display. No subtraction, weighting, "
        "normalization, or OGLI calculation is applied in this dashboard version."
    )

with explorer_tab:
    selected_component = next(
        component for component, label in COMPONENT_LABELS.items() if label == selected_label
    )
    component_data = visible.loc[visible["component"] == selected_component]
    st.plotly_chart(
        _history_figure(component_data, selected_label),
        width="stretch",
        config={"displaylogo": False},
    )
    source_row = data.loc[data["component"] == selected_component].iloc[-1]
    left, right = st.columns(2)
    left.markdown(f"**FRED series:** `{source_row['series_id']}`")
    left.markdown(f"**Source unit:** {source_row['unit']}")
    right.markdown(f"**Frequency:** {source_row['frequency']}")
    right.markdown(f"**Latest observation:** {source_row['date']:%Y-%m-%d}")

with data_tab:
    st.subheader("Most recent source observations")
    table = (
        data.sort_values("date")
        .groupby("component", as_index=False)
        .tail(10)[["date", "label", "series_id", "value", "unit", "frequency"]]
        .sort_values(["label", "date"], ascending=[True, False])
    )
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption(f"Displayed file: `{data_path.relative_to(PROJECT_ROOT)}`")

with methodology_tab:
    st.subheader("What this version shows")
    st.markdown(
        """
        This dashboard displays four **measured public series**:

        - **WALCL:** Federal Reserve total assets, Wednesday level.
        - **WDTGAL:** Treasury General Account, Wednesday level.
        - **RRPONTSYD:** overnight reverse-repurchase operations, daily.
        - **WRBWFRBL:** reserve balances with Federal Reserve Banks, Wednesday level.

        Source observations in millions are divided by 1,000 for a common **USD billions** display
        unit. RRP is already reported in billions. This unit conversion is not an economic model.

        The charts use current-vintage FRED data and do not account for publication lags or preserve
        historical vintages. Daily RRP has not yet been resampled to a weekly research frequency.
        No values are interpolated. Hosted deployments use a versioned public-data snapshot when
        locally processed data is unavailable; the sidebar identifies the active data mode.
        """
    )
    st.warning(
        "No liquidity formula, momentum score, regime, or OGLI normalization is implemented yet. "
        "Any such additions will be explicitly labeled as project assumptions."
    )
    st.markdown(
        "[WALCL](https://fred.stlouisfed.org/series/WALCL) · "
        "[WDTGAL](https://fred.stlouisfed.org/series/WDTGAL) · "
        "[RRPONTSYD](https://fred.stlouisfed.org/series/RRPONTSYD) · "
        "[WRBWFRBL](https://fred.stlouisfed.org/series/WRBWFRBL)"
    )
