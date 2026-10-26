-- setup_db.sql — สร้างตารางทั้งหมดใน database k3 (PostgreSQL)
-- ใช้: createdb k3 && psql -d k3 -f setup_db.sql
-- แล้ว load ข้อมูลด้วยคำสั่ง \copy ใน RUNBOOK

CREATE TABLE IF NOT EXISTS President(
  PresidentName TEXT, YearBorn INT, StateBorn TEXT, PartyName TEXT);
CREATE TABLE IF NOT EXISTS Party(PartyName TEXT);
CREATE TABLE IF NOT EXISTS PresidentMarriage(
  PresidentName TEXT, SpouseName TEXT, SpouseBirthDay DATE,
  MarriageYear INT, MarriageStatus TEXT);
CREATE TABLE IF NOT EXISTS PresidentHolding(
  PresidentName TEXT, YearHolding INT, YearEnd INT,
  VicePresidentName TEXT, RunnerUp TEXT);

CREATE TABLE IF NOT EXISTS Ecommerce(
  OrderID TEXT, CustomerID TEXT, OrderDate DATE, ProductSKU TEXT,
  ProductName TEXT, Category TEXT, Brand TEXT, BasePrice NUMERIC,
  DiscountPercent NUMERIC, FinalPrice NUMERIC, Quantity INT,
  Revenue NUMERIC, Currency TEXT, CustomerAge INT, CustomerGender TEXT,
  CustomerCity TEXT, CustomerCountry TEXT, Region TEXT,
  MembershipTier TEXT, MarketingChannel TEXT, WebsiteVisits INT,
  TimeOnSite NUMERIC, CartAbandonment TEXT, ProductRating NUMERIC,
  CustomerSatisfaction NUMERIC, ShippingCost NUMERIC, DeliveryDays INT,
  ReturnStatus TEXT, RepeatCustomer TEXT, PurchaseFrequency INT,
  IsHighValue TEXT, SeasonalFactor NUMERIC, InventoryLevel INT,
  ConversionRate NUMERIC, CustomerLTV NUMERIC, AcquisitionCost NUMERIC,
  IsWeekendOrder TEXT, PaymentMethod TEXT);

-- ตารางล้านแถวสำหรับ RQ3 (โครงเดียวกับ Ecommerce)
CREATE TABLE IF NOT EXISTS Ecommerce1M (LIKE Ecommerce);
