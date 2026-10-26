# Independent demo metric definitions

Status: historical Desktop screenshots confirm baseline totals; latest layout/interactions 待 Desktop 验证.

|Measure|Definition|
|---|---|
|Total Cost CNY|Selected charge cost, in fictional CNY.|
|Freight CNY|Freight in current scope; handling-only selection gives blank.|
|Parcels|Date/provider filtered parcels; category does not reduce this denominator.|
|Items|Each parcel counted once. Not summed on charges.|
|Cost per Parcel CNY|Selected category cost per all date/provider selected parcels.|
|Cost per Item CNY|Selected category cost per all date/provider selected items.|
|Freight per Parcel CNY|Every fixture parcel has freight, matching SQL freight-bearing denominator.|
|Freight per Item CNY|Matches SQL for this fixture; see coverage check.|
|Previous Month Cost CNY|Previous calendar month in current provider/category context.|
|Cost MoM|Month rows only; blank outside Date[Month] scope or for missing/zero previous cost.|
|Category Share|Share of all categories, retaining date/provider filters.|
|Charge Lines|Accepted fee lines in selected scope.|
|Review Charge Lines|Charge >400 fictional CNY; not a proven billing error.|
|Review Cost CNY|Flagged charge amount, not demonstrated savings.|
|Rejected Rows All Data|Global rejected snapshot. No date/provider/category filtering.|
|Freight Coverage Parcels|Should equal Parcels under date/provider filters for this fixture.|

## Scope and relationships
Date -> parcels -> charges, active single direction. Category only filters charges.
Freight metrics use KEEPFILTERS; selecting handling alone makes them blank.
No category filter changes parcel/item denominators. Every fixture parcel has freight;
check Freight Coverage Parcels = Parcels before applying SQL freight metrics to new data.
Rejected rows are global and disconnected; do not invent ship dates.
Months with no costs/previous month show blank growth, not zero.
There are no revenue, margin, service-quality or demonstrated-savings measures.


最新状态：用户已确认最终Desktop验证完成；当前项目中尚无新版三张PNG和独立PBIX，文件核查尚未完成。历史图继续明确标记为旧版，不替换为不存在的图片。
