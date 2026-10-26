# Fixed synthetic snapshot
All rows originate from this repository's fictional generator. This is not masked business data.
charges: one charge category per provider / tracking_id / ship_date.
parcels: one row per provider / tracking_id / ship_date.
rejected: one rejected input row, with synthetic source filename and row number only.
Amounts used in BI are integer CNY cents; units come from parcels only.
manifest.json records hashes and fixture expectations.
Run the normal ETL separately; use powerbi/build_demo.py only when intentionally updating this fixed snapshot.

Serialization: UTF-8 without BOM; LF. Manifest records exact byte SHA256; Git enforces LF. Values are unchanged by this serialization repair.
