"""Streamlit presentation layer for Open Global Liquidity research."""

from __future__ import annotations

import os
from datetime import timedelta
from importlib import reload
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import dashboard_support as dashboard_support_module  # noqa: E402

reload(dashboard_support_module)
from dashboard_support import (  # noqa: E402
    COMPONENT_LABELS,
    DashboardDataError,
    assess_freshness,
    latest_model_readings,
    latest_ogli_readings,
    latest_readings,
    load_dashboard_data,
    load_liquidity_model_data,
    load_macro_context,
    load_market_comparisons,
    load_market_correlations,
    load_market_regime_statistics,
    load_ogli_data,
    resolve_dashboard_data_path,
)

DATA_ROOT = Path(os.environ.get("OGLI_DATA_ROOT", PROJECT_ROOT / "data"))
PROCESSED_DATA_PATH = DATA_ROOT / "processed" / "us_fred_series.parquet"
SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_fred_series_snapshot.parquet"
MODEL_DATA_PATH = DATA_ROOT / "processed" / "us_liquidity_models.parquet"
MODEL_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_liquidity_models_snapshot.parquet"
OGLI_DATA_PATH = DATA_ROOT / "processed" / "us_ogli.parquet"
OGLI_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_ogli_snapshot.parquet"
MARKET_COMPARISONS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_comparisons.parquet"
MARKET_COMPARISONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_comparisons_snapshot.parquet"
)
MARKET_CORRELATIONS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_correlations.parquet"
MARKET_CORRELATIONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_correlations_snapshot.parquet"
)
MARKET_REGIMES_PATH = DATA_ROOT / "processed" / "us_liquidity_market_regimes.parquet"
MARKET_REGIMES_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_regimes_snapshot.parquet"
)
MACRO_CONTEXT_PATH = DATA_ROOT / "processed" / "us_macro_context_indicators.parquet"
MACRO_CONTEXT_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_macro_context_indicators_snapshot.parquet"
)
COMPONENT_ORDER = list(COMPONENT_LABELS)
WINDOW_DAYS = {"1 year": 365, "3 years": 3 * 365, "5 years": 5 * 365}
COLORS = {
    "Fed total assets": "#2563EB",
    "Treasury General Account": "#D97706",
    "ON reverse repo": "#7C3AED",
    "Reserve balances": "#059669",
}
MODEL_COLORS = {
    "Model A — Fed assets": "#2563EB",
    "Model B — Net Fed liquidity proxy": "#D97706",
    "Model C — Reserve-based liquidity": "#059669",
}

st.set_page_config(
    page_title="Open Global Liquidity",
    page_icon=":material/water_drop:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def _load_data(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache processed data until its file modification timestamp changes."""
    del modified_ns
    return load_dashboard_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_models(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache model data until its file modification timestamp changes."""
    del modified_ns
    return load_liquidity_model_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_ogli(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache calculated OGLI data until its file timestamp changes."""
    del modified_ns
    return load_ogli_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_comparisons(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated market comparison pairs."""
    del modified_ns
    return load_market_comparisons(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_correlations(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated market correlation summaries."""
    del modified_ns
    return load_market_correlations(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_regimes(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated regime outcome summaries."""
    del modified_ns
    return load_market_regime_statistics(Path(path))


@st.cache_data(show_spinner=False)
def _load_macro_context(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated measured macro context."""
    del modified_ns
    return load_macro_context(Path(path))


def _source_data() -> tuple[pd.DataFrame, Path, str]:
    data_path, data_origin = resolve_dashboard_data_path(PROCESSED_DATA_PATH, SNAPSHOT_DATA_PATH)
    return _load_data(str(data_path), data_path.stat().st_mtime_ns), data_path, data_origin


def _model_data() -> tuple[pd.DataFrame, str] | None:
    try:
        model_path, model_origin = resolve_dashboard_data_path(
            MODEL_DATA_PATH, MODEL_SNAPSHOT_DATA_PATH
        )
    except DashboardDataError:
        return None
    models = _load_models(str(model_path), model_path.stat().st_mtime_ns)
    return models, model_origin


def _ogli_data() -> tuple[pd.DataFrame, str]:
    ogli_path, ogli_origin = resolve_dashboard_data_path(OGLI_DATA_PATH, OGLI_SNAPSHOT_DATA_PATH)
    return _load_ogli(str(ogli_path), ogli_path.stat().st_mtime_ns), ogli_origin


def _market_data() -> tuple[pd.DataFrame | None, pd.DataFrame, str]:
    correlation_path, correlation_origin = resolve_dashboard_data_path(
        MARKET_CORRELATIONS_PATH, MARKET_CORRELATIONS_SNAPSHOT_PATH
    )
    correlations = _load_market_correlations(
        str(correlation_path), correlation_path.stat().st_mtime_ns
    )
    try:
        comparison_path, comparison_origin = resolve_dashboard_data_path(
            MARKET_COMPARISONS_PATH, MARKET_COMPARISONS_SNAPSHOT_PATH
        )
    except DashboardDataError:
        return None, correlations, correlation_origin
    comparisons = _load_market_comparisons(str(comparison_path), comparison_path.stat().st_mtime_ns)
    return comparisons, correlations, comparison_origin


def _market_regime_data() -> pd.DataFrame | None:
    try:
        path, _origin = resolve_dashboard_data_path(
            MARKET_REGIMES_PATH, MARKET_REGIMES_SNAPSHOT_PATH
        )
    except DashboardDataError:
        return None
    return _load_market_regimes(str(path), path.stat().st_mtime_ns)


def _macro_context_data() -> pd.DataFrame | None:
    try:
        path, _origin = resolve_dashboard_data_path(MACRO_CONTEXT_PATH, MACRO_CONTEXT_SNAPSHOT_PATH)
    except DashboardDataError:
        return None
    return _load_macro_context(str(path), path.stat().st_mtime_ns)


def _show_freshness(frame: pd.DataFrame, label: str, *, max_age_days: int = 14) -> None:
    status = assess_freshness(frame, max_age_days=max_age_days)
    message = (
        f"{label} latest observation: {status.latest_date:%Y-%m-%d} ({status.age_days} days old)."
    )
    if status.is_stale:
        st.warning(
            message
            + f" Expected maximum age is {status.max_age_days} days; check the refresh workflow.",
            icon=":material/update_disabled:",
        )
    else:
        st.caption(message)


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


def _model_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="value_usd_billions",
        color="model_name",
        color_discrete_map=MODEL_COLORS,
        labels={"date": "", "value_usd_billions": "USD billions", "model_name": "Model"},
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


def _ogli_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="ogli",
        labels={"date": "", "ogli": "OGLI (0-100)"},
        title=title,
    )
    figure.update_traces(line={"width": 2.5, "color": "#2563EB"})
    for threshold in [10, 30, 45, 55, 70, 90]:
        figure.add_hline(
            y=threshold,
            line_width=1,
            line_dash="dot",
            line_color="rgba(128,128,128,0.3)",
        )
    figure.update_layout(
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [0, 100], "gridcolor": "rgba(128,128,128,0.12)"},
        showlegend=False,
    )
    return figure


def _market_scatter_figure(frame: pd.DataFrame, title: str):
    figure = px.scatter(
        frame,
        x="liquidity_signal",
        y="market_return",
        hover_data={"date": "|%Y-%m-%d", "ogli": ":.1f"},
        labels={
            "liquidity_signal": "OGLI momentum score",
            "market_return": "Bitcoin return",
        },
        title=title,
    )
    figure.update_traces(marker={"size": 7, "opacity": 0.65, "color": "#2563EB"})
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"zeroline": True, "gridcolor": "rgba(128,128,128,0.15)"},
        yaxis={
            "zeroline": True,
            "gridcolor": "rgba(128,128,128,0.15)",
            "tickformat": ".0%",
        },
    )
    return figure


def _ogli_bitcoin_overlay_figure(frame: pd.DataFrame, title: str):
    """Plot package-calculated OGLI beside Bitcoin prices without altering either series."""
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["value"],
            name="Bitcoin price",
            line={"color": "#D97706", "width": 2.25},
            hovertemplate="$%{y:,.0f}<extra>Bitcoin</extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["ogli"],
            name="OGLI",
            line={"color": "#2563EB", "width": 2.25},
            hovertemplate="%{y:.1f}<extra>OGLI</extra>",
        ),
        secondary_y=True,
    )
    figure.update_layout(
        title=title,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        margin={"l": 10, "r": 10, "t": 75, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    figure.update_yaxes(
        title_text="Bitcoin price (USD, log scale)",
        type="log",
        tickprefix="$",
        gridcolor="rgba(128,128,128,0.15)",
        secondary_y=False,
    )
    figure.update_yaxes(
        title_text="OGLI (0-100)",
        range=[0, 100],
        gridcolor="rgba(128,128,128,0.10)",
        secondary_y=True,
    )
    return figure


def _rolling_correlation_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="rolling_correlation",
        labels={"date": "", "rolling_correlation": "Trailing correlation"},
        title=title,
    )
    figure.update_traces(line={"width": 2.25, "color": "#7C3AED"})
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [-1, 1], "gridcolor": "rgba(128,128,128,0.15)"},
        showlegend=False,
    )
    return figure


