# Quality and operational boundaries
Required headers are checked before reading records. Invalid dates, missing IDs,
nonfinite or negative amounts, nonpositive weights, noninteger item counts,
unknown categories and missing FX coverage are rejected and counted.
Identical business-key repeats are skipped; conflicting amounts/parcel attributes
abort and roll back the entire import. File state and data share one transaction.
SHA-256 includes file bytes and mapping/FX config. Unchanged files skip;
changed files/config require explicit --rebuild (local demo database only).
Input deletion is not synchronized; use a complete input set and rebuild.
Invalid rejected rows still mark a file as processed; fixing it needs rebuild.
No scheduler, concurrent runner support, refunds, historical FX service,
production deployment or automatic anomaly learning is implemented.
SQLite is the tested default. MySQL adapter and MySQL 8 SQL are supplied but not
integration-tested. No real API, shared drive or company source is used.
Power BI artifacts are preparation documents only.
