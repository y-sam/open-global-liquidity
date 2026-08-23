"""Streamlit presentation layer for Open Global Liquidity research."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
from dashboard_support import (  # noqa: E402
    COMPONENT_LABELS,
    DashboardDataError,
    latest_model_readings,
    latest_ogli_readings,
    latest_readings,
    load_dashboard_data,
    load_liquidity_model_data,
    load_market_comparisons,
    load_market_correlations,
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
MARKET_CORRELATIONS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_correlations.parquet"
MARKET_CORRELATIONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_correlations_snapshot.parquet"
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
    if not MARKET_COMPARISONS_PATH.is_file():
        return None, correlations, correlation_origin
    comparisons = _load_market_comparisons(
        str(MARKET_COMPARISONS_PATH), MARKET_COMPARISONS_PATH.stat().st_mtime_ns
    )
    return comparisons, correlations, "Local research data"


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
            "market_return": "S&P 500 return",
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
        "Retrospective comparison of OGLI momentum with S&P 500 returns. Correlation is not "
        "causation, a forecast, or parameter calibration."
    )
    try:
        comparisons, correlations, data_origin = _market_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/info:")
        st.markdown(
            "The official FRED `SP500` series is suitable for local research, but its source "
            "notes restrict redistribution. Run the pipeline with your own FRED key to create "
            "the market files locally:"
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        st.link_button(
            "Review official SP500 metadata",
            "https://fred.stlouisfed.org/series/SP500",
            icon=":material/open_in_new:",
        )
        return

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
        st.caption("Market: S&P 500 price index")
        st.caption(f"Data mode: {data_origin}")

    model_id = model_options[selected_model]
    horizon = horizon_options[selected_horizon_label]
    selected_summary = correlations.loc[
        (correlations["model_id"] == model_id)
        & (correlations["market_id"] == "sp500")
        & (correlations["horizon_weeks"] == horizon)
    ].iloc[0]
    model_correlations = correlations.loc[
        (correlations["model_id"] == model_id) & (correlations["market_id"] == "sp500")
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
            "This hosted view contains only aggregate research statistics. Raw S&P 500 levels, "
            "individual return observations, scatter points, and rolling correlations remain "
            "local-only because the source series has redistribution restrictions.",
            icon=":material/privacy_tip:",
        )
        st.warning(
            "These exploratory correlations use observation dates, do not model publication lags, "
            "and do not establish causation or an investable signal.",
            icon=":material/warning:",
        )
        return

    selected_pairs = comparisons.loc[
        (comparisons["model_id"] == model_id)
        & (comparisons["market_id"] == "sp500")
        & (comparisons["horizon_weeks"] == horizon)
    ].dropna(subset=["liquidity_signal", "market_return"])
    latest_pair = selected_pairs.iloc[-1]

    with st.container(horizontal=True):
        st.metric(
            "Pearson correlation",
            "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
            border=True,
        )
        st.metric("Paired observations", f"{int(selected_summary['observations']):,}", border=True)
        st.metric("Latest paired OGLI", f"{latest_pair['ogli']:.1f}", border=True)
        st.metric("Latest paired S&P return", f"{latest_pair['market_return']:.1%}", border=True)

    scatter_tab, rolling_tab, horizons_tab, data_tab = st.tabs(
        ["Relationship", "Rolling correlation", "Across horizons", "Paired data"]
    )
    with scatter_tab:
        st.plotly_chart(
            _market_scatter_figure(
                selected_pairs,
                f"{selected_model} vs S&P 500 · {selected_horizon_label}",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "Each point anchors the expanding OGLI momentum score at t to the named market-return "
            "window. Forward outcomes are never inputs to OGLI."
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
    with data_tab:
        table = selected_pairs[
            [
                "date",
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
                "ogli": st.column_config.NumberColumn("OGLI", format="%.1f"),
                "liquidity_signal": st.column_config.NumberColumn("Momentum score", format="%+.2f"),
                "market_return": st.column_config.NumberColumn("S&P return", format="percent"),
                "return_start_date": st.column_config.DateColumn(
                    "Return start", format="YYYY-MM-DD"
                ),
                "return_end_date": st.column_config.DateColumn("Return end", format="YYYY-MM-DD"),
            },
        )

    st.warning(
        "These statistics are sensitive to sample selection, overlapping forward-return windows, "
        "data revisions, publication lags, and common macroeconomic drivers. The current "
        "exploratory alignment uses observation dates and does not model when each source became "
        "publicly "
        "available. It does not demonstrate that liquidity causes market returns and must not be "
        "read as an investable signal.",
        icon=":material/warning:",
    )
    st.caption(
        "Source: S&P Dow Jones Indices LLC via FRED (`SP500`). Price index only; dividends are "
        "excluded. Raw market observations are not included in the public repository snapshot."
    )


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
        The initial validation slice compares each model's OGLI momentum score with the S&P 500
        price index. Horizon zero is the contemporaneous one-week return ending at the signal date.
        Positive horizons are forward simple returns from the signal date through 4, 8, 12, 26,
        or 52 weeks later. Pearson correlations use at least 52 paired observations; rolling
        correlations use a 52-week window with a 26-observation minimum.

        These choices are statistical transformations configured in `config/model.yaml`. The
        results are not used to select OGLI weights and therefore are not calibrated parameters.
        Forward-return windows overlap, especially at longer horizons, which reduces the effective
        independence of observations. The current alignment uses observation dates and does not
        adjust for when each underlying release became publicly available, so it is exploratory
        analysis rather than a realistic backtest. Correlation does not establish causation.

        FRED's `SP500` is a daily-close price index, excludes dividends, and provides a rolling ten
        years of history. Its source notes restrict redistribution, so this project supports it for
        local research but does not bundle its raw observations or market-analysis files in public
        dashboard snapshots.
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

        **Primary documentation and broader context**

        - [Federal Reserve H.4.1 balance-sheet release](https://www.federalreserve.gov/releases/h41/default.htm)
        - [New York Fed: repo and reverse repo agreements](https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/repo-reverse-repo-agreements)
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
