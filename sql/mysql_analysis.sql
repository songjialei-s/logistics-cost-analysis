-- MySQL 8+ reference. CNY amounts use fictional configured FX and integer cents.
-- One row per charge category per parcel; parcel units must not be summed across charges.
-- 1 Monthly cost and calendar-adjacent month-over-month change (NULL if missing month).
WITH monthly AS (
 SELECT DATE_FORMAT(ship_date,'%Y-%m') month, SUM(amount_cny_minor)/100.0 cost_cny
 FROM charges GROUP BY DATE_FORMAT(ship_date,'%Y-%m')
), prior AS (
 SELECT *, LAG(cost_cny) OVER(ORDER BY month) previous_cost,
 LAG(month) OVER(ORDER BY month) previous_month FROM monthly
)
SELECT month,cost_cny, CASE WHEN previous_month=DATE_FORMAT(DATE_SUB(STR_TO_DATE(CONCAT(month,'-01'),'%Y-%m-%d'), INTERVAL 1 MONTH),'%Y-%m')
 THEN (cost_cny-previous_cost)/NULLIF(previous_cost,0) END mom_ratio FROM prior;

-- 2 Provider cost structure (not service performance ranking).
SELECT provider,category,SUM(amount_cny_minor)/100.0 cost_cny
FROM charges GROUP BY provider,category;

-- 3 Fee category shares.
SELECT category,SUM(amount_cny_minor)*1.0/(SELECT SUM(amount_cny_minor) FROM charges) share
FROM charges GROUP BY category;

-- 4 Freight only: cost per parcel and per item; count each parcel once.
WITH parcels AS (
 SELECT provider,tracking_id,ship_date,MAX(item_count) items,
 SUM(CASE WHEN category='freight' THEN amount_cny_minor ELSE 0 END) freight_minor,
 MAX(CASE WHEN category='freight' THEN 1 ELSE 0 END) has_freight
 FROM charges GROUP BY provider,tracking_id,ship_date
)
SELECT SUM(freight_minor)/100.0/NULLIF(SUM(has_freight),0) freight_per_parcel_cny,
 SUM(freight_minor)/100.0/NULLIF(SUM(CASE WHEN has_freight=1 THEN items ELSE 0 END),0) freight_per_item_cny
FROM parcels;

-- 5 Demo threshold: a charge > CNY 400 is review-worthy, not a proven billing error.
SELECT provider,tracking_id,ship_date,category,amount_cny_minor/100.0 cost_cny
FROM charges WHERE is_anomaly=1;
