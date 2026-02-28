-- Run this SQL to add new address columns to business_order table

ALTER TABLE business_order ADD COLUMN bill_address1 VARCHAR(255);
ALTER TABLE business_order ADD COLUMN bill_address2 VARCHAR(255);
ALTER TABLE business_order ADD COLUMN bill_city VARCHAR(100);
ALTER TABLE business_order ADD COLUMN bill_state VARCHAR(100);
ALTER TABLE business_order ADD COLUMN bill_pin VARCHAR(10);
ALTER TABLE business_order ADD COLUMN bill_country VARCHAR(100) DEFAULT 'India';
ALTER TABLE business_order ADD COLUMN ship_address1 VARCHAR(255);
ALTER TABLE business_order ADD COLUMN ship_address2 VARCHAR(255);
ALTER TABLE business_order ADD COLUMN ship_city VARCHAR(100);
ALTER TABLE business_order ADD COLUMN ship_state VARCHAR(100);
ALTER TABLE business_order ADD COLUMN ship_pin VARCHAR(10);
ALTER TABLE business_order ADD COLUMN ship_country VARCHAR(100) DEFAULT 'India';

-- Drop old columns if they exist
ALTER TABLE business_order DROP COLUMN IF EXISTS bill_address;
ALTER TABLE business_order DROP COLUMN IF EXISTS ship_address;
