from __future__ import annotations

import numpy as np
import pandas as pd


def _num(series, default=0.0):
    return pd.to_numeric(series, errors="coerce").fillna(default).astype(float)


def clamp(series, low=0.0, high=100.0):
    return _num(series).clip(low, high)


def classify(score: float) -> str:
    score = float(np.clip(score, 0, 100))
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 35:
        return "Moderate"
    return "Low"


def blood_group_order():
    return ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]


def score_demand(demand: pd.DataFrame) -> pd.DataFrame:
    d = demand.copy()
    d["blood_group"] = d["blood_group"].astype(str)
    d["weekly_demand_units"] = _num(d["weekly_demand_units"])
    d["available_units"] = _num(d["available_units"])
    d["fulfillment_pct"] = np.where(
        d["weekly_demand_units"] > 0,
        d["available_units"] / d["weekly_demand_units"] * 100,
        100,
    ).clip(0, 150)
    d["demand_gap_units"] = (d["weekly_demand_units"] - d["available_units"]).clip(lower=0)
    d["gap_pressure"] = (d["demand_gap_units"] / d["weekly_demand_units"].replace(0, np.nan) * 100).fillna(0).clip(0, 100)
    d["demand_pressure"] = (
        0.55 * clamp(d["gap_pressure"])
        + 0.45 * (d["weekly_demand_units"] / max(d["weekly_demand_units"].max(), 1) * 100)
    ).clip(0, 100)
    d["demand_class"] = d["demand_pressure"].map(classify)
    return d


def score_donation_history(history: pd.DataFrame) -> pd.DataFrame:
    h = history.copy()
    for c in ["successful_donations_90d", "cancellation_rate_pct", "returning_donor_rate_pct", "avg_units_per_drive"]:
        h[c] = _num(h[c])
    h["reliability_score"] = (
        0.45 * clamp(h["returning_donor_rate_pct"])
        + 0.35 * (100 - clamp(h["cancellation_rate_pct"]))
        + 0.20 * (h["successful_donations_90d"] / max(h["successful_donations_90d"].max(), 1) * 100)
    ).clip(0, 100)
    return h


def score_travel(travel: pd.DataFrame) -> pd.DataFrame:
    t = travel.copy()
    t["travel_minutes"] = _num(t["travel_minutes"])
    t["public_transport_access_pct"] = clamp(t["public_transport_access_pct"])
    t["parking_capacity"] = _num(t["parking_capacity"])
    t["population_reach_index"] = clamp(t["population_reach_index"])
    t["travel_access_score"] = (
        0.38 * (100 - (t["travel_minutes"] / max(t["travel_minutes"].max(), 1) * 100).clip(0, 100))
        + 0.27 * t["public_transport_access_pct"]
        + 0.15 * (t["parking_capacity"] / max(t["parking_capacity"].max(), 1) * 100)
        + 0.20 * t["population_reach_index"]
    ).clip(0, 100)
    return t


def score_events(events: pd.DataFrame) -> pd.DataFrame:
    e = events.copy()
    e["event_attendance"] = _num(e["event_attendance"])
    e["event_relevance_score"] = clamp(e["event_relevance_score"])
    e["competing_event_pressure"] = clamp(e["competing_event_pressure"])
    e["calendar_opportunity_score"] = (
        0.60 * e["event_relevance_score"]
        + 0.25 * (e["event_attendance"] / max(e["event_attendance"].max(), 1) * 100)
        + 0.15 * (100 - e["competing_event_pressure"])
    ).clip(0, 100)
    return e


def build_drive_opportunities(demand, travel, events, history):
    d = score_demand(demand)
    t = score_travel(travel)
    e = score_events(events)
    h = score_donation_history(history)

    demand_index = float(d["demand_pressure"].mean())
    reliability = float(h["reliability_score"].mean())
    rows = []
    for _, site in t.iterrows():
        for _, ev in e.iterrows():
            if str(ev["zone"]) != str(site["zone"]):
                continue
            coverage = float(site["population_reach_index"])
            access = float(site["travel_access_score"])
            calendar = float(ev["calendar_opportunity_score"])
            opportunity = (
                0.38 * demand_index
                + 0.22 * access
                + 0.18 * calendar
                + 0.12 * reliability
                + 0.10 * coverage
            )
            estimated_capacity = max(20, int(round(0.55 * site["parking_capacity"] + 0.35 * site["population_reach_index"])))
            rows.append({
                "site_id": site["site_id"],
                "site_name": site["site_name"],
                "zone": site["zone"],
                "date": ev["date"],
                "event_name": ev["event_name"],
                "access_score": round(access, 1),
                "calendar_score": round(calendar, 1),
                "demand_pressure": round(demand_index, 1),
                "donor_reliability": round(reliability, 1),
                "population_reach": round(coverage, 1),
                "estimated_capacity": estimated_capacity,
                "opportunity_score": round(float(np.clip(opportunity, 0, 100)), 1),
            })
    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("No site/event zone matches were found.")
    out["priority"] = out["opportunity_score"].map(classify)
    return out.sort_values(["opportunity_score", "estimated_capacity"], ascending=False)


def blood_group_gap_table(demand, history=None):
    d = score_demand(demand)
    out = d[["blood_group", "weekly_demand_units", "available_units", "demand_gap_units", "fulfillment_pct", "demand_pressure", "demand_class"]].copy()
    if history is not None:
        h = score_donation_history(history)
        if "blood_group" in h.columns:
            donor = h.groupby("blood_group", as_index=False)["successful_donations_90d"].mean()
            out = out.merge(donor, on="blood_group", how="left")
    return out.sort_values("demand_pressure", ascending=False)


def scenario_opportunity(base_score: float, demand_change_pct=0, access_change=0, calendar_change=0, capacity_change_pct=0):
    score = (
        base_score
        + 0.38 * np.clip(demand_change_pct, -50, 100) / 2.0
        + 0.22 * access_change
        + 0.18 * calendar_change
        + 0.10 * np.clip(capacity_change_pct, -50, 100) / 2.0
    )
    return float(np.clip(score, 0, 100))


def data_quality(df: pd.DataFrame):
    return pd.DataFrame([
        {"column": c, "missing": int(df[c].isna().sum()), "unique": int(df[c].nunique(dropna=True)), "dtype": str(df[c].dtype)}
        for c in df.columns
    ])