def _horizon_correlation_figure(frame: pd.DataFrame, title: str):
    chart = frame.copy()
    chart["horizon_label"] = chart["horizon_weeks"].map(
        lambda value: "0 (1w current)" if value == 0 else f"{value}w forward"
    )
    figure = px.bar(
        chart,
        x="horizon_label",
        y="correlation",
        text_auto=".2f",
        labels={"horizon_label": "Return horizon", "correlation": "Pearson correlation"},
        title=title,
    )
    figure.update_traces(marker_color="#D97706")
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [-1, 1], "gridcolor": "rgba(128,128,128,0.15)"},
    )
    return figure


def _regime_return_figure(frame: pd.DataFrame, title: str):
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["regime"],
            y=frame["median_return"],
            name="Median return",
            marker_color="#2563EB",
            hovertemplate="%{x}<br>Median: %{y:.1%}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["regime"],
            y=frame["mean_return"],
            mode="markers",
            name="Mean return",
            marker={"color": "#D97706", "size": 10},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": frame["mean_ci_upper"] - frame["mean_return"],
                "arrayminus": frame["mean_return"] - frame["mean_ci_lower"],
            },
            hovertemplate="%{x}<br>Mean: %{y:.1%}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        title=title,
        barmode="group",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"tickformat": ".0%", "title": "Bitcoin return"},
        xaxis={"title": "OGLI regime at signal observation"},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def _macro_context_figure(frame: pd.DataFrame, title: str):
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["treasury_yield_10y"],
            name="10-year yield",
            line={"color": "#2563EB", "width": 2},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["treasury_yield_2y"],
            name="2-year yield",
            line={"color": "#7C3AED", "width": 2},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["broad_usd_index"],
            name="Broad USD index",
            line={"color": "#D97706", "width": 2},
        ),
        secondary_y=True,
    )
    figure.update_yaxes(title_text="Treasury yield (%)", secondary_y=False)
    figure.update_yaxes(title_text="Broad USD index (Jan 2006=100)", secondary_y=True)
    figure.update_layout(
        title=title,
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def _load_or_explain() -> tuple[pd.DataFrame, Path, str] | None:
    try:
        return _source_data()
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        return None


def landing_page() -> None:
    st.badge("Independent public-data research · v0.1", icon=":material/science:")
    st.title("See the financial system through a liquidity lens")
    st.markdown(
        """
        **Global liquidity is the ease with which financing can be created, obtained, and moved
        through the financial system.** It reflects more than central-bank money: bank balance
        sheets, credit creation, collateral, funding markets, and cross-border finance all matter.

        Open Global Liquidity turns public data into transparent, reproducible indicators. The
        current release is deliberately narrow—**United States only**—so the engineering and
        research assumptions can be tested before building a global aggregate.
        """
    )

    loaded = _load_or_explain()
    if loaded is not None:
        data, _data_path, data_origin = loaded
        latest = latest_readings(data).set_index("component")
        try:
            model_bundle = _model_data()
        except DashboardDataError:
            model_bundle = None
        models = model_bundle[0] if model_bundle is not None else None
        latest_models = (
            latest_model_readings(models).set_index("model_id") if models is not None else None
        )

        st.subheader("Latest US liquidity snapshot")
        with st.container(horizontal=True):
            if latest_models is not None and "model_b" in latest_models.index:
                row = latest_models.loc["model_b"]
                delta = row["change_usd_billions"]
                st.metric(
                    "Net Fed liquidity proxy",
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(delta) else f"{delta:+,.1f}bn weekly",
                    border=True,
                    chart_data=models.loc[models["model_id"] == "model_b", "value_usd_billions"]
                    .tail(26)
                    .tolist(),
                )
            for component in ["fed_assets", "reserve_balances", "treasury_general_account"]:
                if component not in latest.index:
                    continue
                row = latest.loc[component]
                delta = row["change_usd_billions"]
                st.metric(
                    str(row["label"]),
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(delta) else f"{delta:+,.1f}bn prior observation",
                    border=True,
                    chart_data=data.loc[data["component"] == component, "value_usd_billions"].tail(
                        26
                    ),
                )
        latest_date = data["date"].max()
        st.caption(
            f"Latest source date {latest_date:%Y-%m-%d} · {data_origin} · Nominal USD balances"
        )
        _show_freshness(data, "US liquidity data")

        try:
            comparisons, correlations, market_origin = _market_data()
            ogli_data, _ogli_origin = _ogli_data()
        except DashboardDataError:
            comparisons = None
            correlations = pd.DataFrame()
            ogli_data = pd.DataFrame()
            market_origin = "Unavailable"

        if comparisons is not None:
            current_btc = comparisons.loc[
                (comparisons["model_id"] == "model_b")
                & (comparisons["market_id"] == "bitcoin")
                & (comparisons["horizon_weeks"] == 0)
            ].dropna(subset=["market_return"])
            latest_ogli = ogli_data.loc[
                (ogli_data["model_id"] == "model_b") & ogli_data["ogli"].notna()
            ]
            relationship = correlations.loc[
                (correlations["model_id"] == "model_b")
                & (correlations["market_id"] == "bitcoin")
                & (correlations["horizon_weeks"] == 12)
                & (correlations["analysis_mode"] == "available_information")
                & (correlations["sample_policy"] == "non_overlapping")
            ]
            if relationship.empty:
                relationship = correlations.loc[
                    (correlations["model_id"] == "model_b")
                    & (correlations["market_id"] == "bitcoin")
                    & (correlations["horizon_weeks"] == 12)
                ]
            if not current_btc.empty and not latest_ogli.empty and not relationship.empty:
                btc_row = current_btc.iloc[-1]
                ogli_row = latest_ogli.iloc[-1]
                relationship_row = relationship.iloc[0]
                st.subheader("Bitcoin and liquidity momentum")
                with st.container(horizontal=True):
                    bitcoin_price = btc_row.get("value")
                    if pd.notna(bitcoin_price):
                        st.metric(
                            "Bitcoin price",
                            f"${float(bitcoin_price):,.0f}",
                            f"{btc_row['market_return']:+.1%} weekly",
                            border=True,
                        )
                    st.metric(
                        "OGLI · Model B",
                        f"{ogli_row['ogli']:.1f}",
                        str(ogli_row["regime"]),
                        border=True,
                    )
                    correlation = relationship_row["correlation"]
                    st.metric(
                        "BTC correlation · 12w forward",
                        "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
                        f"{int(relationship_row['observations']):,} paired observations",
                        border=True,
                    )
                st.caption(
                    f"Bitcoin data through {btc_row['date']:%Y-%m-%d} · {market_origin} · "
                    "Correlation is descriptive, not a forecast."
                )

    st.subheader("A practical way to think about global liquidity")
    concept_columns = st.columns(3)
    with concept_columns[0].container(border=True, height="stretch"):
        st.markdown("#### :material/account_balance: Monetary base")
        st.write(
            "Central-bank assets and reserve balances establish the official-money foundation "
            "on which financial institutions settle and expand balance sheets."
        )
    with concept_columns[1].container(border=True, height="stretch"):
        st.markdown("#### :material/credit_score: Credit capacity")
        st.write(
            "Banks and market-based lenders multiply financing through loans, securities, repo, "
            "and other forms of leverage."
        )
    with concept_columns[2].container(border=True, height="stretch"):
        st.markdown("#### :material/hub: Market transmission")
        st.write(
            "Collateral quality, volatility, funding costs, and cross-border channels influence "
            "how easily liquidity reaches markets and borrowers."
        )

    st.subheader("Why use a liquidity framework?")
    benefit_columns = st.columns(3)
    with benefit_columns[0]:
        st.markdown("**Track the direction of financing conditions**")
        st.caption(
            "Levels and momentum can provide context for whether balance-sheet capacity is "
            "expanding or contracting."
        )
    with benefit_columns[1]:
        st.markdown("**Compare competing definitions**")
        st.caption(
            "No single series captures liquidity. Showing alternatives makes model uncertainty "
            "visible instead of hiding it."
        )
    with benefit_columns[2]:
        st.markdown("**Audit every transformation**")
        st.caption(
            "Series IDs, units, alignment rules, source dates, and model weights remain explicit "
            "and reproducible."
        )

    st.warning(
        "Liquidity is not directly observable, and correlation with asset prices does not imply "
        "causation. This project is a research tool—not a market-timing signal or investment "
        "advice.",
        icon=":material/warning:",
    )
    with st.container(horizontal=True):
        st.page_link(data_page, label="Explore the data", icon=":material/monitoring:")
        st.page_link(guide_page, label="Read the research guide", icon=":material/menu_book:")


def data_dashboard_page() -> None:
    st.title("US liquidity dashboard")
    st.caption(
        "Measured balance-sheet data and three transparent model assumptions. This is not OGLI "
        "and does not reproduce CrossBorder Capital's proprietary GLI."
    )
    loaded = _load_or_explain()
    if loaded is None:
        return
    data, data_path, data_origin = loaded
    _show_freshness(data, "US liquidity data")
    try:
        model_bundle = _model_data()
        model_error = None
    except DashboardDataError as exc:
        model_bundle = None
        model_error = str(exc)
    if model_bundle is None:
        models = None
        model_origin = None
    else:
        models, model_origin = model_bundle

    latest = latest_readings(data).set_index("component")
    last_retrieved = pd.to_datetime(data["retrieved_at"].max(), utc=True)
    with st.sidebar:
        st.header("View controls")
        window = st.segmented_control(
            "History", ["1 year", "3 years", "5 years", "All"], default="5 years"
        )
        selected_label = st.selectbox(
            "Component explorer",
            [COMPONENT_LABELS[item] for item in COMPONENT_ORDER if item in set(data["component"])],
        )
        st.caption(f"Data mode: {data_origin}")
        st.caption(f"Retrieved {last_retrieved:%Y-%m-%d %H:%M UTC}")
        st.caption("Source: FRED and the named originating Federal Reserve releases.")

    max_date = data["date"].max()
    if window == "All":
        visible = data
    else:
        visible = data.loc[data["date"] >= max_date - timedelta(days=WINDOW_DAYS[str(window)])]

    overview_tab, models_tab, explorer_tab, data_tab = st.tabs(
        ["Measured data", "Liquidity models", "Component explorer", "Latest observations"]
    )
    with overview_tab:
        st.subheader("Latest measured balances")
        with st.container(horizontal=True):
            for component in COMPONENT_ORDER:
                if component not in latest.index:
                    st.metric(COMPONENT_LABELS[component], "Unavailable", border=True)
                    continue
                row = latest.loc[component]
                change = row["change_usd_billions"]
                st.metric(
                    str(row["label"]),
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(change) else f"{change:+,.1f}bn vs prior observation",
                    border=True,
                )
        st.plotly_chart(
            _history_figure(visible, f"US liquidity-related balance-sheet series · {window}"),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "These charts show measured source series. USD-billions conversion is a display "
            "transformation, not an economic weighting."
        )

    with models_tab:
        st.subheader("Three competing US liquidity definitions")
        if model_error:
            st.error(model_error)
        elif models is None:
            st.info("Run the local pipeline to generate the liquidity-model dataset.")
            st.code(
                "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
                language="zsh",
            )
        else:
            latest_models = latest_model_readings(models).set_index("model_id")
            with st.container(horizontal=True):
                for model_id in ["model_a", "model_b", "model_c"]:
                    if model_id not in latest_models.index:
                        continue
                    row = latest_models.loc[model_id]
                    change = row["change_usd_billions"]
                    st.metric(
                        str(row["model_name"]),
                        _format_billions(float(row["value_usd_billions"])),
                        None if pd.isna(change) else f"{change:+,.1f}bn vs prior week",
                        border=True,
                    )
            model_max_date = models["date"].max()
            if window == "All":
                visible_models = models
            else:
                visible_models = models.loc[
                    models["date"] >= model_max_date - timedelta(days=WINDOW_DAYS[str(window)])
                ]
            st.plotly_chart(
                _model_figure(visible_models, f"US liquidity model levels · {window}"),
                width="stretch",
                config={"displaylogo": False},
            )
            st.warning(
                "These are configurable Open Global Liquidity assumptions. Model B is a common "
                "public-market proxy; none is CrossBorder Capital's proprietary formula."
            )
            st.caption(f"Model data mode: {model_origin}")

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
        source_columns = st.columns(2)
        source_columns[0].markdown(f"**FRED series:** `{source_row['series_id']}`")
        source_columns[0].markdown(f"**Source unit:** {source_row['unit']}")
        source_columns[1].markdown(f"**Frequency:** {source_row['frequency']}")
        source_columns[1].markdown(f"**Latest observation:** {source_row['date']:%Y-%m-%d}")

    with data_tab:
        st.subheader("Most recent source observations")
        table = (
            data.sort_values("date")
            .groupby("component", as_index=False)
            .tail(10)[["date", "label", "series_id", "value", "unit", "frequency"]]
            .sort_values(["label", "date"], ascending=[True, False])
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={"date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")},
        )
        try:
            displayed_path = data_path.relative_to(PROJECT_ROOT)
        except ValueError:
            displayed_path = data_path
        st.caption(f"Displayed file: `{displayed_path}`")


