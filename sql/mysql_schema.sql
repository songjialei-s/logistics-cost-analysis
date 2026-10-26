-- MySQL 8+, local sandbox only. No credentials are included.
CREATE TABLE IF NOT EXISTS charges (
 provider VARCHAR(64) NOT NULL, tracking_id VARCHAR(80) NOT NULL,
 ship_date DATE NOT NULL, category VARCHAR(32) NOT NULL, currency CHAR(3) NOT NULL,
 amount_minor BIGINT NOT NULL, fx_rate VARCHAR(32) NOT NULL,
 amount_cny_minor BIGINT NOT NULL, weight_kg DOUBLE NOT NULL, item_count INT NOT NULL,
 source_file VARCHAR(128) NOT NULL, source_row INT NOT NULL, is_anomaly TINYINT NOT NULL,
 PRIMARY KEY(provider,tracking_id,ship_date,category)
);
