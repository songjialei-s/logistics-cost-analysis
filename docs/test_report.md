# Local validation report

Validated on 2026-10-26 using bundled Python; library versions: {"pandas": "3.0.1", "openpyxl": "3.1.5"}.
`python -m unittest discover -s tests -v`: 3 tests passed.

Coverage: all six mappings and kg/g/lb conversions; valid amount parsing;
invalid dates/FX coverage, negative amounts, zero weight, fractional quantities,
unknown categories; exact duplicate skipping; conflicting duplicate transaction
rollback; CSV exports; unchanged-file skip; changed-file rejection and rebuild;
all five SQLite analysis statements and independently specified expected results.

First run: 6 files, 144 inserted, 6 duplicate rows skipped, 18 rejected;
72 parcels, 144 items, 1 designed review flag.
Second run: 6 files skipped, 0 inserted. Persisted rejects remain 18.
Monthly costs CNY 2,360 / 2,488 / 3,099, total 7,947.
Freight per parcel 99.708333 CNY; freight per item 49.854167 CNY.

Text and XLSX XML scan: 25 candidate source/sample files examined;
no detected private IP addresses, literal password/token assignments or company paths.
No Git directory or inherited history exists. Loopback-only MySQL opt-in adapter
is not executed. SQLite local tests make no database server or API calls.
This is a targeted scan, not a universal secret scanner or ownership certification.
No original company directory was read or modified during this build.

Not validated: actual MySQL 8 integration, Power BI Desktop/DAX, production workload,
performance improvement or business savings. All results above are synthetic fixtures.