def ogli_page() -> None:
    st.title("OGLI momentum index")
    st.caption(
        "Experimental 0-100 normalization of US liquidity momentum. Independent Open Global "
        "Liquidity methodology—not CrossBorder Capital's proprietary GLI."
    )
    try:
        data, data_origin = _ogli_data()
        latest_by_model = latest_ogli_readings(data)
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        return

    model_options = dict(
        latest_by_model[["model_name", "model_id"]].itertuples(index=False, name=None)
    )
    with st.sidebar:
        st.header("OGLI controls")
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index("Model B — Net Fed liquidity proxy"),
        )
        history = st.segmented_control(
            "History", ["1 year", "3 years", "All"], default="3 years", key="ogli_history"
        )
        st.caption(f"Data mode: {data_origin}")

    model_id = model_options[selected_name]
    model_data = data.loc[(data["model_id"] == model_id) & data["ogli"].notna()].copy()
    latest = model_data.iloc[-1]
    if history == "All":
        visible = model_data
    else:
        visible = model_data.loc[
            model_data["date"]
            >= model_data["date"].max() - timedelta(days=WINDOW_DAYS[str(history)])
        ]

    with st.container(horizontal=True):
        st.metric(
            "Latest OGLI",
            f"{latest['ogli']:.1f}",
            border=True,
            chart_data=model_data["ogli"].tail(26).tolist(),
        )
        st.metric("Liquidity regime", str(latest["regime"]), border=True)
        st.metric(
            "Momentum score", f"{latest['momentum_score']:+.2f} standard deviations", border=True
        )
        st.metric(
            "3m annualized growth",
            f"{latest['growth_3m_annualized']:.1%}",
            border=True,
        )
        st.metric("12m YoY growth", f"{latest['growth_12m_yoy']:.1%}", border=True)

    st.plotly_chart(
        _ogli_figure(visible, f"{selected_name} · OGLI history"),
        width="stretch",
        config={"displaylogo": False},
    )
    st.caption(
        f"Latest reading {latest['date']:%Y-%m-%d} · "
        f"{latest['zscore_mode']} z-score · minimum {latest['zscore_min_periods']} observations"
    )

    with st.container(border=True):
        st.subheader("How to read OGLI")
        st.markdown(
            """
            OGLI measures how unusual current liquidity momentum is relative to historical
            observations. It uses z-score normalization and the standard normal cumulative
            distribution function. It is not normalized against the historical maximum, so new
            liquidity highs do not mechanically rescale the entire historical index.

            **Around 50 is statistically neutral.** Higher readings indicate momentum above its
            historical norm; lower readings indicate momentum below its historical norm. This is
            a relative momentum measure, not the dollar level of liquidity and not a forecast.
            """
        )

    with st.expander("Formula, weights, and regimes"):
        st.code(
            "Momentum = 0.60 * z(3m annualized growth) + 0.40 * z(12m YoY growth)\n"
            "OGLI = 100 * Phi(Momentum)",
            language=None,
        )
        st.write(
            "The 60/40 weights and regime thresholds are configurable Open Global Liquidity "
            "research assumptions. They are not calibrated parameters and are not Howell or "
            "CrossBorder Capital parameters."
        )
        st.dataframe(
            pd.DataFrame(
                {
                    "OGLI range": [
                        "0-10",
                        ">10-30",
                        ">30-45",
                        ">45-55",
                        ">55-70",
                        ">70-90",
                        ">90-100",
                    ],
                    "Regime": [
                        "Strong contraction",
                        "Contraction",
                        "Below normal",
                        "Neutral",
                        "Above normal",
                        "Expansion",
                        "Strong expansion",
                    ],
                }
            ),
            hide_index=True,
        )


