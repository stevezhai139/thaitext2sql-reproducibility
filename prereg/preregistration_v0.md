# K3 Pre-registration (v0 — freeze พร้อม suite v1)

**Study:** Curriculum-aligned bilingual (TH/EN) Text-to-SQL readiness benchmark
**Frame:** benchmark/readiness study ของเครื่องมือ — ไม่ claim ผลการเรียนรู้; classroom = phase 2 (IRB-ready)
**Novelty positioning (เช็ค 5 ส.ค.):** ตระกูล single-language Text-to-SQL
ยัง active (Dialect2SQL/Darija 2025); ไทยยังว่าง → claim แบบ hedge
"to our knowledge, the first Thai Text-to-SQL evaluation suite" +
curriculum-tier + value-translation protocol; deep prior-art ซ้ำตอน W3

## Conditions
- **หลักการเลือกโมเดล (มติผู้เขียน 6 ส.ค.):** "นักศึกษาใช้ของฟรี" —
  ประเมินโมเดลที่อยู่หลัง free tier ของสามค่ายหลัก + open-weight ฟรี
- **Roster (5 ตัว; pin ชื่อ/เวอร์ชัน API จริง ณ วัน freeze):**
  (1) ChatGPT free ↔ **GPT mini-class** ผ่าน API (free tier ได้ตัวท็อป
  แบบจำกัดโควตาแล้วตกลง mini — เราประเมิน sustained free use;
  footnote ในตารางจับคู่)
  (2) Gemini free ↔ **Flash** ผ่าน API
  (3) Claude free ↔ **Sonnet-class** ผ่าน API (หมายเหตุ: Opus = paid
  tier เท่านั้น จึงไม่เข้าเกณฑ์ "free-tier model")
  (4) llama3.1:8b ผ่าน Ollama [open, generalist]
  (5) qwen2.5-coder:7b ผ่าน Ollama [open, code-specialized]
  + ตารางจับคู่ free-tier↔API-model ณ วัน freeze ใส่ในเปเปอร์ พร้อม
  limitation: web free tier อาจมี scaffolding ต่างจาก raw API
- **Languages:** EN / TH (ข้อเดียวกัน 60 คู่)
- **Prompt:** zero-shot เดียวมาตรฐาน: system = schema DDL + "answer with a single PostgreSQL query only" — ไม่มี few-shot, ไม่มี retry
- **Runs (นิยามบทบาทชัด — มติผู้เขียน 6 ส.ค.):** **5 ครั้ง**/ข้อ/โมเดล/
  ภาษา ที่ temperature 0 (Ollama: fixed seed) — มีไว้วัด stability
  (unanimity 5/5, flip rate, majority-execution ถ้าไม่เอกฉันท์) ไม่ใช่
  สร้าง CI; **CI ทั้งหมดมาจากการสุ่มระดับข้อ (n=60)**
- **Efficiency runs (RQ3):** warm-up 2 + วัด 10 รอบ/query → median, p95

## Translation protocol (กำหนดโดย instructor, 5 ส.ค.)
- คำ/แนวคิดสามัญที่มีภาษาไทยธรรมชาติ → แปลไทย (รวมถึง data values
  ที่เป็นคำสามัญ เช่น 'Widowed' → "หม้าย")
- ชื่อเฉพาะ, ชื่อตาราง/คอลัมน์, data values ที่เป็น named entity
  (เช่น 'Federalist', 'Tokyo', 'Credit Card') → ทับศัพท์/คงอังกฤษ
- ความกำกวมต้องเท่ากันสองภาษา (เช่น ช่วงปี ระบุ explicit ทั้งคู่)
- ตอนวิเคราะห์: ข้อที่ data value ถูกแปล จะถูก tag `value_translated`
  (derive อัตโนมัติ) เพื่อแยกวัด value-literal mapping effect

## Metrics
1. **Execution accuracy**: รัน SQL ที่ได้บน PostgreSQL — ถูก iff result set ตรง gold (unordered multiset เว้นข้อที่มี ORDER BY)
2. **Cross-lingual gap**: acc(EN) − acc(TH) รายข้อ (paired)
3. **Efficiency (ข้อ eff=yes, 12 ข้อ)**: รันบน Ecommerce-1M มี/ไม่มี index — report latency distribution (median, p95) + ใช้ index หรือไม่ (EXPLAIN) — **ไม่ใช้ Cohen's d กับ benchmark กำหนดแน่**
4. **Error taxonomy**: โค้ดผิดพลาดตามรายการปิด (wrong-join / missing-group / hallucinated-column / wrong-filter / syntax / other) — ผู้โค้ดสองรอบห่างกัน ≥3 วัน (intra-rater)

## Statistics (กำหนดก่อนเห็นผล)
- Accuracy: Wilson 95% CI ต่อ model×language (n=60); ระดับ tier (n=15)
  รายงานเชิงพรรณนาพร้อม CI (ประกาศ power ตรงๆ ว่ากว้าง)
- TH vs EN: **McNemar** paired รายข้อ ต่อโมเดล, α = 0.05 +
  **Holm correction ข้าม 5 โมเดล** + รายงาน Δaccuracy พร้อม
  Newcombe paired CI (ไม่รายงาน p เปล่าๆ)
- Stability: unanimity rate (3/3 ตรงกัน) ต่อโมเดล; ถ้า <100% ใช้
  majority-execution + รายงาน flip rate
- Latency: median + p95 (ไม่ใช้ mean±SD, ไม่ใช้ Cohen's d กับ
  benchmark กำหนดแน่)
- ไม่มี hypothesis เชิงทิศ — เป็น estimation study

## Exclusion / integrity
- Parse-fail (ไม่ใช่ SQL เดียว) = ผิด (นับ, ไม่ตัดทิ้ง) — รายงาน parse rate แยก
- ห้ามแก้ suite หลัง freeze; ทุกตัวเลขในเปเปอร์ = run-of-record บนเครื่องผู้เขียน; script + suite ขึ้น repo สาธารณะ
- Gold SQL ผิดที่พบหลังรัน: แก้ได้ แต่บันทึกเป็น amendment พร้อมเหตุผล (ไม่เงียบ)

**Freeze เมื่อ:** suite v1 อนุมัติ + รายชื่อโมเดล pin แล้ว → คัดลอกไฟล์นี้เป็น `preregistration_FROZEN.md` ก่อนรันครั้งแรก
