# Data dictionary
Grain: one provider / tracking ID / ship date / category charge. At most one charge
of each category per parcel in this generic demo. Real multi-line invoices would
need invoice and charge-line IDs; do not reuse this key without domain review.

|Field|Meaning|
|---|---|
|provider, tracking_id|Fictional carrier and synthetic parcel ID|
|ship_date|ISO date parsed using an explicit provider format|
|category|freight or handling|
|currency|Original synthetic CNY/USD/EUR currency|
|amount_minor|Original amount in integer cents|
|fx_rate|Fictional CNY per original currency unit|
|amount_cny_minor|CNY cents, ROUND_HALF_UP for each charge|
|weight_kg|Positive parcel weight converted to kilograms|
|item_count|Positive integer item quantity; consistent across parcel charge lines|
|source_file, source_row|Synthetic file and Excel row for traceability|
|is_anomaly|1 if converted charge exceeds CNY 400; review flag only|

CSV also includes amount and amount_cny as human-readable decimal values.
Rejected records retain source and reason only, not invalid raw data.