def markets_page() -> None:
    st.title("Liquidity vs markets")
    st.caption(
        "Retrospective comparison of OGLI momentum with Bitcoin returns. Correlation is not "
        "causation, a forecast, or parameter calibration."
    )
    try:
        comparisons, correlations, data_origin = _market_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/info:")
        st.markdown(
            "Bitcoin comparison files are unavailable. Run the pipeline to refresh the public "
            "Coin Metrics market snapshot:"
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        st.link_button(
            "Review Coin Metrics community data",
            "https://github.com/coinmetrics/data",
            icon=":material/open_in_new:",
        )
        return
    if comparisons is not None:
        _show_freshness(comparisons, "Bitcoin/OGLI comparison")

    model_options = dict(
        correlations[["model_name", "model_id"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    horizon_options = {
        "Current 1-week return": 0,
        "4 weeks forward": 4,
        "8 weeks forward": 8,
        "12 weeks forward": 12,
        "26 weeks forward": 26,
        "52 weeks forward": 52,
    }
    analysis_labels = {
        "Available-information (1-week release lag)": "available_information",
        "Observation-date exploratory": "observation_date",
    }
    available_analysis_modes = set(correlations["analysis_mode"])
    analysis_options = {
        label: value
        for label, value in analysis_labels.items()
        if value in available_analysis_modes
    }
    sample_labels = {
        "Non-overlapping windows": "non_overlapping",
        "All overlapping observations": "overlapping",
    }
    available_sample_policies = set(correlations["sample_policy"])
    sample_options = {
        label: value for label, value in sample_labels.items() if value in available_sample_policies
    }
    with st.sidebar:
        st.header("Market controls")
        selected_model = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index("Model B — Net Fed liquidity proxy"),
            key="market_model",
        )
        selected_horizon_label = st.selectbox(
            "Return horizon",
            list(horizon_options),
            index=3,
            key="market_horizon",
        )
        selected_analysis_label = st.selectbox(
            "Signal timing",
            list(analysis_options),
            key="market_analysis_mode",
        )
        selected_sample_label = st.selectbox(
            "Statistical sample",
            list(sample_options),
            key="market_sample_policy",
        )
        timeline_history = st.segmented_control(
            "Timeline history",
            ["3 years", "5 years", "All"],
            default="5 years",
            key="market_timeline_history",
        )
        st.caption("Market: Bitcoin · Coin Metrics daily USD price")
        st.caption(f"Data mode: {data_origin}")

    model_id = model_options[selected_model]
    horizon = horizon_options[selected_horizon_label]
    analysis_mode = analysis_options[selected_analysis_label]
    sample_policy = sample_options[selected_sample_label]
    selected_summary = correlations.loc[
        (correlations["model_id"] == model_id)
        & (correlations["market_id"] == "bitcoin")
        & (correlations["horizon_weeks"] == horizon)
        & (correlations["analysis_mode"] == analysis_mode)
        & (correlations["sample_policy"] == sample_policy)
    ].iloc[0]
    model_correlations = correlations.loc[
        (correlations["model_id"] == model_id)
        & (correlations["market_id"] == "bitcoin")
        & (correlations["analysis_mode"] == analysis_mode)
        & (correlations["sample_policy"] == sample_policy)
    ]
    correlation = selected_summary["correlation"]

    if comparisons is None:
        with st.container(horizontal=True):
            st.metric(
                "Pearson correlation",
                "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
                border=True,
            )
            st.metric(
                "Paired observations", f"{int(selected_summary['observations']):,}", border=True
            )
            st.metric("Selected horizon", selected_horizon_label, border=True)

        st.plotly_chart(
            _horizon_correlation_figure(
                model_correlations,
                f"{selected_model} · correlation by return horizon",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.dataframe(
            model_correlations[["horizon_weeks", "correlation", "observations"]],
            width="stretch",
            hide_index=True,
            column_config={
                "horizon_weeks": st.column_config.NumberColumn("Forward horizon (weeks)"),
                "correlation": st.column_config.NumberColumn("Pearson correlation", format="%+.2f"),
                "observations": st.column_config.NumberColumn("Paired observations", format="%d"),
            },
        )
        st.info(
            "Only aggregate statistics are available in this data snapshot. Refresh the dashboard "
            "snapshots to publish the complete non-commercial Bitcoin research view.",
            icon=":material/info:",
        )
        st.warning(
            "These exploratory correlations do not establish causation or an investable signal. "
            "Refresh the full snapshots to compare observation-date and available-information "
            "timing policies.",
            icon=":material/warning:",
        )
        return

    selected_pairs = comparisons.loc[
        (comparisons["model_id"] == model_id)
        & (comparisons["market_id"] == "bitcoin")
        & (comparisons["horizon_weeks"] == horizon)
        & (comparisons["analysis_mode"] == analysis_mode)
    ].dropna(subset=["liquidity_signal", "market_return"])
    if sample_policy == "non_overlapping":
        selected_pairs = selected_pairs.loc[selected_pairs["is_non_overlapping"]]
    if selected_pairs.empty:
        st.info(
            "No completed Bitcoin outcome windows are available for this combination yet.",
            icon=":material/hourglass_empty:",
        )
        return
    latest_pair = selected_pairs.iloc[-1]
    bitcoin_price = latest_pair.get("value")

    with st.container(horizontal=True):
        st.metric(
            "Pearson correlation",
            "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
            border=True,
        )
        st.metric("Paired observations", f"{int(selected_summary['observations']):,}", border=True)
        st.metric("Latest paired OGLI", f"{latest_pair['ogli']:.1f}", border=True)
        if pd.notna(bitcoin_price):
            st.metric("BTC at signal date", f"${float(bitcoin_price):,.0f}", border=True)
        st.metric("Latest paired BTC return", f"{latest_pair['market_return']:.1%}", border=True)

    timeline_tab, scatter_tab, regimes_tab, rolling_tab, horizons_tab, macro_tab, data_tab = (
        st.tabs(
            [
                "Timeline",
                "Relationship",
                "Returns by regime",
                "Rolling correlation",
                "Across horizons",
                "Macro context",
                "Paired data",
            ]
        )
    )
    with timeline_tab:
        if "value" not in comparisons.columns:
            st.info(
                "Bitcoin price history will appear after the hosted data process finishes "
                "reloading the latest snapshot.",
                icon=":material/sync:",
            )
        else:
            timeline = comparisons.loc[
                (comparisons["model_id"] == model_id)
                & (comparisons["market_id"] == "bitcoin")
                & (comparisons["horizon_weeks"] == 0)
                & (comparisons["analysis_mode"] == analysis_mode)
            ].dropna(subset=["ogli", "value"])
            if timeline_history != "All":
                years = 3 if timeline_history == "3 years" else 5
                timeline = timeline.loc[
                    timeline["date"] >= timeline["date"].max() - timedelta(days=years * 365)
                ]
            st.plotly_chart(
                _ogli_bitcoin_overlay_figure(
                    timeline,
                    f"{selected_model} and Bitcoin · {timeline_history}",
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.caption(
                "Bitcoin uses a logarithmic USD axis; OGLI uses its 0-100 scale. The lines share "
                "dates only—neither series is rescaled or fitted to the other."
            )
    with scatter_tab:
        st.plotly_chart(
            _market_scatter_figure(
                selected_pairs,
                f"{selected_model} vs Bitcoin · {selected_horizon_label}",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "Each point anchors the expanding OGLI momentum score at t to the named market-return "
            "window. Forward outcomes are never inputs to OGLI."
        )
    with regimes_tab:
        regime_statistics = _market_regime_data()
        if regime_statistics is None:
            st.info(
                "Regime statistics will appear after the refreshed research snapshots are built.",
                icon=":material/sync:",
            )
        else:
            selected_regimes = regime_statistics.loc[
                (regime_statistics["model_id"] == model_id)
                & (regime_statistics["market_id"] == "bitcoin")
                & (regime_statistics["horizon_weeks"] == horizon)
                & (regime_statistics["analysis_mode"] == analysis_mode)
                & (regime_statistics["sample_policy"] == sample_policy)
            ]
            st.plotly_chart(
                _regime_return_figure(
                    selected_regimes,
                    f"Bitcoin outcomes by OGLI regime · {selected_horizon_label}",
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.dataframe(
                selected_regimes[
                    [
                        "regime",
                        "observations",
                        "mean_return",
                        "median_return",
                        "positive_share",
                        "mean_ci_lower",
                        "mean_ci_upper",
                    ]
                ],
                hide_index=True,
                column_config={
                    "regime": "OGLI regime",
                    "observations": st.column_config.NumberColumn("Observations", format="%d"),
                    "mean_return": st.column_config.NumberColumn("Mean", format="percent"),
                    "median_return": st.column_config.NumberColumn("Median", format="percent"),
                    "positive_share": st.column_config.NumberColumn(
                        "Positive share", format="percent"
                    ),
                    "mean_ci_lower": st.column_config.NumberColumn(
                        "Mean CI lower", format="percent"
                    ),
                    "mean_ci_upper": st.column_config.NumberColumn(
                        "Mean CI upper", format="percent"
                    ),
                },
            )
            st.caption(
                "Error bars are classical 95% Student-t confidence intervals around the mean, "
                "not forecast intervals. Median and positive-share statistics are shown because "
                "Bitcoin returns are strongly skewed."
            )
    with rolling_tab:
        rolling = selected_pairs.dropna(subset=["rolling_correlation"])
        st.plotly_chart(
            _rolling_correlation_figure(
                rolling,
                f"52-week trailing correlation · {selected_horizon_label}",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption("The rolling estimate requires at least 26 paired weekly observations.")
    with horizons_tab:
        st.plotly_chart(
            _horizon_correlation_figure(
                model_correlations,
                f"{selected_model} · correlation by return horizon",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "All estimates use the same configured OGLI momentum signal. Horizon zero is the "
            "one-week return ending at t; positive horizons start at t."
        )
    with macro_tab:
        macro_context = _macro_context_data()
        if macro_context is None:
            st.info(
                "Treasury-yield and dollar context will appear after the next full pipeline run.",
                icon=":material/sync:",
            )
        else:
            visible_macro = macro_context.loc[
                macro_context["date"] >= macro_context["date"].max() - timedelta(days=5 * 365)
            ]
            latest_macro = macro_context.dropna().iloc[-1]
            with st.container(horizontal=True):
                st.metric(
                    "10-year Treasury", f"{latest_macro['treasury_yield_10y']:.2f}%", border=True
                )
                st.metric(
                    "2-year Treasury", f"{latest_macro['treasury_yield_2y']:.2f}%", border=True
                )
                st.metric(
                    "10y-2y slope", f"{latest_macro['yield_curve_10y_2y']:+.2f}pp", border=True
                )
                st.metric("Broad USD index", f"{latest_macro['broad_usd_index']:.1f}", border=True)
            st.plotly_chart(
                _macro_context_figure(
                    visible_macro, "Treasury yields and broad U.S. dollar · 5 years"
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.caption(
                "DGS10, DGS2, and DTWEXBGS are measured context series. The 10y-2y slope is a "
                "transparent subtraction. None is currently an OGLI input."
            )
    with data_tab:
        table = selected_pairs[
            [
                "date",
                "signal_observation_date",
                "signal_available_date",
                "ogli",
                "liquidity_signal",
                "market_return",
                "return_start_date",
                "return_end_date",
            ]
        ].sort_values("date", ascending=False)
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Signal date", format="YYYY-MM-DD"),
                "signal_observation_date": st.column_config.DateColumn(
                    "Source observation", format="YYYY-MM-DD"
                ),
                "signal_available_date": st.column_config.DateColumn(
                    "Assumed available", format="YYYY-MM-DD"
                ),
                "ogli": st.column_config.NumberColumn("OGLI", format="%.1f"),
                "liquidity_signal": st.column_config.NumberColumn("Momentum score", format="%+.2f"),
                "market_return": st.column_config.NumberColumn("Bitcoin return", format="percent"),
                "return_start_date": st.column_config.DateColumn(
                    "Return start", format="YYYY-MM-DD"
                ),
                "return_end_date": st.column_config.DateColumn("Return end", format="YYYY-MM-DD"),
            },
        )

    st.warning(
        "These statistics are sensitive to sample selection, overlapping forward-return windows, "
        "data revisions, publication-lag assumptions, and common macroeconomic drivers. The "
        "available-information view applies a configurable one-week weekly lag; it is a practical "
        "approximation, not a historical release-vintage database. The results do not demonstrate "
        "that liquidity causes market returns and must not be "
        "read as an investable signal.",
        icon=":material/warning:",
    )
    st.caption("Source: Coin Metrics Community Data (`btc.PriceUSD`), licensed CC BY-NC 4.0.")


def research_guide_page() -> None:
    st.title("Research guide")
    st.markdown(
        """
        This page defines the concepts, data, and assumptions behind the current prototype. The
        guiding principle is simple: **measured data, model assumptions, and calibrated parameters
        must never be presented as the same thing.**
        """
    )

    st.subheader("What does global liquidity mean?")
    st.markdown(
        """
        Global liquidity describes the ease of financing in the international financial system.
        It has both a **funding** dimension—the ability to obtain cash or credit—and a **market**
        dimension—the ability to transact in assets without large price disruption. It is shaped
        jointly by central banks, commercial banks, non-bank intermediaries, collateral markets,
        investors, and cross-border currency funding.

        Liquidity is not a single observable quantity. A serious framework therefore compares
        several price and quantity indicators rather than treating one balance-sheet series as a
        complete answer. The BIS likewise describes global liquidity as an unobservable system
        property that must be assessed through multiple indicators.
        """
    )

    with st.container(horizontal=True):
        with st.container(border=True):
            st.markdown("#### Measured data")
            st.write(
                "Public observations with provider, series ID, units, dates, and retrieval time."
            )
            st.badge("Implemented", color="green")
        with st.container(border=True):
            st.markdown("#### Model assumptions")
            st.write(
                "Declared transformations, frequency rules, formulas, and weights chosen here."
            )
            st.badge("Implemented", color="blue")
        with st.container(border=True):
            st.markdown("#### Calibrated parameters")
            st.write("Values fitted against a named public target using a documented procedure.")
            st.badge("Not used in v0.1", color="gray")

    st.subheader("Current US model definitions")
    with st.container(border=True):
        st.markdown("#### Model A — Fed assets")
        st.code("L_A(t) = FedAssets(t)", language=None)
        st.write(
            "The simplest central-bank balance-sheet measure. It ignores liability-side drains "
            "and does not represent all system-wide liquidity."
        )
    with st.container(border=True):
        st.markdown("#### Model B — Net Fed liquidity proxy")
        st.code("L_B(t) = FedAssets(t) - TGA(t) - ON_RRP(t)", language=None)
        st.write(
            "A common public-market proxy. It adjusts total assets for Treasury cash held at the "
            "Fed and balances absorbed through overnight reverse repo. It is not presented as a "
            "Michael Howell or CrossBorder Capital formula."
        )
    with st.container(border=True):
        st.markdown("#### Model C — Reserve-based liquidity")
        st.code("L_C(t) = ReserveBalances(t)", language=None)
        st.write(
            "A direct settlement-liquidity proxy. TGA and ON RRP are not subtracted again because "
            "their effects are already reflected in reserve balances, so another adjustment could "
            "double count those drains."
        )

    st.subheader("Glossary")
    glossary = {
        "Central-bank liquidity": (
            "Official balance-sheet capacity supplied by a central bank, including assets and "
            "reserve liabilities. It is important but narrower than global liquidity."
        ),
        "Bank reserves": (
            "Balances that eligible institutions hold at the Federal Reserve. They support "
            "settlement and monetary-policy implementation but are not directly spendable by "
            "the public."
        ),
        "Treasury General Account (TGA)": (
            "The US Treasury's operating cash account at the Federal Reserve. Changes can shift "
            "balances between the Treasury and the banking system."
        ),
        "Overnight reverse repo (ON RRP)": (
            "A Federal Reserve facility through which eligible counterparties place cash overnight "
            "against Treasury collateral. In the current proxy, the balance is treated as "
            "absorption."
        ),
        "Collateral and haircuts": (
            "Secured funding depends on acceptable collateral and the discount applied to it. "
            "Higher haircuts reduce the amount of financing obtainable from a given asset pool. "
            "Future scope."
        ),
        "Offshore dollar liquidity": (
            "US-dollar credit and funding activity outside the United States, including banking, "
            "bond, and FX-swap channels. It is outside the current US-only release."
        ),
    }
    for term, definition in glossary.items():
        with st.expander(term):
            st.write(definition)

    st.subheader("Frequency and data policy")
    st.markdown(
        """
        - Canonical research frequency: **weekly, Wednesday**.
        - Weekly H.4.1 series require an exact Wednesday observation.
        - Daily ON RRP uses the latest observation on or before Wednesday, with a maximum age of
          seven calendar days.
        - No balance-sheet values are interpolated.
        - Monetary inputs are standardized to **millions of US dollars** before model calculation.
        - Source date, source unit, alignment method, and staleness are retained in processed data.
        - Current-vintage FRED data can be revised; this project does not yet maintain real-time
          vintages.
        """
    )

    st.subheader("OGLI statistical methodology")
    st.markdown(
        """
        OGLI measures how unusual current liquidity momentum is relative to historical
        observations. For each model, it combines **60% of the expanding z-score of 3-month
        annualized growth** with **40% of the expanding z-score of 12-month year-over-year
        growth**, then applies `100 * Phi(MomentumScore)`.

        The default expanding z-score requires 104 valid observations and uses only information
        available through each date. Full-sample normalization is available in package code for
        exploratory research only because it contains look-ahead. OGLI is not normalized against
        the historical maximum, so new liquidity highs do not mechanically rescale its history.

        The weights, history requirement, and regime boundaries are declared in
        `config/model.yaml`. They are Open Global Liquidity assumptions, not calibrated parameters.
        OGLI is an independent methodology and is not the proprietary CrossBorder Capital GLI.
        """
    )

    st.subheader("Market validation methodology")
    st.markdown(
        """
        The initial validation slice compares each model's OGLI momentum score with the Coin
        Metrics Bitcoin USD price. Horizon zero is the contemporaneous one-week return
        ending at the signal date.
        Positive horizons are forward simple returns through 4, 8, 12, 26, or 52 weeks. The
        observation-date view is retained for exploratory comparison. The default
        available-information view delays the weekly signal by one week because Wednesday H.4.1
        observations are normally published after that Wednesday's market close. This is a
        configurable availability assumption, not a real-time release-vintage archive.

        These choices are statistical transformations configured in `config/model.yaml`. The
        results are not used to select OGLI weights and therefore are not calibrated parameters.
        The dashboard defaults to non-overlapping return windows and retains the overlapping view
        for comparison. Correlations have Fisher-transformed confidence intervals; regime tables
        report means, medians, positive-return shares, and Student-t confidence intervals around
        means. Smaller non-overlapping samples and current-vintage revisions remain important
        limitations. Correlation does not establish causation.

        Coin Metrics publishes the daily `PriceUSD` metric in its community archive under CC BY-NC
        4.0. This project uses it only for independent, non-commercial research and attributes the
        source.
        """
    )

    st.subheader("Data sources and further reading")
    st.markdown(
        """
        **Series used by v0.1**

        - [WALCL — Federal Reserve total assets](https://fred.stlouisfed.org/series/WALCL)
        - [WDTGAL — Treasury General Account](https://fred.stlouisfed.org/series/WDTGAL)
        - [RRPONTSYD — Overnight reverse repo](https://fred.stlouisfed.org/series/RRPONTSYD)
        - [WRBWFRBL — Reserve balances](https://fred.stlouisfed.org/series/WRBWFRBL)
        - [Bitcoin PriceUSD — Coin Metrics community data](https://github.com/coinmetrics/data)
        - [DGS10 — 10-year Treasury yield](https://fred.stlouisfed.org/series/DGS10)
        - [DGS2 — 2-year Treasury yield](https://fred.stlouisfed.org/series/DGS2)
        - [DTWEXBGS — Nominal broad U.S. dollar index](https://fred.stlouisfed.org/series/DTWEXBGS)

        **Primary documentation and broader context**

        - [Federal Reserve H.4.1 balance-sheet release](https://www.federalreserve.gov/releases/h41/default.htm)
        - [New York Fed: repo and reverse repo agreements](https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/repo-reverse-repo-agreements)
        - [Coin Metrics metric documentation](https://docs.coinmetrics.io/)
        - [BIS: global liquidity indicators](https://www.bis.org/statistics/dataportal/gli.htm)
        - [BIS: global liquidity background and interpretation](https://www.bis.org/publ/qtrpdf/r_qt1503u.htm)
        """
    )

    st.warning(
        "Open Global Liquidity is independent and unaffiliated. It is inspired by publicly "
        "discussed global-liquidity concepts, including work by Michael Howell and CrossBorder "
        "Capital, but does not reproduce or claim access to their proprietary data, methodology, "
        "or models.",
        icon=":material/info:",
    )


home_page = st.Page(
    landing_page,
    title="Overview",
    icon=":material/home:",
    default=True,
)
data_page = st.Page(
    data_dashboard_page,
    title="Data dashboard",
    icon=":material/monitoring:",
    url_path="dashboard",
)
markets_index_page = st.Page(
    markets_page,
    title="Liquidity vs markets",
    icon=":material/query_stats:",
    url_path="markets",
)
ogli_index_page = st.Page(
    ogli_page,
    title="OGLI index",
    icon=":material/speed:",
    url_path="ogli",
)
guide_page = st.Page(
    research_guide_page,
    title="Research guide",
    icon=":material/menu_book:",
    url_path="research-guide",
)
navigation = st.navigation(
    [home_page, ogli_index_page, markets_index_page, data_page, guide_page], position="top"
)
navigation.run()
