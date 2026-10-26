# Metric definitions and expected demo results
All cross-currency metrics use explicit fictional CNY rates: CNY=1, USD=7, EUR=8,
valid January–March 2026 only. No market-rate accuracy is claimed. Missing coverage
is rejected. Native-currency cents are rounded first, then converted per charge.

- Total costs: freight + handling, in CNY.
- Provider/category structure: grouped sum of converted cents.
- Category share: category cost / all cost in current SQL scope.
- Single-parcel freight: freight total / distinct freight-bearing parcels.
- Single-item freight: freight total / items on freight-bearing parcels, once per parcel.
- MoM: (current month cost - previous calendar month cost) / previous cost;
  no preceding calendar month or zero denominator yields NULL.
- Exception review: converted individual charge > CNY 400, not proof of overbilling.

Expected: monthly costs 2,360 / 2,488 / 3,099 CNY; total 7,947 CNY.
Freight 7,179 CNY / 72 parcels / 144 items: 99.708333 CNY per parcel,
49.854167 CNY per item. One designed high-cost charge. These are test fixture values,
not internship business outcomes or savings.
