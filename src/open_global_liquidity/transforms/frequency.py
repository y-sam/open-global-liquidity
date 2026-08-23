"""Auditable alignment of measured series to canonical Wednesdays."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


class FrequencyAlignmentError(ValueError):
    """Raised when frequency alignment would require an undocumented assumption."""


def align_to_weekly_wednesday(
    frame: pd.DataFrame,
    *,
    daily_asof_components: Iterable[str],
    daily_asof_max_staleness_days: int,
) -> pd.DataFrame:
    """Align source stocks to Wednesday without interpolation or future information.

    Weekly sources require an exact Wednesday observation. Configured daily components use the
    latest numeric observation on or before Wednesday, capped by a strict calendar-day tolerance.
    The chosen source date and staleness are retained so every aligned value remains auditable.
    """
    required = {
        "date",
        "country",
        "provider",
        "series_id",
        "component",
        "value",
        "unit",
        "frequency",
        "retrieved_at",
        "source_unit",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise FrequencyAlignmentError(
            f"Frequency alignment is missing columns: {', '.join(missing)}"
        )
    if frame.empty:
        raise FrequencyAlignmentError("Frequency alignment received no observations")
    if daily_asof_max_staleness_days < 0:
        raise FrequencyAlignmentError("daily_asof_max_staleness_days cannot be negative")

    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"]).dt.normalize()
    if data.duplicated(["component", "date"]).any():
        raise FrequencyAlignmentError("Source data has duplicate component/date observations")

    numeric = data.dropna(subset=["value"])
    bounds = numeric.groupby("component")["date"].agg(["min", "max"])
    if bounds.empty:
        raise FrequencyAlignmentError("Frequency alignment received no numeric observations")
    calendar_start = bounds["min"].max()
    calendar_end = bounds["max"].min()
    calendar = pd.DataFrame({"date": pd.date_range(calendar_start, calendar_end, freq="W-WED")})
    if calendar.empty:
        raise FrequencyAlignmentError("Series do not share an overlapping Wednesday window")

    daily_components = set(daily_asof_components)
    aligned_frames: list[pd.DataFrame] = []
    for component, component_data in data.groupby("component", sort=True):
        component_data = component_data.sort_values("date")
        source_frequencies = set(component_data["frequency"].dropna())
        if len(source_frequencies) != 1:
            raise FrequencyAlignmentError(f"Component {component} has inconsistent frequencies")
        source_frequency = next(iter(source_frequencies))
        is_daily = source_frequency == "Daily"
        if is_daily and component not in daily_components:
            raise FrequencyAlignmentError(
                f"Daily component {component} lacks an explicit as-of alignment policy"
            )

        source = component_data.rename(columns={"date": "source_date"})
        if is_daily:
            source = source.dropna(subset=["value"])
            aligned = pd.merge_asof(
                calendar,
                source,
                left_on="date",
                right_on="source_date",
                direction="backward",
                tolerance=pd.Timedelta(days=daily_asof_max_staleness_days),
            )
            aligned["alignment_method"] = "latest_prior_daily"
        else:
            aligned = calendar.merge(source, left_on="date", right_on="source_date", how="left")
            aligned["alignment_method"] = "exact_wednesday"

        aligned["component"] = component
        aligned["source_frequency"] = source_frequency
        aligned["frequency"] = "Weekly, As of Wednesday"
        aligned["staleness_days"] = (aligned["date"] - aligned["source_date"]).dt.days.astype(
            "Int64"
        )
        aligned_frames.append(aligned)

    result = pd.concat(aligned_frames, ignore_index=True)
    result["unit"] = "Millions of U.S. Dollars"
    columns = [
        "date",
        "country",
        "provider",
        "series_id",
        "component",
        "value",
        "unit",
        "frequency",
        "source_date",
        "source_unit",
        "source_frequency",
        "staleness_days",
        "alignment_method",
        "retrieved_at",
    ]
    return result[columns].sort_values(["date", "component"]).reset_index(drop=True)


def align_market_closes_to_weekly_wednesday(
    frame: pd.DataFrame,
    *,
    daily_asof_components: Iterable[str],
    daily_asof_max_staleness_days: int,
) -> pd.DataFrame:
    """Align each daily market close independently to Wednesday without interpolation.

    The latest close on or before each Wednesday is selected with a configured calendar-day
    tolerance. This handles market holidays without using a future close. Source date, original
    frequency, staleness, and original units remain attached to every selected observation.
    """
    required = {
        "date",
        "country",
        "provider",
        "series_id",
        "component",
        "value",
        "unit",
        "frequency",
        "retrieved_at",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise FrequencyAlignmentError(
            f"Market frequency alignment is missing columns: {', '.join(missing)}"
        )
    if frame.empty:
        raise FrequencyAlignmentError("Market frequency alignment received no observations")
    if daily_asof_max_staleness_days < 0:
        raise FrequencyAlignmentError("Market as-of staleness cannot be negative")

    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"]).dt.normalize()
    if data.duplicated(["component", "date"]).any():
        raise FrequencyAlignmentError("Market data has duplicate component/date observations")

    allowed = set(daily_asof_components)
    aligned_frames: list[pd.DataFrame] = []
    for component, component_data in data.groupby("component", sort=True):
        if component not in allowed:
            raise FrequencyAlignmentError(
                f"Daily market component {component} lacks an explicit as-of alignment policy"
            )
        source_frequencies = set(component_data["frequency"].dropna())
        if len(source_frequencies) != 1:
            raise FrequencyAlignmentError(
                f"Market component {component} has inconsistent frequency"
            )
        source_frequency = next(iter(source_frequencies))
        if not source_frequency.startswith("Daily"):
            raise FrequencyAlignmentError(
                f"Market component {component} must be configured as a daily close"
            )
        numeric = component_data.dropna(subset=["value"]).sort_values("date")
        if numeric.empty:
            raise FrequencyAlignmentError(f"Market component {component} has no numeric closes")
        calendar = pd.DataFrame(
            {"date": pd.date_range(numeric["date"].min(), numeric["date"].max(), freq="W-WED")}
        )
        source = numeric.rename(columns={"date": "source_date"})
        source["source_unit"] = source["unit"]
        source = source.drop(columns="unit")
        aligned = pd.merge_asof(
            calendar,
            source,
            left_on="date",
            right_on="source_date",
            direction="backward",
            tolerance=pd.Timedelta(days=daily_asof_max_staleness_days),
        )
        aligned["component"] = component
        aligned["unit"] = aligned["source_unit"]
        aligned["source_frequency"] = source_frequency
        aligned["frequency"] = "Weekly, As of Wednesday"
        aligned["staleness_days"] = (aligned["date"] - aligned["source_date"]).dt.days.astype(
            "Int64"
        )
        aligned["alignment_method"] = "latest_prior_market_close"
        aligned_frames.append(aligned)

    columns = [
        "date",
        "country",
        "provider",
        "series_id",
        "component",
        "value",
        "unit",
        "frequency",
        "source_date",
        "source_unit",
        "source_frequency",
        "staleness_days",
        "alignment_method",
        "retrieved_at",
    ]
    return (
        pd.concat(aligned_frames, ignore_index=True)[columns]
        .sort_values(["date", "component"])
        .reset_index(drop=True)
    )
