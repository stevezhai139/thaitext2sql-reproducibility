r"""
scale_ecommerce.py — ขยาย Ecommerce_Dataset.csv (2,390 แถว) เป็น N แถว
สำหรับการทดลอง efficiency (RQ3) โดยรักษา distribution ของคอลัมน์เดิม

วิธี: bootstrap resample แถวเดิม แล้ว perturb เฉพาะคอลัมน์ที่ต้อง unique/
กระจาย: OrderID ใหม่ (ORD + running), CustomerID สุ่มจาก pool ขยาย,
OrderDate jitter ภายในช่วงปีเดิม, ตัวเลขต่อเนื่อง jitter ±5% — คอลัมน์
categorical คงค่าจากแถวต้นแบบ (รักษา correlation ภายในแถว)

Usage:
  python3 scale_ecommerce.py --src <Ecommerce_Dataset.csv> \
      --n 1000000 --out ecommerce_1m.csv --seed 42
Run of record: เครื่องผู้เขียน. Load เข้า PostgreSQL ด้วย \copy
"""
import argparse
import csv
import random
from datetime import date, timedelta

NUMERIC_JITTER = {"BasePrice", "FinalPrice", "Revenue", "ShippingCost",
                  "CustomerLTV", "AcquisitionCost", "TimeOnSite"}
INT_COLS = {"Quantity", "CustomerAge", "WebsiteVisits", "DeliveryDays",
            "PurchaseFrequency", "InventoryLevel"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--customers", type=int, default=120_000,
                    help="ขนาด pool CustomerID (คุม repeat-customer realism)")
    a = ap.parse_args()
    rng = random.Random(a.seed)

    with open(a.src, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        hdr = rd.fieldnames
        base = list(rd)
    if not base:
        raise SystemExit("source empty")

    d0, d1 = date(2024, 1, 1), date(2024, 12, 31)
    span = (d1 - d0).days

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for i in range(a.n):
            proto = dict(rng.choice(base))
            proto["OrderID"] = f"ORD{i:08d}"
            proto["CustomerID"] = f"CUS{rng.randrange(a.customers):06d}"
            proto["OrderDate"] = (d0 + timedelta(days=rng.randrange(span + 1))).isoformat()
            for c in NUMERIC_JITTER:
                try:
                    v = float(proto[c])
                    proto[c] = f"{v * rng.uniform(0.95, 1.05):.2f}"
                except (ValueError, KeyError, TypeError):
                    pass
            for c in INT_COLS:
                try:
                    v = int(float(proto[c]))
                    proto[c] = str(max(0, v + rng.randint(-1, 1)))
                except (ValueError, KeyError, TypeError):
                    pass
            w.writerow(proto)
            if (i + 1) % 100_000 == 0:
                print(f"  {i+1:,} rows...")
    print(f"done: {a.n:,} rows -> {a.out}")


if __name__ == "__main__":
    main()
