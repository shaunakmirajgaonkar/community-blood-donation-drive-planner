from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    blood_group_gap_table,
    build_drive_opportunities,
    classify,
    data_quality,
    scenario_opportunity,
    score_donation_history,
    score_events,
    score_travel,
)

st.set_page_config(page_title="Community Blood Donation Drive Planner", page_icon="🩸", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#f8fbff 0%,#fff 46%,#f7fbfa);color:#162033}
.block-container{max-width:1500px;padding-top:1rem}
h1,h2,h3,h4,p,label,span,div{color:#162033}
.hero{background:linear-gradient(135deg,#fff0f3,#eef7ff 48%,#eefbf5);border:1px solid #e1e8f0;border-radius:28px;padding:28px 30px;box-shadow:0 13px 32px rgba(39,61,87,.08);margin-bottom:18px}
.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:800;color:#b43d55!important}.hero-title{font-size:2.2rem;font-weight:850}.hero-sub{color:#607087!important;font-size:1rem;margin-top:6px}
.pill{display:inline-block;background:#fff;border:1px solid #dce6ef;border-radius:999px;padding:6px 11px;margin:10px 6px 0 0;font-size:.74rem;font-weight:750;color:#405873!important}
.kpi{background:#fff;border:1px solid #e2e9ef;border-radius:18px;padding:17px 18px;box-shadow:0 8px 21px rgba(29,55,77,.06)}.kpi-label{font-size:.77rem;font-weight:700;color:#758195!important}.kpi-value{font-size:1.7rem;font-weight:850;margin-top:4px}.kpi-note{font-size:.76rem;color:#7d899a!important}
.note{background:#f6f9fc;border-left:4px solid #4f8fbf;border-radius:10px;padding:12px 14px;color:#5e6b7d!important}
</style>
""", unsafe_allow_html=True)

BASE = Path(__file__).parent


def metric(label, value, note):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)


def read_csv(upload, fallback):
    if upload is not None:
        try:
            return pd.read_csv(upload), upload.name
        except Exception as exc:
            st.error(f"Unable to read {upload.name}: {exc}")
            st.stop()
    return pd.read_csv(fallback), fallback.name


with st.sidebar:
    st.markdown("## 🩸 BloodFlow Local")
    st.caption("100% local • CSV-first • no external APIs")
    st.markdown("### Data inputs")
    up_demand = st.file_uploader("Blood-group demand CSV", type=["csv"])
    up_history = st.file_uploader("Donation history CSV", type=["csv"])
    up_travel = st.file_uploader("Travel access CSV", type=["csv"])
    up_events = st.file_uploader("Event calendar CSV", type=["csv"])
    use_sample = st.toggle("Use bundled sample data", value=True)

if not use_sample and not all([up_demand, up_history, up_travel, up_events]):
    st.info("Upload all four CSV datasets or turn on bundled sample data.")
    st.stop()

(demand, demand_src) = read_csv(up_demand if not use_sample else None, BASE/"data"/"sample_blood_group_demand.csv")
(history, history_src) = read_csv(up_history if not use_sample else None, BASE/"data"/"sample_donation_history.csv")
(travel, travel_src) = read_csv(up_travel if not use_sample else None, BASE/"data"/"sample_travel_access.csv")
(events, events_src) = read_csv(up_events if not use_sample else None, BASE/"data"/"sample_event_calendar.csv")

required_map = {
    "demand": ["blood_group","weekly_demand_units","available_units"],
    "history": ["blood_group","successful_donations_90d","cancellation_rate_pct","returning_donor_rate_pct","avg_units_per_drive"],
    "travel": ["site_id","site_name","zone","travel_minutes","public_transport_access_pct","parking_capacity","population_reach_index"],
    "events": ["date","event_name","zone","event_attendance","event_relevance_score","competing_event_pressure"],
}
for name, cols in required_map.items():
    current = {"demand": demand, "history": history, "travel": travel, "events": events}[name]
    missing = [c for c in cols if c not in current.columns]
    if missing:
        st.error(f"{name.title()} CSV is missing: {', '.join(missing)}")
        st.stop()

opp = build_drive_opportunities(demand, travel, events, history)
gaps = blood_group_gap_table(demand, history)
hist_scored = score_donation_history(history)
travel_scored = score_travel(travel)
events_scored = score_events(events)

with st.sidebar:
    st.divider()
    st.markdown("### Navigation")
    page = st.radio("Open module", [
        "Overview", "Blood-Group Demand", "Donor Reliability", "Access & Reach", "Calendar Opportunities",
        "Drive Planner", "Priority Queue", "Scenario Lab", "Reports & Export"
    ], label_visibility="collapsed")
    st.divider()
    st.caption(f"Demand: {demand_src}")
    st.caption(f"History: {history_src}")
    st.caption(f"Travel: {travel_src}")
    st.caption(f"Events: {events_src}")

st.markdown("""
<div class="hero">
<div class="eyebrow">LOCAL-FIRST • COMMUNITY DONATION PLANNING INTELLIGENCE</div>
<div class="hero-title">Community Blood Donation Drive Planner</div>
<div class="hero-sub">Transparent planning support for where and when community blood drives may be useful, using blood-group demand, donation history, travel access and local event-calendar signals.</div>
<div><span class="pill">Demand gap analysis</span><span class="pill">Donor reliability</span><span class="pill">Travel reach</span><span class="pill">Calendar matching</span><span class="pill">Capacity planning</span><span class="pill">What-if scenarios</span></div>
</div>
""", unsafe_allow_html=True)

high_priority = int(opp.priority.isin(["High", "Critical"]).sum())
avg_demand = float(gaps.demand_pressure.mean())
avg_access = float(travel_scored.travel_access_score.mean())
avg_rel = float(hist_scored.reliability_score.mean())

c = st.columns(5)
for col, vals in zip(c, [
    ("Blood groups", f"{demand['blood_group'].nunique()}", "tracked groups"),
    ("Avg demand pressure", f"{avg_demand:.1f}", "0–100 screening index"),
    ("Priority opportunities", f"{high_priority}", "High / Critical"),
    ("Travel access", f"{avg_access:.1f}", "average access score"),
    ("Donor reliability", f"{avg_rel:.1f}", "historical planning index"),
]):
    with col: metric(*vals)

if page == "Overview":
    a,b = st.columns([1.15,.85])
    with a:
        st.subheader("Top drive opportunities")
        fig = px.bar(opp.head(12), x="opportunity_score", y="site_name", orientation="h", color="priority",
                     hover_data=["zone","date","event_name","estimated_capacity","access_score","calendar_score"])
        fig.update_layout(height=500, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="Opportunity score", yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.subheader("Blood-group demand gap")
        fig = px.bar(gaps, x="blood_group", y="demand_gap_units", color="demand_class",
                     labels={"demand_gap_units":"Estimated weekly gap (units)"})
        fig.update_layout(height=500, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Suggested planning queue")
    st.dataframe(opp.head(15), use_container_width=True, hide_index=True)

elif page == "Blood-Group Demand":
    st.subheader("Blood-group demand and fulfillment")
    fig = px.scatter(gaps, x="weekly_demand_units", y="fulfillment_pct", size=np.maximum(gaps.demand_gap_units,1), color="demand_class", hover_name="blood_group",
                     labels={"weekly_demand_units":"Weekly demand (units)", "fulfillment_pct":"Fulfillment (%)"})
    fig.update_layout(height=470, yaxis_range=[0,150])
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(gaps, use_container_width=True, hide_index=True)

elif page == "Donor Reliability":
    st.subheader("Historical donor response signals")
    fig = px.scatter(hist_scored, x="cancellation_rate_pct", y="returning_donor_rate_pct", size=np.maximum(hist_scored.successful_donations_90d,1), color="reliability_score",
                     hover_name="zone" if "zone" in hist_scored.columns else "blood_group")
    fig.update_layout(height=470, xaxis_title="Cancellation rate (%)", yaxis_title="Returning-donor rate (%)")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(hist_scored.sort_values("reliability_score", ascending=False), use_container_width=True, hide_index=True)

elif page == "Access & Reach":
    st.subheader("Travel accessibility and population reach")
    a,b=st.columns(2)
    with a:
        fig=px.scatter(travel_scored,x="travel_minutes",y="travel_access_score",size="population_reach_index",color="zone",hover_name="site_name")
        fig.update_layout(height=450,xaxis_title="Travel time (min)",yaxis_title="Access score")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.bar(travel_scored.sort_values("travel_access_score",ascending=False),x="travel_access_score",y="site_name",orientation="h",color="population_reach_index")
        fig.update_layout(height=450, yaxis_title=None, xaxis_title="Travel access score")
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(travel_scored,use_container_width=True,hide_index=True)

elif page == "Calendar Opportunities":
    st.subheader("Event-calendar opportunity signals")
    fig=px.scatter(events_scored,x="event_attendance",y="calendar_opportunity_score",size="event_relevance_score",color="zone",hover_name="event_name")
    fig.update_layout(height=470,xaxis_title="Event attendance",yaxis_title="Calendar opportunity score")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(events_scored.sort_values("calendar_opportunity_score",ascending=False),use_container_width=True,hide_index=True)

elif page == "Drive Planner":
    st.subheader("Drive planning board")
    zones = sorted(opp.zone.astype(str).unique())
    selected_zone = st.selectbox("Planning zone", ["All zones"] + zones)
    filtered = opp if selected_zone == "All zones" else opp[opp.zone.astype(str)==selected_zone]
    top_n = st.slider("Candidate drives to display", 5, min(30, len(filtered)), min(12, len(filtered)))
    show = filtered.head(top_n)
    st.dataframe(show, use_container_width=True, hide_index=True)
    fig=px.scatter(show,x="access_score",y="calendar_score",size="estimated_capacity",color="opportunity_score",hover_name="site_name",hover_data=["date","event_name","zone"])
    fig.update_layout(height=470,xaxis_title="Travel access score",yaxis_title="Calendar opportunity score")
    st.plotly_chart(fig,use_container_width=True)

elif page == "Priority Queue":
    st.subheader("Priority review queue")
    show = opp[opp.priority.isin(["High","Critical"])].sort_values("opportunity_score",ascending=False)
    if show.empty:
        st.success("No High/Critical planning opportunities under the current inputs.")
    else:
        st.info("This is a planning queue for additional operational review, not a medical eligibility or donor-selection system.")
        st.dataframe(show,use_container_width=True,hide_index=True)
        st.download_button("Download priority queue CSV",show.to_csv(index=False).encode(),"blood_drive_priority_queue.csv","text/csv",use_container_width=True)

elif page == "Scenario Lab":
    st.subheader("What-if drive planning")
    st.caption("Explore directional changes to opportunity under planning assumptions. Results are not guarantees of attendance, blood collection, or clinical supply impact.")
    base = float(opp.opportunity_score.iloc[0])
    c1,c2,c3,c4=st.columns(4)
    demand_change=c1.slider("Demand change (%)",-40,100,20,5)
    access_change=c2.slider("Access improvement",-30,30,10,5)
    calendar_change=c3.slider("Calendar opportunity change",-30,30,10,5)
    capacity_change=c4.slider("Capacity change (%)",-50,100,15,5)
    after=scenario_opportunity(base,demand_change,access_change,calendar_change,capacity_change)
    delta=after-base
    m=st.columns(3)
    with m[0]: metric("Baseline opportunity",f"{base:.1f}",classify(base))
    with m[1]: metric("Scenario opportunity",f"{after:.1f}",classify(after))
    with m[2]: metric("Change",f"{delta:+.1f}","planning signal")
    chart=pd.DataFrame({"State":["Baseline","Scenario"],"Score":[base,after]})
    fig=px.bar(chart,x="State",y="Score",text_auto=".1f")
    fig.update_layout(height=360,yaxis_range=[0,100])
    st.plotly_chart(fig,use_container_width=True)

elif page == "Reports & Export":
    t1,t2,t3=st.tabs(["Opportunity report","Blood-group report","Data quality"])
    with t1:
        st.dataframe(opp,use_container_width=True,hide_index=True)
        st.download_button("Download opportunity report",opp.to_csv(index=False).encode(),"blood_drive_opportunity_report.csv","text/csv",use_container_width=True)
    with t2:
        st.dataframe(gaps,use_container_width=True,hide_index=True)
        st.download_button("Download blood-group gap report",gaps.to_csv(index=False).encode(),"blood_group_gap_report.csv","text/csv",use_container_width=True)
    with t3:
        for label, frame in [("Demand",demand),("History",history),("Travel",travel),("Events",events)]:
            st.markdown(f"**{label}**")
            st.dataframe(data_quality(frame),use_container_width=True,hide_index=True)

st.markdown("---")
st.markdown('<div class="note">Planning support only. Actual donor recruitment, donor eligibility, collection procedures, blood testing, storage, and clinical supply decisions must follow qualified blood-bank and public-health procedures.</div>',unsafe_allow_html=True)
st.caption("BloodFlow Local • 100% local Python/Streamlit analytics • no external APIs")
