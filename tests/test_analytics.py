import pandas as pd
from analytics import build_drive_opportunities, blood_group_gap_table, classify, score_donation_history, score_travel, score_events


def load():
    base='data/'
    return (
        pd.read_csv(base+'sample_blood_group_demand.csv'),
        pd.read_csv(base+'sample_donation_history.csv'),
        pd.read_csv(base+'sample_travel_access.csv'),
        pd.read_csv(base+'sample_event_calendar.csv'),
    )


def test_classification():
    assert classify(10)=='Low'
    assert classify(60)=='High'
    assert classify(90)=='Critical'


def test_gap_and_scores():
    d,h,t,e=load()
    gaps=blood_group_gap_table(d,h)
    assert len(gaps)==8
    assert gaps['demand_gap_units'].ge(0).all()
    assert score_donation_history(h)['reliability_score'].between(0,100).all()
    assert score_travel(t)['travel_access_score'].between(0,100).all()
    assert score_events(e)['calendar_opportunity_score'].between(0,100).all()


def test_drive_opportunities():
    d,h,t,e=load()
    out=build_drive_opportunities(d,t,e,h)
    assert not out.empty
    assert out['opportunity_score'].between(0,100).all()
    assert {'site_id','date','event_name','estimated_capacity','priority'}.issubset(out.columns)
