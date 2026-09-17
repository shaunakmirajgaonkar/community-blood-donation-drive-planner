# Data Dictionary

## Blood-group demand CSV
- `blood_group`: ABO/Rh group label
- `weekly_demand_units`: local weekly demand signal
- `available_units`: local available supply signal

## Donation history CSV
- `blood_group`: blood group
- `zone`: operational zone
- `successful_donations_90d`: completed donations in the local planning window
- `cancellation_rate_pct`: historical cancellation rate
- `returning_donor_rate_pct`: returning donor rate
- `avg_units_per_drive`: historical collection-volume signal

## Travel access CSV
- `site_id`: unique candidate site
- `site_name`: site label
- `zone`: local planning zone
- `travel_minutes`: representative travel time
- `public_transport_access_pct`: public-transport access indicator
- `parking_capacity`: approximate capacity indicator
- `population_reach_index`: local population-reach signal

## Event calendar CSV
- `date`: candidate planning date
- `event_name`: event/calendar context
- `zone`: local planning zone
- `event_attendance`: expected local attendance signal
- `event_relevance_score`: relevance of the event to community outreach
- `competing_event_pressure`: potential calendar competition signal
