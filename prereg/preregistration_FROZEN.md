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

---
## FREEZE STAMP
- **Frozen: 6 Aug 2026** — suite = k3_suite_v1.tsv (60 ข้อ, อนุมัติโดยผู้เขียน; changelog v0→v1 บันทึกแยก)
- Model classes ล็อกตามด้านบน; **ชื่อรุ่น API เป๊ะๆ + Ollama digest จะถูกบันทึกอัตโนมัติโดย harness ในการรันครั้งแรก** (run-of-record log echo model string) และห้ามสลับรุ่นหลังจากนั้น — วิธีนี้แม่นกว่า pin ด้วยมือวันนี้
- การแก้ไขใดๆ หลังจุดนี้ = amendment พร้อมเหตุผลบันทึกเท่านั้น

## AMENDMENT-1 (อนุมัติโดยผู้เขียน 6 ส.ค. — ก่อน first LLM run)
- Suite ฉบับใช้จริง = **k3_suite_v1.1.tsv** (11 ข้อแก้: Q24/Q40 คำตอบว่างบนข้อมูลจริง + tiebreak determinism 9 ข้อ — รายละเอียดใน suite/CHANGELOG)
- เหตุผล: พบจาก gold validation + grader self-test; ยังไม่มีการเรียก LLM ใดๆ เกิดขึ้นก่อน amendment นี้

---
## AMENDMENT-2 (7 ส.ค. 2026 — ก่อนการรันเก็บจริง)
- แก้ข้อความโจทย์ 17 ข้อ (EN+TH) เพื่อขจัด projection ambiguity ที่ smoke run พิสูจน์
  (Q13-Q15, Q20, Q23, Q29, Q38, Q40, Q44, Q46, Q47, Q49, Q50, Q53-Q56); gold SQL ไม่เปลี่ยน;
  suite = k3_suite_v1.2.tsv; ลบ 7 records ที่เก็บด้วยโจทย์เก่า (log ใน CHANGELOG)
- ธรรมเนียมการตีความที่ประกาศเพิ่ม:
  (a) "For each X, show Y" ⇒ ผลลัพธ์รวมคอลัมน์ X ด้วย
  (b) "List presidents…" บน schema P ⇒ PresidentName คอลัมน์เดียว
- เอกสารเต็ม: suite/AMENDMENT2_PROPOSAL.md

## AMENDMENT-3 (7 ส.ค. 2026 — config การสุ่มรายโมเดล)
- claude-sonnet-5: API ปฏิเสธ `temperature` (deprecated) → รันด้วย default ของผู้ให้บริการ
  ผลพลอยได้: unanimity 5 รอบของ Claude เป็นการวัด stability ภายใต้การสุ่มจริง
  (ต่างจาก ollama ที่ temp 0 + seed 42 = deterministic โดยพิสูจน์แล้ว 60/60 ทุกช่อง)
- ตารางท้ายว่าแต่ละโมเดลรันด้วย config ใด จะรายงานใน paper (sampling-config table)

## AMENDMENT-4 (7 ส.ค. 2026 — เพิ่มโมเดลที่ 6: Typhoon2 8B, ก่อนเริ่มวิเคราะห์ยืนยัน)
- เพิ่ม typhoon2-8b = scb10x/llama3.1-typhoon2-8b-instruct (GGUF Q4_K_M ผ่าน Ollama)
- เหตุผล: matched-pair กับ llama31-8b (ฐานเดียวกัน ขนาดเดียวกัน quant ระดับเดียวกัน
  ต่างเฉพาะ Thai adaptation) → ตอบ RQ ข้ามภาษาโดยควบคุมตัวแปร และกันคำถาม
  reviewer เวทีไทยเรื่องโมเดลไทย; capped ที่ 1 ตัว (DeepSeek/Doubao/SEA-LION → Future Work)
- roster สุดท้าย = 6 โมเดล; ตาราง/สถิติทุกชุดขยายตาม (Holm ปรับตามจำนวนคู่เทียบใหม่)

### AMENDMENT-4 addendum — artifact ที่ใช้จริง (7 ส.ค.)
- GGUF ทางการของ llama3.1-typhoon2-8b ถูกถอดจาก HF (org scb10x → typhoon-ai แล้วเหลือรุ่นอื่น)
- ใช้ community quant: mradermacher/llama3.1-typhoon2-8b-instruct-GGUF
  ไฟล์ llama3.1-typhoon2-8b-instruct.Q4_K_M.gguf (4.6GB) — weights ต้นทางคือ
  typhoon-ai/llama3.1-typhoon2-8b-instruct อย่างเป็นทางการ; quant Q4_K_M ระดับเดียวกับ
  llama3.1:8b ของ ollama library → matched-pair ยังถูกต้อง (จะระบุใน paper ว่าเป็น community quant)
- นำเข้าเป็น ollama model ชื่อ typhoon2-8b (Modelfile: FROM <gguf>; chat template จาก GGUF metadata)

## AMENDMENT-5 (7 ส.ค. 2026 — ก่อนวิเคราะห์ RQ3; ข้อวิจารณ์โดยผู้เขียน)
- เปลี่ยน operationalization ของ RQ3: จากจับเวลา wall-clock (warm-cache, เครื่องเดียว,
  confound สูง และงานนี้ไม่ได้ claim performance study) → **วัดคุณภาพ query plan**
  ด้วย EXPLAIN (FORMAT JSON) ซึ่งไม่ execute จริง จึงไม่มีประเด็น cache และ
  deterministic ต่อ (PG version, data, ANALYZE, config) ที่ repo ตรึงครบ
- ตัวชี้วัด: scan types, uses_index, planner total cost, **cost ratio เทียบ gold**,
  และ index-responsiveness (เทียบสองเฟส indexed/noindex)
- efficiency.py (จับเวลา) ถูกถอดออก แทนที่ด้วย plan_quality.py; ข้อมูลเวลาที่วัดไป
  บางส่วนก่อน amendment จะไม่ถูกใช้ใน paper

## AMENDMENT-6 (19 ต.ค. 2026 — เปลี่ยนเลขของการแก้กฎ value grounding วันที่ 13 ส.ค. 2026; ไม่เปลี่ยนเนื้อหา)
- **เอกสารที่เปลี่ยนเลข:** `suite/AMENDMENT3_VG_RULE.md` (commit e0d757e, 13 ส.ค. 2026 19:05:26 +0700;
  sha256 `256dc532f5ed698e08360c91b56742f629f7010b8e0c922b7a8493e9a21a7d6f`) นับเป็น **AMENDMENT-6** ตั้งแต่ amendment นี้
  - บรรทัด 3 ของไฟล์นี้มีชื่อบุคคล สำเนาบน mirror นิรนามของ artifact จึง redact บรรทัดนั้น และ sha256 ของสำเนาบน mirror ต่างจากค่าข้างต้น
    ค่าที่ pin หมายถึงไฟล์ใน repository ที่ไม่ redact
- **เนื้อหาไม่เปลี่ยน:** ไฟล์คงชื่อและคงทุก byte (sha256 ข้างต้น) หัวเรื่อง "Amendment 3" ในไฟล์ให้อ่านว่า AMENDMENT-6
  การอ้างถึงในเอกสารใหม่ทุกฉบับ (เล่ม, Response, artifact) ใช้ชื่อ AMENDMENT-6
- **เหตุผลของการเปลี่ยนเลข**
  1. ชื่อชนกับ AMENDMENT-3 ในไฟล์นี้ (7 ส.ค. 2026 — config การสุ่มของ claude-sonnet-5) ผู้อ่านจึงแยกสองฉบับไม่ได้
  2. การแก้ครั้งนั้นไม่ได้ถูกบันทึกในไฟล์นี้ index ของ amendment จึงขาดไปหนึ่งฉบับ และเล่มที่ส่ง (16 ส.ค. 2026)
     เขียนว่า "five dated amendments" ทั้งที่ ณ วันส่งมีหกฉบับ
  3. ตามลำดับเวลา การแก้นี้เป็นฉบับที่หก (หลัง AMENDMENT-5 ซึ่ง commit 7 ส.ค. 2026 20:37:37 ใน ca42208)
- **สถานะของการแก้ที่ถูกเปลี่ยนเลข (บันทึกตามจริง):** เป็นการแก้กฎหลังรันและหลังเห็นผล (post-hoc) แต่ก่อนส่งเล่ม
  ผู้เขียนตรวจพบระหว่างอ่าน annotation sheet ของ C-2 (Q06 ถูกนับเป็น value grounding เพราะ wildcard)
  แก้ด้วยกฎทั่วไปสองข้อที่ใช้กับทุกข้อ และบันทึกตัวเลขเก่า→ใหม่ไว้ในไฟล์ การเปลี่ยนเลขครั้งนี้ไม่เปลี่ยนสถานะดังกล่าว
  - ทิศของผล: headline ลดลง ("roughly half" เป็น "up to 40%") และส่วนแบ่งความผิดภาษาไทยบน VG ของ frontier ลดลงทุกโมเดล
    (8/15, 7/15, 4/10 เป็น 6/15, 5/15, 2/10 ตามไฟล์)
- **สรุปเนื้อหาสำหรับ index (ข้อความเต็มอยู่ในไฟล์):**
  - กฎ: (a) ตัด wildcard `%`/`_` ออกจาก literal ก่อนตรวจว่าปรากฏในโจทย์ไทยหรือไม่
    (b) ไม่นับ literal ที่เป็น argument หน่วยเวลาของ DATE_TRUNC/EXTRACT/DATE_PART
  - ตัว implement หลัก: `harness/vg_rule.py` ซึ่ง analyze.py, analyze_typhoon.py และ make_annotation_sheet.py import ใช้
  - ผล: ชุด value grounding (VG) จาก 13 เหลือ 10 ข้อ (Q06, Q39, Q54 ออก); คำนวณตัวเลขที่ขึ้นกับชุดนี้ใหม่ทั้งหมด
    และ headline ใน abstract เปลี่ยนจาก "roughly half" เป็น "up to 40%"
- **ความสัมพันธ์กับ amendment ถัดไป:** ชุด VG หลักยังเป็น VG10 ตามกฎของ amendment นี้ (มติผู้เขียน 13 ต.ค. 2026)
  เงื่อนไข relevance ของ literal (VG9) ใช้เป็น sensitivity ใน AMENDMENT-7 Part B2.1 และไม่ใช่การแก้ AMENDMENT-6
- **ผลต่อเล่ม:** จำนวน amendment ที่อ้างในเล่มนับตาม index นี้ (AMENDMENT-1 ถึง 6 ก่อนส่ง; 7, 8 และ 9 หลัง review
  โดยกฎข้อมูล 'None' → NULL และ answer key v1.3/v1.3n เป็นส่วนหนึ่งของ AMENDMENT-7) ประโยค "five dated amendments" ต้องแก้

## AMENDMENT-7 (19 ต.ค. 2026 — หลัง review KST 2027; ก่อน re-grade ทางการ, ก่อนวิเคราะห์ log เดิม และก่อน model call แรกของแขน values)

**ขอบเขต:** amendment นี้มีหกส่วน
- Part 0 ข้อมูลหลักของเล่มฉบับแก้ (มติ D10)
- กฎข้อมูล: การเข้ารหัสค่าที่ไม่มีอยู่ 'None' → NULL (ฐาน k3n)
- Part A แขน values (เงื่อนไขใหม่ที่ต้องเรียกโมเดล)
- Part B การวิเคราะห์เชิงพรรณนา (บนแขน base ของรอบ ต.ค. เป็นผลหลัก และบน log ส.ค. เป็นผลรอง)
- Part C answer key v1.3 และ v1.3n (re-grade log ส.ค. ไม่เรียกโมเดล)
- Part D รายการ deviation ที่ทราบแล้ว

ลำดับการมีผล: Part 0 → กฎข้อมูล (k3n) → Part C → Part A และ Part B
Part C กำหนด key ที่ Part A, Part B, AMENDMENT-8 และ AMENDMENT-9 ใช้ บนฐาน k3n ตามกฎข้อมูล

**สิ่งที่ไม่เปลี่ยน**
- `results/results.jsonl` (run-of-record ของฉบับที่ส่ง; ดู Part 0) ไม่แก้ทุก byte
- ข้อความโจทย์ 60 ข้อทั้ง EN และ TH เหมือน suite v1.2 ทุกตัวอักษร ยกเว้น Q27 ของ suite รอบ ต.ค. ซึ่งซ่อมตามมติ D11 (Part C3);
  suite ที่ใช้ re-grade log ส.ค. คงข้อความเดิมทั้ง 60 ข้อ
- ข้อมูลในฐาน k3 (ไม่ถูกแก้; ฐานของ record เปลี่ยนเป็น k3n ตามกฎข้อมูลของ amendment นี้ และผลบน k3 เป็น sensitivity)
- สถิติหลักตามบรรทัด 47–57 และ AMENDMENT-4 (Wilson 95%, exact McNemar, Holm ข้าม 6 โมเดล)
- suite v1.2 และ `results/graded.csv` เก็บไว้เป็นฉบับ preregistered และรายงานคู่กัน (Part C5)

**ที่มา:** decision ของ KST 2027 ลงวันที่ 10 ต.ค. 2026 (accepted with major revision), มติผู้เขียน 12 ต.ค. 2026
ข้อ D1, D3, D6, D7, D8 และ D9, มติ 13 ต.ค. 2026 (การเข้ารหัส 'None' → NULL ทาง A, ชุด VG10, การ grade หลาย instance MI-1b,
ชุดขยาย 40 ข้อ และลำดับ amendment) และมติ D10 และ D11 วันที่ 14 ต.ค. 2026 (ข้อมูลหลักของเล่มมาจากรอบ ต.ค.;
Q27 ซ่อมสำหรับรอบ ต.ค.) (บันทึกใน `KST_REVISION_2026-10-12.md`)

### Part 0 — ข้อมูลหลักของเล่มฉบับแก้ (มติ D10 และ D11 ของผู้เขียน 14 ต.ค. 2026; มีผลก่อนทุกส่วน)
1. **รอบ ต.ค. เป็น experiment ใหม่ด้วยวิธีเดิม** เพื่อตอบ reviewer เรื่องขนาดและการตีความ ตัวเลขหลักทั้งหมดของเล่มฉบับแก้มาจากรอบ ต.ค.
   ได้แก่ 6 โมเดลบนฐาน k3n ด้วย answer key v1.3n: แขน base (วิธีเดิม: DDL อย่างเดียว 60 ข้อ โดย Q27 เป็นฉบับซ่อมตามข้อ 11),
   แขน values (Part A) และชุดขยาย 40 ข้อ (AMENDMENT-9; แขน base)
2. **run-of-record:** run-of-record ของเล่มฉบับแก้คือรอบ ต.ค. บนเครื่องของผู้เขียน (`results/rc1/` และ `results/ext/`)
   - `results/results.jsonl` ยังเป็น run-of-record ของฉบับที่ส่ง และไม่ถูกแก้ทุก byte
   - บรรทัด 61 ของ prereg ("ทุกตัวเลขในเปเปอร์ = run-of-record บนเครื่องผู้เขียน") อ่านตามข้อนี้ และบันทึกใน Part D (D-6)
3. **log ส.ค.:** regrade บน k3n ด้วย v1.3n (Q27 เดิมยังเป็น excluded ตาม D3; n=59) เพื่อการเทียบความสอดคล้องสั้น ๆ ในเล่ม
   และรายละเอียดอยู่ใน artifact
   - เนื้อหาที่ตรึง (`harness/consistency_aug_oct.py`): ต่อโมเดล × ภาษา จำนวนข้อที่ถูกโดย majority ในรอบ ส.ค. และรอบ ต.ค.
     และจำนวนข้อที่คำตัดสินต่างกันแยกทิศ บน 59 ข้อที่ถามเหมือนกันในสองรอบ อยู่ในเล่ม;
     อัตรา unanimity ของทั้งสองรอบและรายการรายข้ออยู่ใน artifact
   - Q27 ไม่อยู่ในการเทียบ เพราะสองรอบถามคนละโจทย์ (ข้อ 11) และไม่มีการเทียบบน 60 ข้อ
   - เป็นการเทียบเชิงพรรณนา ไม่มีการทดสอบทางสถิติ ไม่ใช่เป้า parity และไม่รวมข้อมูลสองรอบ; ผลของโมเดล local ติดป้าย exploratory
4. **ตารางของเล่ม:** Part B และตารางของเล่ม (accuracy และ tiers, EN–TH exact McNemar + Holm, Table IV พร้อม label ของ phi,
   taxonomy และ B6, silent split, B3, B4, B5/RQ3/Q51 และ positional) คำนวณบนแขน base ของรอบ ต.ค. 60 ข้อเป็นผลหลัก
   ด้วยสคริปต์ชุดเดียวกันที่รับ `--arm base` และ suite ของรอบ ต.ค.; ชุดเดียวกันบน log ส.ค. (59 ข้อ และ n=60 เป็น sensitivity
   ของ log ส.ค.) เป็นผลรอง
5. **Ollama:** ไม่มี Ollama parity gate; digest และ metadata ของรอบ ต.ค. บันทึกใน `results/rc1/provenance_gate1a.json`,
   `provenance_before.json` และ `provenance_after.json` และ runner ล็อก digest ก่อน local call แรก
   การไม่ได้บันทึก digest ในเดือน ส.ค. (prereg บรรทัด 69) เปิดเผยสำหรับข้อมูล ส.ค. เท่านั้น (D-7)
6. **ลำดับการถามของแขน base ในโมเดล local ต่างจาก ส.ค.:** ใน ส.ค. llama31-8b และ qwen25-coder-7b ถูกถามแบบ item-major
   (5 run ของข้อเดียวติดกัน) รอบ ต.ค. ถามแบบ run-major และสลับกับแขน values จึงเปลี่ยนสถานะ prefix cache ของ Ollama
   (ผู้ร่างพบ 6 cell ใน log ส.ค. ที่ run 1 ต่างจาก run 2–5) prompt และ payload ของแขน base เหมือน ส.ค. ทุก byte
   ยกเว้น call ของ Q27 ตามข้อ 11 (ตรวจด้วย `harness/check_prompts_rc1.py`) แต่ลำดับการเรียกไม่เหมือนเดิม (D-8)
7. **ความพร้อมกันของคู่ (concurrent control):** นิยาม การรายงาน และ sensitivity ตาม A4
8. **ลำดับการรันในแต่ละ terminal:** core ของทุกโมเดลก่อน แล้วจึงชุดขยายตามลำดับโมเดลเดียวกัน (A4)
9. **ความต่างนอก request body:** key ของ Gemini ย้ายจาก URL ไป header (commit c698547) และ User-Agent ของ urllib
   ต่างตาม version ของ Python (ส.ค.: Python 3.10 อนุมานจาก bytecode cache; ต.ค.: ตาม `provenance_gate1a.json`)
   request body ของแขน base ตรงกับ ส.ค. ทุก byte ยกเว้น call ของ Q27 (ข้อ 11; ทดสอบ: call ของแขน base 3,540/3,600 ตรงกับ ส.ค.
   และอีก 60 call เป็นของ Q27) และ User-Agent ของรอบ ต.ค. เท่ากันทั้งสองแขน
10. **echo ไม่ตรง:** การหยุดแบบ MODEL SWAP ของ A5 ข้อ 2 ครอบตารางหลักแขน base ของโมเดลนั้นด้วย
    ทางต่อไประบุใน addendum ลงวันที่ตาม A5 ข้อ 2 ก่อน call ถัดไป และการเทียบ ส.ค.–ต.ค. ของโมเดลนั้นติดป้ายว่าเปลี่ยนรุ่น
11. **Q27 ซ่อมสำหรับรอบ ต.ค. (มติ D11):** รอบ ต.ค. ถาม Q27 ฉบับซ่อม (ข้อความ EN และ TH และ gold ใน Part C3) แทนการตัดข้อ
    - suite ของรอบ ต.ค. คือ `suite/k3n_suite_v1.3n_oct.tsv` ซึ่งแยกจาก suite ของ ส.ค. (`suite/k3n_suite_v1.3n.tsv` ไม่ถูกแก้)
      และต่างจาก suite ของ ส.ค. เฉพาะบรรทัดของ Q27
    - core ของรอบ ต.ค. grade ครบ 60 ข้อ (100 ข้อเมื่อรวมชุดขยาย) และ n=60 เป็นผลหลักของรอบ ต.ค.
    - re-grade log ส.ค. คง Q27 เดิมเป็น excluded (D3; n=59 และรายงาน n=60 เป็น sensitivity ของ log ส.ค.)
    - การเทียบ ส.ค.–ต.ค. (ข้อ 3) และ drift (A6 ข้อ 7) ใช้ 59 ข้อที่ถามเหมือนกันในสองรอบ
    - ข้อยกเว้นเดียวของการตรวจ byte ของ prompt คือ call ของแขน base ของ Q27 (6 โมเดล × 2 ภาษา × 5 run = 60 call)
      ซึ่งประกาศในค่าคงที่เดียว `D11_PROMPT_EXCEPTION` ของ `harness/check_prompts_rc1.py`
    - RQ3 ของรอบ ต.ค. ใช้ gold ฉบับซ่อมของ Q27 และ RQ3 ของ log ส.ค. ไม่เปลี่ยน; Q27 มี eff = no จึงไม่อยู่ในชุดข้อของ RQ3
      ทั้งสองรอบ (ทดสอบ)
    - ข้อความ TH ของ Q27 ฉบับซ่อมเป็นฉบับที่ผู้เขียนเขียนและเป็นฉบับสุดท้าย
12. **เวลาที่ตัดสิน:** ผู้เขียนตัดสิน D10 และ D11 วันที่ 14 ต.ค. 2026 ก่อน model call แรกของรอบ ต.ค. และก่อน regrade ทางการ
    ข้อมูลที่ผู้ร่างเห็นก่อนเขียน Part 0 อยู่ในหัวข้อถัดไป

### ข้อมูลที่ผู้ร่างเห็นก่อนเขียน (เปิดเผย; ใช้กับทุก Part)
- **ผู้ร่าง:** ผู้ช่วย AI เป็นผู้ร่าง ผู้เขียนอ่าน แก้ และอนุมัติ (ต้องระบุใน AI-use disclosure ของเล่ม)
- **ผลทางการของ run-of-record (key v1.2):** ผู้ร่างเห็นทั้งระดับ run และระดับ item รวมทั้ง SQL ของ run ที่ผิด
- **ตัวเลขทดสอบที่ผู้ร่างเห็น (ทดสอบ)**
  - การแยก silent ภายใต้ key v1.2 และ v1.3 (Part B1)
  - การนับ VG ของ gpt-5.4-mini ภายใต้ key v1.2 สี่แบบ ได้ 3/15, 4/15, 5/15 และ 6/15 และการนับแบบ set-based ภายใต้ key v1.3 (Part B2.5)
  - ผลระดับ item และการเปลี่ยนระดับ run/cell ของ key v1.3 รายข้อ (Part C7)
  - gap นอก VG ภายใต้ v1.2 (Part B3)
  - ความแปรปรวนของ SQL text (Part B4)
  - ขนาดและ sha256 ของ value block (Part A2)
  - ตัวเลขทดสอบบนฐาน k3n: การเปลี่ยนระดับ item ของ log ส.ค. 46 cells จากผิดเป็นถูกและ 2 cells จากถูกเป็นผิด (แทน 47 และ 0 บน k3),
    silent-non-empty 102 และ silent-empty 36 ของ frontier (แทน 98 และ 40), p_Holm ของ EN−TH ของ llama3.1:8b .0647 → .1758 (n=59)
    และ .0369 → .1064 (n=60), และ p ของ typhoon2-8b เทียบ llama3.1:8b ใน EN .0044 → .0127
  - การทดสอบ Ollama วันที่ 13 ต.ค. 2026 ที่ได้ raw output ตรงกับ log ส.ค. 18/18 (ผู้ร่างเห็น แต่ไม่ใช้เป็นหลักฐานหรือ gate ตาม Part 0 ข้อ 5)
  - latency ของ log ส.ค. (สูงสุด 42.9 วินาที) ที่ใช้กำหนดขอบ 130 วินาทีของความพร้อมกันของคู่ (A4)
  - metadata ของผู้ให้บริการและการวัด token ด้วยการเรียกจริงค่ายละ 3 ครั้ง (13 ต.ค. 2026; ค่าใช้จ่ายต่ำกว่า US$0.01)
  - การจำลองข้อ PK1 ด้วยคำตอบ 45 แบบบน instance ที่จำลองด้วย CTE (AMENDMENT-9)
  - ผลของ gold ของ Q27 ฉบับซ่อมและของคำตอบที่ผู้ร่างเขียนเพื่อตรวจถ้อยคำบน k3n (ทดสอบ; Part C3) ไม่มีคำตอบของโมเดลต่อโจทย์ฉบับซ่อม
  - ระหว่างแก้ตัวจำแนก B2.3 (14 ต.ค. 2026) ผู้ช่วยรันสคริปต์ตรวจ `scan.py` ที่อ่าน record
    ของข้อ VG ใน log ส.ค. เฉพาะ qid, lang, sql และ parse_ok (ไม่อ่านผลการ grade) แล้วพิมพ์จำนวน record ที่คลาสของตัวจำแนก
    ฉบับก่อนแก้กับฉบับหลังแก้ต่างกัน แยกตามภาษาและคู่คลาส
    - ตัวเลขนี้ไม่ใช่จำนวน GF เพราะนับทุก run ไม่แยก run ที่ผิด และไม่มีไฟล์บันทึกว่ารันกี่ครั้งและพิมพ์ค่าใด
    - สคริปต์และตัวจำแนกสองฉบับที่เทียบเก็บไว้เป็นหลักฐาน (sha256 ใน FREEZE STAMP ของ amendment นี้) และแนบใน artifact
  - dry-run ของ Gate 0 (14 ต.ค. 2026; ทดสอบ) รันขั้นของ Gate 2 (regrade log ส.ค. บนสำเนา k3n จนถึงการสุ่มข้อและการสร้าง cells
    ของ AMENDMENT-8) และขั้น parity ของ Gate 1a กับ log ส.ค. และเก็บผลแบบปิดตัวเลข (ตัวเลขทุกตัวแทนด้วย #) โดยไม่แสดง
    - ผู้ร่างเห็นเฉพาะผลเชิงโครงสร้าง ได้แก่ 3,600/3,600 ของ parity, จำนวนข้อ 18 ข้อของ chat check และ 28 cells ต่อ app
      ไม่เห็นรายการข้อ ตาราง accuracy หรือจำนวน GF ของ regrade
    - ข้อยกเว้นหนึ่งจุด: ขั้นการเทียบ ส.ค.–ต.ค. ของ dry-run (บนข้อมูลรอบ ต.ค. แบบสังเคราะห์) พิมพ์จำนวนข้อที่ถูกของ log ส.ค.
      ที่ n=60 ของสาม cell (llama31-8b ภาษาไทย และ typhoon2-8b ภาษาอังกฤษและภาษาไทย) ก่อนผลถูกปิดตัวเลข
- **สิ่งที่ผู้ร่างยังไม่เห็น**
  - ผลใดๆ ของแขน values (ยังไม่มีการเรียกโมเดล)
  - จำนวน GF ภายใต้ key v1.3 (ตั้งใจไม่คำนวณก่อนตรึงนิยาม)
  - ผลจาก chat app
- **ตัวเลขทดสอบที่ผู้เขียนเข้าถึงได้:** memo `kst_rev/wf_d7/D7_GOLD_DECISION_DRAFT.md` ซึ่งมีผลรายโมเดลภายใต้ key v1.3
  รวมผลของชุด VG ทั้งสองแบบ อยู่ในโฟลเดอร์โครงการตั้งแต่ 12 ต.ค. 2026 แต่ผู้เขียนไม่ได้อ่านตารางผลรายโมเดลใน memo ก่อนอนุมัติ amendment นี้
  ตัวเลขทดสอบที่ผู้เขียนเห็นระหว่างการทำงานมีบันทึกไว้ใน master log ของการแก้ไข (`KST_REVISION_2026-10-12.md`)
- **ขอบเขตของการปิดตา**
  - re-grade เป็น deterministic และสำเนา scratch ให้ผลแบบ legacy ตรง `results/graded.csv` ครบ 3,600 แถว (ทดสอบ)
  - ผลทางการของ Part C และส่วนใหญ่ของ Part B จึงคาดว่าจะเท่ากับตัวเลขทดสอบที่ผู้ร่างเห็นแล้ว (ผู้เขียนเห็นเฉพาะตัวเลขทดสอบบางตัวที่บันทึกไว้ใน master log)
  - การ commit ก่อน re-grade ทางการจึงตรึงนิยามและขั้นตอน แต่ไม่ได้ทำให้การตัดสินใจใน Part B และ Part C ปิดตาจากผล
  - ส่วนที่ปิดตาจริงคือผลของแขน values (Part A), จำนวน GF ภายใต้ key v1.3 และผลของ chat check (AMENDMENT-8)
- **ตัวเลขทางการ:** ตัวเลขทุกตัวที่จะลงเล่มมาจากการรันของผู้เขียนเท่านั้น

---

### Part A — แขน values (มติ D1; ตอบ R1-W1 และ R1-RC1)

**A1 เหตุผล**
- Reviewer 1 ชี้ว่า prompt ของ run-of-record ให้โมเดลเห็นเฉพาะ DDL
  - การคัดลอกคำไทย (เช่น หม้าย) ลงใน predicate จึงอาจเป็นการเดาที่สมเหตุสมผลจากข้อมูลที่ได้รับ
  - ตัวเลข "up to 40%" อาจสะท้อนโจทย์ที่ให้ข้อมูลไม่พอ (underspecified task) มากกว่าขีดจำกัดของโมเดล
- Reviewer ขอเงื่อนไขที่ prompt มี sample rows หรือ distinct values ของแต่ละคอลัมน์
  และให้รายงานว่า Thai gap และ value-grounding errors เหลือเท่าใด
- **ที่เลือก:** Part A เพิ่มแขน values (V) แล้วเทียบกับแขน base (B) ที่รันพร้อมกันในช่วงเดียวกัน
- **เหตุผลที่เลือก distinct values แทน sample rows**
  1. distinct values ไม่ขึ้นกับลำดับแถว ส่วน sample rows ครอบ literal เป้าหมายได้เพราะลำดับแถวบังเอิญเอื้อ
     (ทดสอบ: k=3 ครอบ 9/10 ข้อ และ 'Female' ของ Q15 ไม่ปรากฏจนถึง k=10)
  2. distinct values ตรงกับนิสัย `SELECT DISTINCT` ก่อน `WHERE` ที่เล่มเสนอ
     แขนนี้จึงทดสอบข้อเสนอดังกล่าวในระดับเครื่องมือเท่านั้น ไม่ใช่ระดับนักศึกษา
- sample rows ไม่ทำในรอบนี้

**A2 การสร้าง prompt (ตรึง)**
- **แขน B:**
  - `system = SYSTEM.format(ddl=DDL_<schema>)` และ `user = question_<lang>`
  - ค่าคงที่ SYSTEM, DDL_P และ DDL_E มาจาก `harness/runner.py` โดยไม่แก้
  - prompt ของแขน B จึงเหมือน run-of-record ทุก byte ยกเว้นข้อความผู้ใช้ของ Q27 ซึ่งเป็นโจทย์ฉบับซ่อมตามมติ D11
    (ข้อยกเว้นเดียว ประกาศในค่าคงที่ `D11_PROMPT_EXCEPTION` และตรวจด้วย `harness/check_prompts_rc1.py`; Part 0 ข้อ 11)
- **แขน V:**
  - `system = SYSTEM.format(ddl=DDL_<schema>) + "\n\n" + block[<schema>]` และ user เหมือนแขน B
  - ข้อความคำสั่งไม่เปลี่ยน prompt ของแขน B จึงเป็น prefix ของแขน V
- **value block:** บรรทัดแรกเป็นข้อความหัวตามนี้ทุกตัวอักษร
  `Stored values of the text columns (SELECT DISTINCT; a column with more than 25 distinct values shows 3 examples):`
  - **ขอบเขต:** หนึ่งบรรทัดต่อคอลัมน์ TEXT ทุกคอลัมน์ใน DDL ที่โมเดลเห็น
    เรียงตามลำดับใน DDL (ตารางตามลำดับ `CREATE TABLE` แล้วคอลัมน์ตามลำดับที่ประกาศ) คั่นบรรทัดด้วย `\n`
  - **n:** จำนวนค่าไม่ซ้ำรวม NULL คือจำนวนแถวที่ได้จาก `SELECT DISTINCT <col> FROM <table>`
  - **n ≤ 25:** `Table.Column: v1, v2, …` แสดงทุกค่า
    - เรียงค่าที่ไม่ใช่ NULL ตาม Unicode code point ด้วย Python `sorted` ไม่ใช้ collation ของฐานข้อมูล
    - ถ้ามี NULL ให้ต่อท้ายด้วยคำว่า `NULL`
  - **n > 25:** `Table.Column: <n> distinct values, e.g. v1, v2, v3` คือ 3 ค่าแรกที่ไม่ใช่ NULL ตาม code point
  - **รูปแบบค่า:** แสดงเป็น SQL literal `'…'` (single quote ภายในค่าเขียนเป็น `''`) และคั่นด้วย `", "`
  - **ข้อห้าม:** ไม่มีคำแปลไทยของค่าใดๆ โจทย์ยังคงเป็นการโยงคำไทย (หม้าย) ไปยังค่าอังกฤษ (`'Widowed'`)
    เพียงแต่รายการค่าที่เก็บจริง (stored values) มองเห็นได้
- **ผู้สร้าง block:** `harness/make_value_hints.py`
  - อ่าน PostgreSQL ฐาน k3n แบบ read-only ครั้งเดียว (`--expect-db k3n` ตรวจว่าไม่มีสตริง 'None' และ NULL = 1/4/1 ใน SpouseName,
    VicePresidentName และ RunnerUp) แล้วเขียน `suite/value_hints_v1.json` (version 'v1', `source_db: "k3n"`, ไม่มี timestamp, เขียนแบบ deterministic)
  - ปฏิเสธการเขียนทับไฟล์ที่มีอยู่แล้ว
  - runner อ่านไฟล์นี้และตรวจ sha256 ให้ตรงกับ FREEZE STAMP ก่อนเรียกโมเดล runner ไม่ query ฐานข้อมูลเอง
- **ค่าที่คาด (ทดสอบ):** คำนวณบนสำเนา scratch ของ k3 (12 ต.ค.) และของ k3n (13–14 ต.ค.) จาก CSV ชุดเดียวกัน; block เท่ากันทุก byte บนสองฐาน
  - block P ยาว 1,381 ตัวอักษร sha256 `32e422929b84fa12ed45d0752e45f25c8ebaa2ae077adb17d95e8f2e7fb61713`
  - block E ยาว 1,723 ตัวอักษร sha256 `5a9fb96ffd03bf08cb723f5f4f1f87161aaf642f83faf015bab6852f3255987c`
  - ทั้งสองค่าตรงกับ preview ของร่าง 12 ต.ค.; sha256 ของไฟล์ต่างจากฉบับ k3 เพราะมี field `source_db` และไม่มี timestamp
  - FREEZE STAMP บันทึกทั้ง sha256 ของไฟล์และ sha256 ของ block ต่อ schema
  - ถ้าผู้เขียนสร้างแล้วได้ค่าไม่ตรง ให้บันทึกค่าจริงและสาเหตุก่อน commit
- **คอลัมน์ที่แสดงครบ (ทดสอบ)**
  - schema P: President.StateBorn (21), President.PartyName (7), Party.PartyName (9),
    PresidentMarriage.MarriageStatus (3 ค่ารวม NULL)
  - schema E (15 คอลัมน์): Category (10), Brand (15), Currency (1), CustomerGender (3), CustomerCity (12),
    CustomerCountry (10), Region (4), MembershipTier (5), MarketingChannel (8), CartAbandonment (2), ReturnStatus (3),
    RepeatCustomer (2), IsHighValue (2), IsWeekendOrder (2), PaymentMethod (5)
- **คอลัมน์ที่แสดงเพียงตัวอย่าง (ทดสอบ)**
  - ชื่อบุคคลใน schema P มี 43–49 ค่า: PresidentName ทั้งสามตาราง, SpouseName, VicePresidentName และ RunnerUp
  - รหัสและชื่อสินค้าใน schema E มี 2,089–2,387 ค่า: OrderID, CustomerID, ProductSKU และ ProductName
- **cap:** คอลัมน์หมวดหมู่มีค่าไม่ซ้ำสูงสุด 21 ค่า ส่วนคอลัมน์ชื่อหรือรหัสเริ่มที่ 43 ค่า
  ค่า cap ใดก็ได้ในช่วง 21–42 จึงให้ block เดียวกันทุก byte ผลไม่ขึ้นกับการเลือก cap = 25 (ทดสอบ)
- **ความยาว (ทดสอบ):** system ของแขน V ยาวสุด 2,665 ตัวอักษร (schema E) และ prompt รวม (system + user) ยาวสุด 2,803 ตัวอักษร (Q14 EN)
  เทียบกับ 1,078 ตัวอักษรของแขน B ในข้อเดียวกัน
- **coverage (ทดสอบ):** literal เป้าหมายของ VG ปรากฏใน block ครบ 9 ข้อ ได้แก่ Q01, Q07, Q09, Q13, Q14, Q15, Q21, Q30 และ Q42
  - Q48 ('None' ในคอลัมน์ RunnerUp ซึ่งแสดงเพียงตัวอย่าง) ไม่ปรากฏ ประกาศไว้ล่วงหน้า และวิเคราะห์แยกเป็น exploratory
- **การอ่านที่ประกาศไว้:** แขน V แสดงค่าของคอลัมน์หมวดหมู่ครบทุกค่า
  จึงเป็นขอบบน (upper bound) ของข้อมูลที่ได้จากการรัน `SELECT DISTINCT` ไม่ใช่การจำลองพฤติกรรมของนักศึกษา

**A3 Roster, identifier และ config การสุ่ม**

| model_key | บทบาท | identifier ที่ส่ง | echo ที่ล็อกจาก run-of-record | config |
|---|---|---|---|---|
| gpt-mini | confirmatory | `gpt-5.4-mini-2026-03-17` | `gpt-5.4-mini-2026-03-17` | temperature 0 |
| gemini-flash | confirmatory | `gemini-3.6-flash` | `gemini-3.6-flash` | temperature 0; ไม่ส่ง thinkingConfig (thinking ค่า default เหมือน ส.ค.); key ส่งใน header (c698547) โดย request body ไม่เปลี่ยน |
| claude-sonnet | confirmatory | `claude-sonnet-5` | `claude-sonnet-5` | ค่า default ของผู้ให้บริการ (AMENDMENT-3), max_tokens 1024; ไม่มี identifier แบบมีวันที่ (created_at 2026-06-29) echo lock จึงตรวจการเปลี่ยนรุ่นแบบเงียบไม่ได้ และใช้ provenance ก่อนและหลังรันแทน |
| llama31-8b | exploratory | `llama3.1:8b` (Ollama) | `llama3.1:8b` | temperature 0, seed 42 |
| qwen25-coder-7b | exploratory | `qwen2.5-coder:7b` (Ollama) | `qwen2.5-coder:7b` | temperature 0, seed 42 |
| typhoon2-8b | exploratory | `typhoon2-8b` (import ไฟล์ `llama3.1-typhoon2-8b-instruct.Q4_K_M.gguf` ตาม AMENDMENT-4 addendum) | `typhoon2-8b` | temperature 0, seed 42 |

- **บันทึก 13 ต.ค. 2026:** ผู้เขียน pull และ import โมเดล local ใหม่ก่อนรอบ ต.ค. (Ollama 0.32.5; digest llama3.1:8b 46e0c10c039e,
  qwen2.5-coder:7b dae161e27b0e, typhoon2-8b b3768487ef30; GGUF sha256 63a0e0730cc131abbd2d2ab7ddde27bf9aac530143e4b1f824d03399c4567770)
- รอบ ต.ค. เป็น experiment ใหม่ด้วยวิธีเดิม (Part 0) จึงไม่ใช้ raw output ของ ส.ค. เป็นเงื่อนไขหรือหลักฐาน
- digest ของเดือน ส.ค. ไม่ได้บันทึก (เปิดเผยสำหรับข้อมูล ส.ค. เท่านั้น; D-7)
- digest และ metadata ของรอบ ต.ค. อยู่ใน `results/rc1/provenance_gate1a.json`, `provenance_before.json` และ `provenance_after.json`
  และ runner หยุดก่อน generate แรกถ้า digest จาก `/api/tags` ไม่ตรงกับ `provenance_gate1a.json`
- **echo lock:** runner โหลด echo จาก run-of-record (`--lock-from results/results.jsonl`) ถ้า echo ไม่ตรงจะหยุดทันที (A5)
- ไม่เพิ่มหรือเปลี่ยนโมเดลในแขนนี้

**A4 การออกแบบ ขนาด และลำดับการรัน**
- **items:**
  - ถามทั้ง 60 ข้อของ suite รอบ ต.ค. `suite/k3n_suite_v1.3n_oct.tsv` (v1.3n ที่ซ่อม Q27 ตามมติ D11 ใน Part C3;
    ข้อความโจทย์ของอีก 59 ข้อเหมือน v1.2 ทุกตัวอักษร)
  - runner, dry-run และ grader อ่านไฟล์ `suite/k3n_suite_v1.3n_oct.tsv` ไฟล์เดียวกันทุกขั้น และ grade บนฐาน k3n
    (ขั้นตอนของผู้เขียนอยู่ใน RUNBOOK v2 ซึ่งแทน `kst_rev/drafts/RUNBOOK_RC1_DRAFT.md`)
  - primary analysis ใช้ 60 ข้อ (D11); การเทียบกับ log ส.ค. ใช้ 59 ข้อที่ถามเหมือนกันในสองรอบ (Part 0 ข้อ 3 และ A6 ข้อ 7)
- **ต่อโมเดล:** 2 arms × 2 ภาษา × 60 ข้อ × 5 runs = 1,200 records
- **ขนาดรวม**
  - API: 3 × 1,200 = 3,600 calls (แขน B 1,800 และแขน V 1,800)
  - local: 3 × 1,200 = 3,600 generations
  - รวม 7,200 records
  - dry-run บันทึก prompt ของทุก record ซึ่งมี prompt ที่ไม่ซ้ำกัน 240 แบบ (2 × 2 × 60)
- **ชุดขยาย (AMENDMENT-9):** 40 ข้อ × 2 ภาษา × 5 runs = 400 records ต่อโมเดล แขน base อย่างเดียว ทั้งหกโมเดล
  ใช้ runner และ payload เดียวกัน และ `--not-before` เดียวกับ core
- **ไฟล์ผล:**
  - `results/rc1/results_rc1_api.jsonl` และ `results/rc1/results_rc1_local.jsonl` (append-only และ resume ได้)
    ไม่สร้างไฟล์รวม เครื่องมือทุกตัวรับทั้งสองไฟล์ (`--log` และ `--results` ส่งซ้ำได้)
  - runner ปฏิเสธ `--out` ที่ชี้ไปที่ไฟล์เดียวกับ `--lock-from` (run-of-record) จึงต้องส่ง `--lock-from` ทุกครั้ง
- **ลำดับภายในโมเดล:**
  - run 1 ถึง 5 ในแต่ละ run ถาม EN ก่อน TH และถามข้อตามลำดับใน suite
  - สองแขนของข้อเดียวกันถามติดกัน และลำดับแขนสลับตาม parity ของ (ลำดับข้อ + run)
  - แขน B จึงเป็น concurrent control ที่ห่างจากแขน V เพียงไม่กี่วินาที
  - runner เขียน `seq` ที่ต่อเนื่องข้าม resume (ค่าสูงสุดในไฟล์ + 1), `run_id` (uuid4 hex 12 ตัวต่อโปรเซส)
    และ `t_epoch` (วินาที ทศนิยม 3 ตำแหน่ง) ทุก record
  - **คู่ที่พร้อมกัน:** record ของแขน B และแขน V ของ (model, lang, qid, run) เดียวกันที่ `run_id` เดียวกัน, seq ติดกัน
    และ |Δt_epoch| ≤ 130 วินาที (timeout ต่อ call 120 วินาที + sleep + ความละเอียดของ ts; latency สูงสุดของ ส.ค. 42.9 วินาที ทดสอบ)
  - คู่ที่ไม่พร้อมกัน (เช่น จาก resume หลัง error, circuit breaker หรือเครดิตหมด) ไม่ทำให้ log ใช้ไม่ได้
    check 8 ของ `check_rc1_log.py` รายงานจำนวนต่อโมเดลและเขียน key ของคู่ลงไฟล์
  - H1–H4 หลักใช้ทุก record; sensitivity ตัดทั้งสองแขนของคู่ที่ไม่พร้อมกัน แล้วคิด majority ของ cell จาก run ที่เหลือ
    (เกินครึ่งอย่างเคร่ง) และตัด cell ที่ไม่เหลือ run ออกจากทั้งสองแขน; ถ้าข้อสรุปต่างกันให้รายงานทั้งสองแบบ
- **ลำดับโมเดล:** สอง terminal รันขนานกัน
  - terminal 1 (API): gpt-mini → gemini-flash → claude-sonnet ตามลำดับ (ไม่ขนาน) แล้วชุดขยาย (AMENDMENT-9) ตามลำดับโมเดลเดิม
  - terminal 2 (local): llama31-8b → qwen25-coder-7b → typhoon2-8b แล้วชุดขยายตามลำดับโมเดลเดิม
  - ในแต่ละ terminal รัน core ของทุกโมเดลก่อน แล้วจึงชุดขยาย
  - แต่ละไฟล์ผลมีผู้เขียนครั้งละหนึ่งโปรเซส (runner ล็อกไฟล์ด้วย flock)
  - terminal ของ local ไม่ source `secrets.env`
- **ช่วงเวลา**
  - เริ่มหลัง Gate 1b push และใช้เวลา commit (`git log -1 --format=%cd --date=format:%Y-%m-%dT%H:%M:%S`; รูปแบบเดียวกับ ts ของ runner)
    เป็น `--not-before` ของทั้ง core และชุดขยาย
  - เก็บครบทุก record ภายใน 7 วันปฏิทินนับจาก call แรก
    เป้าคือวันเดียว ราว 4 ชม. wall time ซึ่งประมาณจาก latency เดือน ส.ค.
  - ถ้าเกิน 7 วัน ให้บันทึก addendum พร้อมเหตุผลก่อนเก็บต่อ
- **ค่าใช้จ่ายโดยประมาณ:** ราว US$11–12 สำหรับ core และชุดขยายรวมกัน (ทดสอบ; ราคาจากหน้าราคาของผู้ให้บริการ เข้าถึง 13 ต.ค. 2026)
  runner บันทึก token usage จึงคำนวณค่าจริงได้หลังรัน (`cost_rc1.py`; ป้าย list-price estimate)

**A5 เงื่อนไขก่อนรันและกฎหยุด**
1. **billing และยอดเครดิต (เงื่อนไขก่อนเริ่ม terminal 1)**
   - สถานะที่ผู้เขียนตรวจแล้ว: Gemini เป็น Prepay (Paid tier 1) และเปิด auto-reload; Anthropic เติมแล้วและปิด auto-reload; OpenAI มีเครดิต
   - ก่อน call แรก ผู้เขียนตรวจยอดใน console ของทั้งสามค่าย และบันทึกเฉพาะยอดและสถานะ auto-reload ใน addendum ของ Gate 3
   - เกณฑ์ขั้นต่ำ (ราว 1.5 เท่าของประมาณการทดสอบของ core และชุดขยาย): Anthropic ≥ US$6, OpenAI ≥ US$2,
     Gemini ≥ THB 600 หรือเปิด auto-reload; ถ้าไม่ถึงเกณฑ์ให้เติมก่อนเริ่ม
   - **เครดิตหมดกลางทาง:** runner หยุดด้วย circuit breaker (ข้อ 7); ผู้เขียนเติมเครดิตเองแล้วรันคำสั่งเดิมของโมเดลนั้นซ้ำ (resume)
     ภายในช่วง 7 วันของ A4; คู่ที่ถูกแยกจากการหยุดรายงานเป็นคู่ที่ไม่พร้อมกัน (A4); ห้ามแก้ `models.json`, ห้ามข้ามโมเดล
     และห้ามเริ่มชุดขยายของ terminal นั้นจนกว่า core ของ terminal นั้นจะครบ
   - project ของ Gemini ที่ใช้ในเดือน ส.ค. เปิด billing หรือไม่ ตรวจย้อนไม่ได้ (บันทึกว่าไม่ทราบ)
     ความต่างของสถานะ billing ระหว่างสองรอบรายงานเป็นเงื่อนไขที่ต่างกัน ส่วนตัวตนของโมเดลควบคุมด้วย echo lock
2. **กฎหยุดเมื่อ echo ไม่ตรง (ตรึงล่วงหน้า)**
   - **ขั้นตอนเมื่อหยุด**
     - runner หยุดทันทีด้วยข้อความ `MODEL SWAP DETECTED` และผู้เขียนหยุดทั้งสอง terminal รวมงานชุดขยายที่ยังไม่เริ่ม
     - ห้ามเรียกโมเดลใดอีก จนกว่าจะบันทึก addendum ลงวันที่ แล้ว commit และ push
     - addendum ต้องมีเวลา, model_key, echo เดิมและใหม่ และจำนวน record ที่เก็บแล้วของโมเดลนั้น
   - **gpt-mini (snapshot มีวันที่):**
     - echo ที่ต่างหมายถึงได้โมเดลอื่น records ของ gpt-mini ในแขนนี้ทั้งหมดจึงไม่ใช้ใน H1–H4
     - ถ้าผู้เขียนเลือกเก็บต่อด้วย identifier ใหม่ ต้องเก็บใหม่ครบทั้งสองแขน และรายงานเป็น exploratory
   - **gemini-flash และ claude-sonnet (alias ที่ไม่มีวันที่):**
     - echo ที่เท่าเดิมไม่รับประกันว่าน้ำหนักเหมือนเดือน ส.ค. ความต่างนี้วัดเป็น drift (A6)
     - ถ้า echo เปลี่ยน ให้ใช้กฎเดียวกับ gpt-mini
   - **ถ้าเหลือ frontier ที่ใช้ได้น้อยกว่าสองโมเดล:** H1–H4 เป็นเชิงพรรณนาทั้งหมด
   - **ถ้าเหลือสองโมเดล:** H1–H4 ใช้เฉพาะสองโมเดลนั้น ค่าสูงสุดของ GF เป็น 18, Holm ของ H4 ข้าม 2 โมเดล
     และเกณฑ์ GF_B < 4 ของ H1 ไม่เปลี่ยน
   - **ห้าม** แก้ `models.json` เพื่อเลี่ยงการหยุด
3. **ความสมบูรณ์ของ prompt**
   - runner ตรวจ sha256 ของไฟล์ hint ก่อนเริ่ม เมื่อได้รับ `--hints-sha256` จึงต้องส่ง option นี้ทุกครั้งที่เรียกโมเดล (dry-run ไม่ต้อง)
   - prompt log จาก dry-run (`results/rc1/prompts_rc1.jsonl`) ต้อง commit ใน Gate 1b
   - check_rc1_log.py ต้อง PASS ครบ 7 ข้อก่อน grade (core และชุดขยายตรวจแยกไฟล์)
     1. arm มีเฉพาะ base และ values (ชุดขยาย: base) และ record ของแขน values มี hints_sha256 ตรงกับ FREEZE STAMP
     2. ครบ 5 runs ทุก cell (ทุก id ของ suite × arm × ภาษา × โมเดล; log core ใช้ suite รอบ ต.ค. 60 ข้อตามมติ D11 เท่านั้น)
     3. echo ตรง run-of-record
     4. prompt hash ตรง dry-run
     5. ไม่มีการตัด prompt จาก num_ctx ในโมเดล local: ทุกคู่ของ (model, lang, qid, run) เดียวกันที่ `run_id` เดียวกัน, seq ติดกัน,
        แขน B มาก่อนแขน V และไม่มี error ต้องได้ tok_in(V) > tok_in(B)
        - ลำดับ B ก่อน V เกิดกับทุกข้อในอย่างน้อย 2 จาก 5 runs ตามกฎ parity ใน A4
        - ไม่เทียบคู่อื่น เพราะ Ollama อาจนับ prompt_eval_count เฉพาะ token ที่ไม่อยู่ใน prefix cache
        - cell ที่ไม่มีคู่ให้ตรวจ (เช่น resume แยกคู่) รายงานเป็น 'unchecked' พร้อมคำเตือนและจำนวน ไม่ทำให้ FAIL
          และข้อที่ไม่มีคู่ให้ตรวจเลยลงรายการ 'truncation unverified'
     6. record แรก (รวม error record) เกิดหลังเวลา commit ของ Gate 1b
     7. ไม่มี string ที่มีรูปแบบของ API key (พิมพ์เฉพาะเลขบรรทัด)
   - check 8 (รายงาน ไม่ใช่เงื่อนไข PASS): จำนวนคู่ที่ไม่พร้อมกันต่อโมเดลตามนิยามใน A4 และไฟล์ key ของคู่
     (`results/rc1/nonconcurrent_pairs.tsv`; ไม่มี raw หรือ sql) สำหรับ sensitivity; ชุดขยายข้าม check 8
4. **ไม่ดูผลระหว่างรัน**
   - runner แสดงเฉพาะบรรทัดความคืบหน้า
   - ห้ามเปิดไฟล์ `results_rc1*.jsonl` และห้าม grade จนกว่าจะเก็บครบและ check_rc1_log.py PASS
5. **error records:** HTTP error และ timeout ไม่นับเป็นความพยายาม การ resume เติมเฉพาะ cell ที่ยังไม่ครบ (เหมือน run-of-record)
6. **เก็บไม่ครบภายในช่วงเวลา:** ถ้าโมเดลใดเก็บไม่ครบ ให้รายงานเท่าที่มีพร้อมเหตุผล
   H1–H4 ใช้เฉพาะโมเดลที่เก็บครบทั้งสองแขน
7. **พฤติกรรมของ runner ที่ตรึง (ตรวจด้วย test แบบ offline ใน Gate 1a)**
   - หยุดเมื่อ error ติดกัน 5 ครั้ง (`--max-consecutive-errors 5`) ด้วย exit 3 และพิมพ์เฉพาะ HTTP status และชนิด error
   - Ollama digest lock: ก่อน local call แรก เทียบ `/api/tags` กับ `provenance_gate1a.json` หยุดเมื่อไม่ตรง และเขียน model_digest ทุก record
   - ข้อความ error ถูก redact ก่อนตัดที่ 250 ตัวอักษร
   - เขียนแต่ละ record ด้วย `os.write` ครั้งเดียว และล็อกไฟล์ผลด้วย `fcntl.flock` (ผู้เขียนไฟล์ละหนึ่งโปรเซส)
   - เขียน seq, run_id และ t_epoch ตาม A4
   - ใน live run ปฏิเสธ suite หรือ prompt log ที่ติดป้าย DRAFT

**A6 การให้คะแนนและตัววัด**
- **grading:** `harness/grade_v13n.py` กับ suite รอบ ต.ค. `suite/k3n_suite_v1.3n_oct.tsv` (Part C3; มติ D11) บน PostgreSQL 16.9
  ฐาน k3n แบบ read-only (`--db-fingerprint` ตรวจว่าเป็น k3n)
  - `results/rc1/graded_rc1.csv` (primary; 60 ข้อ)
  - `graded_rc1_positional.csv` (`--colperm off`) และ `graded_rc1_nocolroles.csv` (`--no-col-roles`; G1 ล้วน)
  - ไม่มีไฟล์ที่คง Q27 แยก เพราะ Q27 ฉบับซ่อมเป็น primary ของรอบ ต.ค. อยู่แล้ว (D11)
  - grader เขียนคอลัมน์ arm และ n_rows ให้
  - sensitivity บน k3: grade core ทั้งสองแขนด้วย suite v1.3 บนฐาน k3 ลง `results/rc1/k3/` (artifact เท่านั้น ไม่เขียน `paper/generated/`)
    suite v1.3 ไม่มี Q27 ฉบับซ่อม sensitivity นี้จึงครอบ 59 ข้อที่ถามเหมือนกัน
- **หน่วยวิเคราะห์:** majority ของ 5 runs ระดับ item (เหมือน analyze.py) บน 60 ข้อของ suite รอบ ต.ค. (D11)
- **ชุดข้อ**
  - VG_cov (สำหรับ H1) คือ VG items ที่ literal เป้าหมายปรากฏใน block: Q01, Q07, Q09, Q13, Q14, Q15, Q21, Q30, Q42
    ชุดนี้ไม่ขึ้นกับการเลือกชุด VG ใน Part B2 เพราะสองทางเลือกต่างกันเฉพาะ Q48 ซึ่ง block ไม่ครอบ
  - PLACEBO (สำหรับ H3) คือ 50 primary items ที่ gold ไม่มี VG literal ตาม vg_rule แบบ syntactic (60 − 10 บน suite รอบ ต.ค.; มติ D11)
- **GF (grounding failure):** ใช้นิยามและตัวจำแนกเดียวกับ Part B2.2–B2.3
  - implementation เดียวกันคือ `harness/analyze_rc1.py` ที่ตรึงด้วย sha256
- **ตัววัด**
  1. accuracy ต่อ model × arm × ภาษา บน 60 ข้อ พร้อม Wilson 95%
  2. GF ต่อ model × arm ในภาษาไทย บน VG_cov และนับระดับ run เป็นตัวรองเชิงพรรณนา
  3. gap ต่อ model × arm = จำนวนข้อที่ EN ถูก − จำนวนข้อที่ TH ถูก บน 60 ข้อ แยกเป็นส่วน VG_cov และส่วนที่เหลือ
  4. share remaining = ΣGap_V / ΣGap_B รวมสาม frontier พร้อม item-cluster bootstrap 95%
     - 10,000 รอบ, seed 20261012, percentile
     - สุ่มข้อพร้อมกันทุกโมเดล ทุกแขน และทุกภาษา
     - resample ที่ ΣGap_B ≤ 0 เก็บไว้ครบ 10,000 รอบ ให้ share remaining = +∞ ใน resample นั้น และรายงานจำนวน resample ดังกล่าว
       ถ้าเกิน 250 รอบ เขียน CI โดยระบุขอบล่างและระบุว่าขอบบนไม่นิยาม (unbounded)
  5. placebo flips = จำนวนข้อใน PLACEBO ที่ majority ต่างกันระหว่างแขน B กับแขน V ต่อ model × ภาษา
  6. exact McNemar ของแขน V เทียบแขน B ภาษาไทย 60 ข้อ ต่อ frontier
  7. drift = จำนวนข้อ (จาก 59 ข้อที่ถามเหมือนกันในสองรอบ; ไม่นับ Q27 ซึ่งรอบ ต.ค. ใช้โจทย์ฉบับซ่อมตามมติ D11) ที่ majority ของแขน B ต่างจาก log ส.ค. ที่ regrade ภายใต้ key v1.3n บน k3n (`results/v13n/graded_v13n.csv`)
     ต่อ model × ภาษา
  8. การแยก silent ต่อแขน ตามนิยามของ Part B1
  9. token usage และค่าใช้จ่ายจริง
- **manual audit**
  - ผู้เขียนตรวจคลาสของทุก failing run บน VG items ภาษาไทยของทั้งสองแขน
    จาก audit sheet ที่สลับลำดับแถว (seed 20261012) และซ่อนชื่อ arm และ model
  - ตัวจำแนกอัตโนมัติเป็นผลหลัก
  - รายงาน agreement เป็นร้อยละและ Cohen's κ ถ้าผลการตัดสิน GF ของ cell ใดต่างกัน ให้รายงานทั้งสองค่า

**A7 สมมติฐานและเกณฑ์ตีความ (ตรึงก่อนรัน)**
- **H1 (หลัก, confirmatory; frontier รวม; ภาษาไทย; VG_cov):** การเห็นค่าที่เก็บจริงลด GF
  - GF_B และ GF_V คือจำนวน cell (model × item) ที่เป็น GF ในแขน B และแขน V รวมสาม frontier (สูงสุด 27)
  - H1 เป็นกฎตัดสินที่ลงทะเบียนล่วงหน้าบน point estimate ไม่มีการทดสอบเชิงอนุมาน การอนุมานอยู่ที่ H4
  - GF_B < 4: รายงานเชิงพรรณนาเท่านั้น ไม่จัด band (scenario S0)
  - GF_V ≤ 0.25 × GF_B: **"information deficit"** (S1)
  - GF_V ≥ 0.75 × GF_B: **"persistent grounding failure"** (S3) รวมกรณีที่ GF_V มากกว่า GF_B
  - ค่าระหว่างสองเกณฑ์: **"partial"** (S2)
  - ค่าคาดการณ์ของผู้ร่างคือ information deficit
    เพราะความผิดใน run-of-record เป็นการคัดลอกคำไทยหรือประดิษฐ์ค่า ซึ่งรายการค่าน่าจะแก้ได้
    ค่าคาดการณ์ไม่ใช่เกณฑ์
- **H2 (gap):** ใช้ share remaining ของ A6 ข้อ 4
  - ΣGap_B ≤ 2 ข้อ: รายงานเชิงพรรณนา เพราะตัวหารไม่เสถียร
  - ≤ 0.60: ช่องว่างลดลงมาก
  - ≥ 0.90: ช่องว่างคงอยู่
  - ค่าระหว่างสองเกณฑ์: ลดลงบางส่วน
  - band ตัดสินจาก point estimate และรายงาน CI เสมอ
- **H3 (placebo):** placebo flips ไม่เกิน 2 ข้อต่อ frontier ต่อภาษา
  - ถ้า frontier โมเดลใดเกินในภาษาใดภาษาหนึ่ง (EN หรือ TH) ต้องรายงาน H1 และ H2 ทั้งแบบรวมและแบบตัดโมเดลนั้น
    (H2 ใช้ทั้งสองภาษา การเปลี่ยนคำตอบภาษาอังกฤษบนข้อที่ไม่ต้องใช้ค่าจึงกระทบ gap ได้)
  - และใช้ถ้อยคำแบบไม่อ้างเหตุ (A9 ตัวปรับ M2)
- **H4 (รอง):** exact McNemar สองทางของแขน V เทียบแขน B บน 60 ข้อภาษาไทย ต่อ frontier (มติ D11)
  - Holm ข้าม 3 โมเดล, α = 0.05
  - power ต่ำ (ประมาณการของร่าง 12 ต.ค.: discordant pairs ไม่เกินราว 6 ต่อโมเดล) ผลที่ไม่มีนัยสำคัญจึงไม่ใช่หลักฐานว่าไม่มีผล
- **ที่มาของเกณฑ์**
  - ค่าตัดของ band (0.25/0.75, 0.60/0.90, placebo ≤ 2, GF_B < 4, Holm ข้าม 3) คงตามร่าง 12 ต.ค. ซึ่งเขียนก่อนมี key v1.3
  - ส่วนที่เพิ่มหรือเปลี่ยนหลังผู้ร่างเห็นตัวเลขทดสอบของ v1.3 ได้แก่ guard ของ H2 (ΣGap_B ≤ 2), ชุด placebo 49 ข้อ (50 ข้อบน suite รอบ ต.ค. หลังมติ D11),
    กฎ GF แบบ union (B2.2), H1 บน VG_cov และการใช้ H3 ทุกภาษา
  - ทิศของการเปลี่ยน: guard และการใช้ H3 ทุกภาษาเพิ่มเงื่อนไขที่ทำให้ตีความเชิงเหตุยากขึ้น
    กฎ union นับ GF ได้เท่ากับหรือมากกว่ากฎ majority class เดิมในแขนทั้งสองเท่ากัน

**A8 Exploratory (รายงาน แต่ไม่ใช้ยืนยัน)**
- ผลของโมเดล local ทั้งสามตัว และคู่ typhoon2-8b เทียบ llama3.1:8b ภายใต้แขน V
- ผลของแขน V ในภาษาอังกฤษ โดยเฉพาะ Q14 ซึ่งต้องทำ value grounding แม้ในภาษาอังกฤษ
- Q48 ซึ่ง block ไม่ครอบ
- การแยก silent ต่อแขน
- sensitivity: เทียบตามตำแหน่ง (G1 ปิด), G1 ล้วน (ไม่ใช้ข้อยกเว้นคอลัมน์มีทิศทาง) และชุด VG9 (B2.1);
  รอบ ต.ค. ไม่มี sensitivity ที่คง Q27 แยก เพราะ Q27 ฉบับซ่อมเป็น primary อยู่แล้ว (มติ D11)

**A9 สถานการณ์ของ thesis และถ้อยคำ before → after (เขียนก่อนรัน; เลือกด้วย band เท่านั้น)**
- **กฎเลือกถ้อยคำ**
  - scenario กำหนดด้วย band ของ H1 (S0–S3)
  - clause เรื่อง gap กำหนดด้วย band ของ H2 (G-a ถึง G-d)
  - ตัวปรับกำหนดด้วย H4 (M1) และ H3 (M2)
  - ค่าในวงเล็บเหลี่ยมเติมจาก output ของ analyze_rc1.py และ Part B2 ที่ผู้เขียนรันเท่านั้น
  - ย่อถ้อยคำเพื่อให้พอดีหน้าได้ แต่ห้ามเปลี่ยนกริยาหรือ qualifier
  - ชุด VG ตัดสินแล้วเป็น VG10 (มติผู้เขียน 13 ต.ค. 2026 ข้อ 4; B2.1) ถ้อยคำที่ขึ้นกับชุด VG ใช้แบบ VG10 เท่านั้น
- **Before (เล่มที่ส่ง, abstract):**
  "value grounding --- recovering stored English constants from Thai wording --- drives up to $40\%$ of frontier Thai errors."
- **Before (ร่าง abstract 12 ต.ค.):**
  "With schema-only prompts, the 10 items whose stored English constants must be recovered from Thai wording account for up to 40% of frontier Thai errors; adding column values to the prompt [RESULT]."
- **After: clause ที่ใช้ทุก scenario** (การนับระดับ item ของ B2.6 ตามมติ D6; คำนวณบนแขน base ของรอบ ต.ค. ตาม Part 0 และไม่ขึ้นกับแขน values)
  - "With schema-only prompts, [a] of the three API proxies' [N] Thai errors fall on the [10] items whose gold compares a stored English constant absent from the Thai wording;"
- **After: ต่อท้ายตาม scenario (abstract)** — "grounding failures" คือ GF ของ B2.2 นิยามในวงเล็บครั้งเดียว
  - S1: "listing each text column's stored values in the prompt removed [most | all] of the grounding failures among them (a Thai word copied into, or an English value invented for, a filter; [GF_B] to [GF_V] in a concurrent re-run), so on these items they reflect information missing from the prompt rather than a limit of the models."
  - S2: "listing each text column's stored values in the prompt removed some of the grounding failures among them (a Thai word copied into, or an English value invented for, a filter) but not most ([GF_B] to [GF_V] in a concurrent re-run)."
  - S3: "the grounding failures among them (a Thai word copied into, or an English value invented for, a filter) persisted when each text column's stored values were listed in the prompt ([GF_B] to [GF_V] in a concurrent re-run)."
  - S0: "with each text column's stored values listed in the prompt, [GF_V] grounding failures (a Thai word copied into, or an English value invented for, a filter) occurred on these items against [GF_B] without, too few for the preregistered decision rule."
  - ใน S1 ใช้คำว่า "all" เมื่อ GF_V = 0 นอกนั้นใช้ "most"
- **Before (เล่มที่ส่ง, RQ2):**
  "The value-grounding subset locates the mechanism: although the 10 value-translated items are structurally easy (...), they concentrate a disproportionate share of frontier Thai errors --- 6 of gpt-5.4-mini's 15, 5 of gemini-3.6-flash's 15, and 2 of claude-sonnet-5's 10 --- with subset Thai accuracies of 40.0%, 50.0%, and 80.0% against 82.0%, 80.0%, and 84.0% elsewhere"
- **After: ส่วนที่ใช้ทุก scenario (RQ2)**
  "On the 10 value-grounding items, [a1] of gpt-5.4-mini's [N1] Thai errors fall, [a2] of gemini-3.6-flash's [N2], and [a3] of claude-sonnet-5's [N3]; by the preregistered count, [g1], [g2], and [g3] of these are value-grounding failures that copy the Thai word or invent an English value (Amendment 7). Outside these items the English--Thai gap is [x1], [x2], and [x3] points."
- **After: ต่อท้ายตาม scenario (RQ2)**
  - S1: "In a concurrent re-run whose prompt also lists each text column's stored values (Table [VI]), grounding failures fell from [GF_B] to [GF_V] across the three proxies; on these items the Thai errors reflect information that the schema-only prompt withholds and that a \texttt{SELECT DISTINCT} query would reveal."
  - S2: "In a concurrent re-run whose prompt also lists each text column's stored values (Table [VI]), grounding failures fell from [GF_B] to [GF_V], short of the preregistered three-quarters; the stored values help but do not by themselves remove the failure."
  - S3: "In a concurrent re-run whose prompt also lists each text column's stored values (Table [VI]), grounding failures barely changed ([GF_B] to [GF_V]); the models copy or invent values even with the stored values in view, so missing information does not explain most of the failure."
  - S0: "In a concurrent re-run whose prompt also lists each text column's stored values (Table [VI]), the baseline arm produced [GF_B] grounding failures, too few for the preregistered decision rule, against [GF_V] with the values listed; we report the counts without inference."
- **After: clause เรื่อง gap (ใส่ใน abstract ทุก scenario ยกเว้น G-d และใส่ใน RQ2 ทุก scenario)**
  - ร่างก่อนหน้าให้ใส่ใน abstract "เฉพาะ S1 และเฉพาะเมื่อมีที่" ซึ่งเปิดให้เลือกหลังเห็นผล จึงตรึงเป็นแบบเดียวก่อนมีข้อมูล
  - abstract รายงานผลที่ลงทะเบียนไว้ทั้งสองข้อของแขน values (H1 และ H2) ไม่ว่าออกทิศใด
    และกันไม่ให้ประโยคของ S1 ถูกอ่านว่าอธิบายช่องว่างภาษาไทยทั้งหมด
  - G-a (≤ 0.60): "and the pooled frontier English--Thai gap fell to [s] of its schema-only size (item-bootstrap 95% CI [lo, hi])."
  - G-b (ระหว่างสองเกณฑ์): "while the pooled frontier English--Thai gap shrank only partly, to [s] of its schema-only size ([lo, hi])."
  - G-c (≥ 0.90): "while the pooled frontier English--Thai gap remained at [s] of its schema-only size ([lo, hi])."
  - G-d (ΣGap_B ≤ 2): ไม่เขียน clause นี้ และรายงานจำนวนข้อใน Table [VI] เท่านั้น
- **ตัวปรับ**
  - M1: ถ้า H4 มีนัยสำคัญหลัง Holm ในโมเดลใด ให้เติม "(Thai accuracy gain significant after Holm for [model])"
    H4 ทดสอบ accuracy บน 60 ข้อ ไม่ได้ทดสอบ GF จึงห้ามวางคำว่า significant ติดกับจำนวน GF
    ถ้าไม่มีโมเดลใดผ่าน ห้ามใช้คำว่า significant
  - M2: ถ้า H3 ไม่ผ่านในโมเดลใด (ภาษาใดก็ตาม) ให้เปลี่ยน "removed" และ "fell" เป็น "coincided with fewer"
    และเติม "(the values also changed [k] answers on items that need no stored value)"
    และตัดวลีเชิงเหตุของ S1 ออกทั้งสองที่ ได้แก่ "so on these items they reflect information missing from the prompt rather than a limit of the models" (abstract)
    และ "on these items the Thai errors reflect information that the schema-only prompt withholds …" (RQ2)
- **Discussion "Mind the values" ตาม scenario**
  - S1: ข้อเสนอ inspect-then-filter มีหลักฐานระดับเครื่องมือ แต่ยังเป็นสมมติฐานที่ต้องทดสอบกับนักศึกษา
  - S2 และ S3: ข้อเสนอให้ pin literal ในใบงานคงเป็นข้อเสนอที่ยังไม่ทดสอบ และต้องระบุว่าการเห็นค่าที่เก็บจริงไม่พอ
  - S0: ไม่สรุปเรื่องผลของ prompt

**A10 การรายงาน**
- รายงานทุกผลไม่ว่าจะออกทิศใด
- ตัวเลขของแขน values ในเล่มมาจาก `analyze_rc1.py` และ `make_table_rc1.py` เท่านั้น
- ตัวเลขหลักใน Table II–V มาจากแขน base ของรอบ ต.ค. ภายใต้ key v1.3n บนฐาน k3n กับ suite รอบ ต.ค. 60 ข้อ (Part 0; มติ D11)
  แขน B จึงเป็นทั้งผลหลักของเล่มและ concurrent control ของแขน V; re-grade log ส.ค. ตาม Part C ใช้เทียบความสอดคล้องและวัด drift
  บน 59 ข้อที่ถามเหมือนกัน
- ผลของโมเดล local ติดป้าย exploratory ทุกจุด
- deviation ทุกข้อบันทึกเป็น addendum ลงวันที่ก่อนเริ่มวิเคราะห์

---

### Part B — การวิเคราะห์เชิงพรรณนา (บนแขน base ของรอบ ต.ค. เป็นผลหลัก และบน log ส.ค. เป็นผลรอง ตาม Part 0; มติ D3, D6; self-assessment 3.4, 3.6, 3.7c, 3.7d, 3.9)

**B0 ขอบเขตร่วม**
- **input หลัก:** `results/rc1/graded_rc1.csv` กับ `--arm base` และ suite รอบ ต.ค. (n=60; Q27 ฉบับซ่อมตามมติ D11)
  และ `results/rc1/results_rc1_api.jsonl` กับ `results_rc1_local.jsonl`
- **input รอง:** `results/v13n/graded_v13n.csv` (re-grade log ส.ค. บน k3n ตาม Part C; n=59) และ `results/results.jsonl`
  - jsonl ทุกไฟล์อ่านด้วย `python3 -I` เฉพาะ field model_key, arm, lang, qid, run, sql และ parse_ok และตรวจเพียงว่า field error เป็น null หรือไม่
  - ห้ามพิมพ์หรือคัดลอก field error เพราะข้อความ error จากผู้ให้บริการบางรายการต้องไม่เผยแพร่ (artifact ใช้ snapshot ที่ mask แล้ว)
- **สัญญา `--arm`:** สคริปต์ทุกตัวที่อ่านไฟล์ graded หรือ jsonl รับ `--arm` (ไม่มีค่า default) กรองแถวตาม arm
  และหยุดเมื่อ cell ใดไม่มี run เท่ากับ 5 หลังกรอง; แถวที่ไม่มีคอลัมน์ arm (log ส.ค.) ถือเป็น base
- **sensitivity:** accuracy พร้อม Wilson CI, McNemar TH–EN กับ Holm, unanimity/flip, parse rate และ value_translated (`analyze.py`)
  บน `graded_rc1_positional.csv` และ `graded_rc1_nocolroles.csv` ของรอบ ต.ค. และบน `graded_v13n_withQ27.csv` (n=60),
  `graded_v13n_positional.csv` และ `graded_v13n_nocolroles.csv` ของ log ส.ค.
  - รอบ ต.ค. ไม่มี sensitivity ที่คง Q27 แยก เพราะ Q27 ฉบับซ่อมเป็น primary อยู่แล้ว (D11)
  - ตัวเลขบน `results/graded.csv` (v1.2) รายงานใน artifact เพื่อเทียบกับเล่มที่ส่ง
- **สถานะ:** B1–B5 เป็นการวิเคราะห์เชิงพรรณนาที่ลงทะเบียนล่วงหน้า (pre-specified descriptive) ไม่มีสมมติฐานเชิงทิศ
  ส่วน B6 เป็น exploratory
- **frontier** หมายถึง claude-sonnet, gpt-mini และ gemini-flash
- **สคริปต์:**
  - `harness/analyze_log_v13.py` สำหรับ B1, B3, B4, B5 และ B6 (B5 อ่านผลของ `harness/plan_quality.py`)
  - B2: `harness/analyze_rc1.py` โหมด rc1 สำหรับแขน base ของรอบ ต.ค. (ค่า slot ของ A9) และโหมด base-only สำหรับ log ส.ค.
  - ตารางของเล่ม: `harness/analyze.py`, `analyze_typhoon.py`, `phi_tableiv.py`, `empty_split_v13.py`, `make_tables.py` และ `make_figures.py`
  - ทุกไฟล์ตรึงด้วย sha256 ใน Gate 1b
  - ผู้เขียนรันทีละคำสั่งหลัง Gate 1b เท่านั้น

**B1 การแยก loud / silent-empty / silent-non-empty (D3; ตอบ R1-W4 และ R1-RC4)**
- **คลาสของ run ที่ผิด** (correct = False ภายใต้ key primary)
  - loud: exec_ok = False คือ fail_reason เป็น parse, non-select, timeout หรือ exec-error
  - silent-empty: exec_ok = True และ n_rows = 0
  - silent-non-empty: exec_ok = True และ n_rows ≥ 1
  - silent คือ silent-empty รวมกับ silent-non-empty
- **ผลหลัก (ระดับ run):** frontier รวม ตามด้วยรายโมเดล × ภาษา, VG (ชุดของ B2.1) กับ non-VG
  และโมเดล local ซึ่งติดป้าย exploratory
- **ผลรอง (ระดับ item):** cell ที่ majority ผิดได้คลาสที่ failing runs ของ cell นั้นเป็นมากกว่าครึ่ง ถ้าไม่มีคลาสใดเกินครึ่ง จัดเป็น "mixed"
- **คำศัพท์:** ไม่ใช้คำว่า "plausible" เป็นนิยาม ใช้คำว่า "non-empty"
- **กฎถ้อยคำในเล่ม**
  - abstract และ Discussion เขียนได้ว่า "most frontier errors ([x]% of error runs) execute without error and return a non-empty table"
    เฉพาะเมื่อ silent-non-empty มากกว่า 50% ของ frontier error records ระดับ run และต้องระบุร้อยละ [x] ทุกครั้ง
    ห้ามบรรยายความผิดทั้งหมดว่าคืนตารางที่ไม่ว่าง
  - ถ้าไม่ถึง ให้ใช้ "executes without error" และรายงานสัดส่วนผลว่างคู่กัน
  - **การเปิดเผย:** ผู้ร่างตั้งเกณฑ์ 50% หลังเห็นตัวเลขทดสอบ (98/151 ≈ 65% ภายใต้ key v1.3 บน k3 และ 102/151 ≈ 68% ภายใต้ key v1.3n บน k3n; log ส.ค.) เกณฑ์นี้จึงไม่ได้ปิดตา
    ค่าตัด 50% มาจากความหมายตรงตัวของคำว่า "most" ไม่ได้มาจากตัวเลข
  - ตัวอย่าง หม้าย ใน RQ2 ต้องระบุว่าเป็น silent-empty
  - เพิ่มตัวอย่าง silent-non-empty หนึ่งตัวที่ผู้เขียนเลือกเพื่อความชัด และระบุว่าเป็นภาพประกอบ ไม่ใช่การวัด
- **ตัวบรรยายเสริม (exploratory):** shape match คือ rows × cols เท่ากับ primary gold
  ต้อง re-execute ด้วย `empty_split.py` ที่ปรับให้อ่าน key v1.3 และไม่ใช้ใน abstract
- **ตัวเลขที่ผู้ร่างเห็น (ทดสอบ)**
  - key v1.2: frontier error records 297 = loud 13 + silent-empty 40 + silent-non-empty 244
  - key v1.3: 151 = 13 + 40 + 98 (silent 138 = 91.4%)
  - key v1.3n บน k3n: 151 = 13 + 36 + 102 (silent 138 = 91.4%)

**B2 ชุด VG, การนับที่แทน "up to 40%" และนิยาม value-grounding failure (D6)**

ตามข้อแนะนำ D6 ที่ผู้เขียนอนุมัติ: abstract ใช้การนับระดับ item แบบ set-based (B2.6) เขียนเป็นจำนวน
และตัวเลขระดับกลไก (GF; B2.2) อยู่ใน RQ2 นิยามทั้งสองตรึงในหัวข้อนี้ก่อนผู้เขียนรัน

*B2.1 ชุด VG (ตัดสินแล้ว: VG10; มติผู้เขียน 13 ต.ค. 2026 ข้อ 4)*
- **ชุดหลัก: VG10** ตามกฎของ AMENDMENT-6: Q01, Q07, Q09, Q13, Q14, Q15, Q21, Q30, Q42, Q48
  - ถ้อยคำในเล่มเปลี่ยนจาก "requires value grounding" เป็นการบรรยายว่า gold เทียบค่าภาษาอังกฤษที่เก็บจริงซึ่งไม่ปรากฏในโจทย์ภาษาไทย (A9)
  - หมายเหตุ Q48: gold ของ Q48 เทียบ literal 'None' ซึ่งบน k3n ไม่ใช่ค่าที่เก็บแล้ว (ค่าที่ไม่มีอยู่เป็น NULL ตามกฎข้อมูล)
    Q48 อยู่ใน VG10 ตามกฎ syntactic ของ AMENDMENT-6 และ block ของแขน values ไม่ครอบ (A2)
- **sensitivity: VG9** คือข้อของ VG10 ที่การแทน literal นั้นทุกตำแหน่งใน gold พร้อมกันด้วย `'zzqabsentvaluezzq'` (ไม่มี wildcard ของ LIKE)
  ทำให้ผลของ gold บนฐาน k3n เปลี่ยนแบบ multiset (คาด: VG10 ยกเว้น Q48; ทดสอบ)
- **เครื่องมือ:** `harness/make_vg_sets.py` อ่านเฉพาะ suite และ gold บนฐาน ไม่รับไฟล์ผลของโมเดล
  เขียน `suite/vg_set_v13n.txt` (VG10) และ `suite/vg_set_v13n_VG9.txt` (VG9) และหยุดเมื่อรายการต่างจากที่คาด (Gate 1a)
  - analyze.py, analyze_typhoon.py, analyze_rc1.py และ analyze_log_v13.py อ่านรายการ VG จากไฟล์เมื่อได้รับ `--vg-set`
    และเมื่อไม่ได้รับ ให้ผลบน v1.2 เหมือนเดิมทุก byte (ตรวจใน Gate 1a)
- **การรายงาน:** รายงานทั้งสองชุดคู่กัน VG9 เป็น sensitivity
- **กฎหยุด:** ถ้าผู้เขียนรันแล้วได้รายการต่างจากที่คาด ให้หยุดและบันทึกก่อนใช้

*B2.2 นิยามระดับกลไก (นิยามเดียว; ใช้ใน RQ2 และใน H1): value-grounding failure (GF) ระดับ item*
- cell (model, TH, item) เป็น GF เมื่อเข้าครบสามเงื่อนไข
  1. item อยู่ในชุด VG ของ B2.1
  2. majority ของ 5 runs ผิดภายใต้ key v1.3
  3. failing runs ของ cell นั้นมากกว่าครึ่ง ถูกตัวจำแนกใน B2.3 จัดเป็น THAI_COPY หรือ INVENTED
- **การนับ:** ตัวตั้งคือจำนวน GF ต่อ frontier model ตัวหารคือจำนวนข้อภาษาไทยที่ majority ผิดของโมเดลนั้น (60 ข้อบนแขน base ของรอบ ต.ค. และ 59 ข้อบน log ส.ค.; มติ D11)
  รายงานในรูป "g of N" ต่อโมเดล และผลรวมของ frontier

*B2.3 ตัวจำแนก (ตรึง; implementation เดียวกับ Part A)*
- **target:** สำหรับ VG literal ทุกตัวของ gold หาคอลัมน์ที่ gold เทียบกับ literal นั้นด้วย `=`, `<>` หรือ `!=`
- **vocabulary:** ค่าที่เก็บจริงทั้งหมดของคอลัมน์ที่มีค่าไม่ซ้ำไม่เกิน 100 ค่า
  นำมาจาก field `full_values` ใน `value_hints_v1.json` (สร้างจาก k3n) ซึ่งไม่เข้า prompt
  (อ้างด้วยชื่อคอลัมน์; คอลัมน์เป้าหมายของ VG ทุกตัวมีชื่อไม่ซ้ำข้ามตาราง)
  - ไม่มีกฎพิเศษสำหรับ Q48: log ส.ค. ไม่มี run ใดของ Q48 ที่ใช้ literal 'None' (ทดสอบ) และ prompt ของรอบ ต.ค. ไม่มี 'None'
    `analyze_rc1.py` พิมพ์จำนวน run ของ Q48 ที่ใช้ literal 'None' ถ้าเกิดขึ้น และรายงานในเล่มถ้าไม่เป็นศูนย์
- **คลาสของ failing run (ตรวจตามลำดับนี้)**
  1. THAI_COPY: string literal ใดใน SQL มีอักษรไทย
  2. INVENTED: literal ที่เทียบกับคอลัมน์เป้าหมาย (`=`, `<>`, `!=`, `IN`, `NOT IN`, `LIKE`, `NOT LIKE`, `ILIKE`) ไม่ตรงกับค่าใดใน vocabulary
     - สำหรับ `=`, `<>`, `!=`, `IN`, `NOT IN`: ตรงตัว (case-sensitive)
     - สำหรับ `LIKE` และ `NOT LIKE`: อ่าน literal เป็น pattern (`%` และ `_` เป็น wildcard) และนับว่าไม่ตรงเมื่อ pattern ไม่ match ค่าใดใน vocabulary
     - สำหรับ `ILIKE`: เหมือน `LIKE` แต่ไม่สนตัวพิมพ์
     - เหตุผล: `LIKE '%Widow%'` อ้างค่าที่เก็บจริง จึงไม่ใช่การประดิษฐ์ค่า
       (implementation เดียวอยู่ใน `harness/vg_classifier.py` ซึ่ง `analyze_rc1.py` และ kit ของ AMENDMENT-8 ใช้ร่วมกัน;
       อ่าน literal ของ `LIKE`, `NOT LIKE`, `ILIKE` และ `NOT ILIKE` เป็น pattern ตามข้อนี้)
       - คอลัมน์เป้าหมายอาจอยู่ในเครื่องหมายคำพูดคู่ (เช่น "MarriageStatus" มีหรือไม่มี alias นำหน้า) และการเทียบค่าเดี่ยวอาจเขียนสลับข้าง (เช่น 'Widow' = MarriageStatus) ตัวจำแนกอ่านทั้งสองรูป
       - comment ของ SQL ไม่นับเป็น code: comment แบบ `--` และแบบ `/* */` (ซ้อนกันได้ตามที่ PostgreSQL อ่าน) ที่อยู่นอก literal และนอกชื่อในเครื่องหมายคำพูดคู่ ถูกตัดออกก่อนตรวจ
         ดังนั้นเครื่องหมาย ' ใน comment ไม่เปิด literal และคำไทยในเครื่องหมายคำพูดภายใน comment ไม่นับเป็น literal ภาษาไทย
       - จุดบอดที่ทราบและเปิดเผยไว้: คอลัมน์เป้าหมายที่อยู่ในฟังก์ชันหรือ cast (เช่น LOWER(MarriageStatus) = 'widowed') ไม่ถูกนับเป็น predicate จึงได้ NO_PRED
         และ string แบบ dollar-quoted หรือ E'...' ไม่ถูกอ่านเป็น literal (เครื่องหมาย ' ที่ escape ด้วย backslash ใน E'...' ทำให้ literal จบก่อนกำหนด)
  3. NO_PRED: คอลัมน์เป้าหมายไม่มี predicate ที่เป็น literal (run ที่ไม่มี SQL อยู่ในคลาสนี้)
  4. GROUNDED: literal เป้าหมายทุกตัวปรากฏบนคอลัมน์ของตน (run ผิดด้วยเหตุอื่น)
  5. STORED: บนคอลัมน์เป้าหมายใช้เฉพาะค่าที่เก็บจริง แต่ไม่ใช่ literal เป้าหมาย เช่น `NOT IN ('Returned','Exchanged')`
- **การตรวจด้วยมือ**
  - ผู้เขียนตรวจคลาสของทุก failing run ใน cell ที่นับ จาก audit sheet ที่ซ่อนคลาสของตัวจำแนก
  - ตัวจำแนกเป็นผลหลัก และรายงาน agreement
  - ถ้าผลการตัดสิน GF ของ cell ใดต่างกัน ให้รายงานทั้งสองค่า

*B2.4 เหตุผลที่เลือกนิยาม GF แบบนี้ (ตัวเลขระดับกลไก)*
1. **ตรงกับ construct:** นับเฉพาะความผิดที่ตัว SQL แสดงกลไก grounding คือคัดลอกคำไทยหรือใช้ค่าที่ไม่มีอยู่จริง
   - การนับแบบ set-based (B2.6) นับทุกความผิดบน item ที่ต้องทำ grounding จึงเป็นตัวเลขระดับ item ไม่ใช่ระดับกลไก
   - ภายใต้ key v1.2 ความผิดบน VG items บางส่วนมาจากเหตุอื่น ได้แก่ ลำดับคอลัมน์ของ Q42, คอลัมน์กำกวมของ Q21 และการอ่านโจทย์ผิดของ Q48
2. **นิยามเดียวกับ GF ใน H1:** ตัวเลขระดับกลไกใน RQ2 และผลของแขน values จึงพูดถึงสิ่งเดียวกัน
   และตอบคำถาม "how much of the value-grounding errors remain" ของ R1 ในหน่วยเดียวกัน
3. **ทำซ้ำได้:** ใช้ตัวจำแนกอัตโนมัติที่ตรึงด้วย sha256 และผู้เขียนตรวจด้วยมือทุก run
4. **ความสัมพันธ์กับการนับอื่น:** GF เป็นเซตย่อยของการนับแบบ set-based เสมอ
   - ผู้ร่างเห็นตัวเลขทดสอบของการนับแบบอื่นก่อนเลือก (B2.5) จึงพิสูจน์ไม่ได้ว่าการเลือกไม่ขึ้นกับตัวเลข
   - ตัวจำแนกแบบ majority class ของร่าง 12 ต.ค. ให้ค่าต่ำสุดของ gpt-5.4-mini (3/15; key v1.2)
     กฎ union ใน B2.2 ให้ค่าเท่ากับหรือมากกว่านั้น และยังไม่ได้คำนวณ
5. **ไม่ต้องตัดสิน tie ด้วยมือ:** กฎ strict majority ของ THAI_COPY ∪ INVENTED แทน majority class
   (ร่าง 12 ต.ค. ใช้ majority class และให้ผู้เขียนตัดสิน tie เอง)
- **นิยามระดับกลไกที่ไม่เลือก**
  - contrast-based (VG items ที่ EN ถูกแต่ TH ผิด) บอกว่าความผิดเฉพาะกับภาษาไทย แต่ไม่ได้บอกกลไก จึงรายงานเชิงพรรณนาใน B2.6
  - การตัดบางข้อออกเป็นรายข้อ (เช่น ตัด Q42 กับ Q48) ไม่ใช่กฎทั่วไป

*B2.5 การเปิดเผย*
- **ตัวเลขที่ผู้ร่างเห็น (ทดสอบ; key v1.2; VG10)**
  - gpt-5.4-mini: 3/15 ตามตัวจำแนกของร่าง 12 ต.ค., 4/15 เมื่อตัด Q42 และ Q48, 5/15 เมื่อนับเฉพาะ VG items ที่ EN ถูกแต่ TH ผิด
    และ 6/15 แบบ set-based ซึ่งเป็นตัวเลขในเล่มที่ส่ง
  - gemini-3.6-flash 4/15 และ claude-sonnet-5 1/10 ตามตัวจำแนก
- **ภายใต้ key v1.3 (ทดสอบ):** set-based ได้ gpt 5/11, gemini 4/6, claude 1/6 และถ้าใช้ VG9 gpt ได้ 4/11
- **สิ่งที่ยังไม่ได้คำนวณ:** GF ภายใต้ key v1.3

*B2.6 การนับระดับ item (set-based) — ตัวเลขที่แทน "up to 40%" ใน abstract ตามมติ D6*
- **a of N:** ต่อ frontier model, a คือจำนวนข้อภาษาไทยในชุด VG (B2.1) ที่ majority ผิดภายใต้ key v1.3
  และ N คือจำนวนข้อภาษาไทยทั้งหมดที่ majority ผิด (60 ข้อบนแขน base ของรอบ ต.ค. และ 59 ข้อบน log ส.ค.; มติ D11) รายงานต่อโมเดลและผลรวมของสาม frontier
- **contrast count (เชิงพรรณนา):** จำนวน VG items ที่ EN ถูกแต่ TH ผิด
- รายงานทั้งสามตัวเลข (a, contrast และ GF ของ B2.2) บนชุด VG ทั้งสองชุด ชุดที่ไม่ได้เลือกเป็น sensitivity

*B2.7 กฎถ้อยคำ*
- abstract ใช้การนับ set-based ของ B2.6 ในรูป "[a] of [N]" (ผลรวมสาม frontier) ด้วยกริยาที่ไม่อ้างเหตุ ("fall on") ตามแม่แบบใน A9
- RQ2 รายงาน a และ GF ("g of N") ต่อโมเดลตามแม่แบบใน A9; contrast count อยู่ในตารางของ artifact
- ห้ามใช้ "up to …%"
- ห้ามใช้กริยาที่อ้างเหตุ ได้แก่ drives, originate, trace to และ locates the mechanism
- ถ้อยคำเชิงเหตุเรื่อง prompt ใช้ได้เฉพาะตาม scenario ของ A9

**B3 gap นอกชุด VG (self-assessment 3.9)**
- **ตัววัด:** ต่อ frontier model คำนวณจำนวนข้อที่ EN ถูก − จำนวนข้อที่ TH ถูก บน primary items นอกชุด VG
  (นอก VG10: 50 ข้อบนแขน base ของรอบ ต.ค. และ 49 ข้อบน log ส.ค.; การนับนอก VG9 เป็น sensitivity) ระดับ item
  - รายงานเป็นจำนวนข้อ จุดร้อยละ และ discordant b/c แยกรายโมเดล และรวม frontier
- **exploratory:** exact McNemar รายโมเดล ไม่ทำ Holm และไม่ใช้สรุป
- **ตัวเลขที่ผู้ร่างเห็น (ทดสอบ; key v1.2; 50 ข้อ):** gpt +1, gemini +2, claude +5 ข้อ (+2, +4, +10 จุด)
- **ถ้อยคำ:** "Outside the value-grounding items, the English--Thai gap is [x], [y], and [z] points." โดยไม่ตีความเชิงเหตุ

**B4 ความแปรปรวนของ SQL text (self-assessment 3.6)**
- **cell:** (model, ภาษา, item) บน 60 ข้อของรอบ ต.ค. หรือ 59 ข้อของ log ส.ค. (มติ D11) runs คือ records ที่ error เป็น null (5 runs ต่อ cell)
- **normalize SQL**
  - ตัด whitespace หัวท้าย
  - ยุบ whitespace ทุกชนิดที่ต่อกันเป็นช่องว่างเดียว
  - ตัด `;` ท้าย
  - ไม่เปลี่ยนตัวพิมพ์
  - run ที่ parse_ok = False ใช้ค่า `<NO_SQL>`
- **ตัววัดต่อ model × ภาษา**
  - (a) text-unanimous cells: SQL ทั้ง 5 runs เหมือนกันหลัง normalize
  - (b) การกระจายของจำนวน SQL ที่ต่างกันต่อ cell (1–5)
  - (c) grade-unanimous cells: ผล correct ของทั้ง 5 runs เหมือนกันภายใต้ key v1.3
  - (d) byte-exact unanimity โดยไม่ normalize (ตัวรอง)
- **ถ้อยคำในเล่ม**
  - ใช้คำว่า "bit-stable" ได้เฉพาะเมื่อ (d) เป็น 100% ของ cell
    ถ้าไม่ถึง ให้ใช้ "grade-stable" และรายงาน (a) คู่กัน
  - ประโยค "one-in-ten to one-in-twenty" แทนด้วย "a differently graded answer in [100 − (c)]% of API cells"
    รายงานเป็นช่วงต่ำสุดถึงสูงสุดของสาม frontier
- **ตัวเลขที่ผู้ร่างเห็น (ทดสอบ)**
  - key v1.2: SQL ของ local ต่างกันข้าม runs ใน 6 จาก 360 cells (llama 4, qwen 2)
  - API ต่างกันราว 46–58% ของ cells หลัง normalize
  - grade-unanimous ภายใต้ key v1.3: API 331/354, local 353/354
- ถ้า (a) ของ local ต่ำกว่า 100% ข้อความใน AMENDMENT-3 ("deterministic โดยพิสูจน์แล้ว 60/60 ทุกช่อง")
  จริงในระดับ grade แต่ไม่จริงในระดับ SQL text (บันทึกใน Part D-4)

**B5 Q51 (self-assessment 3.7d)**
- **แหล่งข้อมูล:** ผลหลัก `results/rc1/base60/plan_indexed.csv` และ `plan_noindex.csv` จากแขน base ของรอบ ต.ค.;
  ผลรอง `results/v13n/plan_indexed.csv` และ `plan_noindex.csv` จาก log ส.ค.; ทั้งสองชุดใช้ gold v1.2 ที่คำนวณใหม่บนสำเนา `k3n_rq3` ของ k3n (Part C5)
  - ข้อที่ซ่อมตามมติ D11 ใช้ gold ฉบับซ่อมในรอบ ต.ค. และ gold เดิมใน log ส.ค.; Q27 มี eff = no จึงไม่อยู่ในชุดข้อของ RQ3 ทั้งสองรอบ (ทดสอบ)
- **ตัววัดแยกต่อเฟส**
  - จำนวนโมเดลที่มี majority-correct cell บน Q51 (ภาษาใดก็ได้) ที่ cost_ratio_vs_gold < 1.00
  - ค่า ratio ต่ำสุด
  - "beats gold by x%" โดย x = (1 − ratio ต่ำสุด) × 100 ปัดเป็นจำนวนเต็ม
- **ถ้อยคำ:** "[k] model(s) beat gold's planner cost by [x]% (with indexes; [y]% without) on a top-1-per-group item"
- **ข้อมูลที่ผู้ร่างเห็น (ผลทางการ v1.2 ใน `results/plan_*.csv`)**
  - claude-sonnet และ gemini-flash ได้ ratio 0.76 (indexed) และ 0.84 (noindex) ทั้ง EN และ TH
  - gpt-mini ได้ 1.00
  - เล่มที่ส่งเขียนว่า "one model"

**B6 Exploratory**
- **(self-assessment 3.4)** typhoon2-8b เทียบ llama3.1:8b
  - นับจาก B1 ระดับ run: จำนวน loud, silent-empty และ silent-non-empty ต่อภาษา
  - จำนวน loud runs ที่ fail_reason ระบุว่าคอลัมน์หรือฟังก์ชันไม่มีอยู่ (ข้อความ error ของ PostgreSQL ไม่ใช่ของ API)
  - ข้อความในเล่ม "executable SQL naming wrong columns" ต้องแก้ให้ตรงกับผลนี้
- **(self-assessment 3.7c)** จำนวน TH VG items (ชุดของ B2.1) ที่ typhoon2-8b และ llama3.1:8b ผิด
  - ใช้ "no harder than the base" ได้เฉพาะเมื่อ typhoon ผิดไม่มากกว่า llama
- contrast ทุกตัวที่เกี่ยวกับ Typhoon เป็น exploratory (Part D-3)

---

### กฎข้อมูล: การเข้ารหัสค่าที่ไม่มีอยู่ 'None' → NULL (ส่วนหนึ่งของ AMENDMENT-7 มีผลก่อน Part C; คำสั่งผู้เขียน 13 ต.ค. 2026 และเลือกทาง A วันเดียวกัน; ก่อน re-grade ทางการ ก่อน model call แรกของรอบ ต.ค. 2026 และก่อนตรึงชุดขยาย)

**กฎ (ใช้ครั้งเดียว กับทุก text column ของทุกตาราง)**
- cell ที่เก็บ string `None` (ตรงทุกตัวอักษรรวมตัวพิมพ์ใหญ่และเล็ก ไม่มีช่องว่าง) ใน CSV ของวิชา ถูกโหลดเป็น NULL
- ค่าอื่นไม่เปลี่ยน ไม่มีแถวเพิ่มหรือลบ ลำดับ physical ของแถวเหมือนฐานเดิม
- ขอบเขตกำหนดจากค่าที่เก็บในข้อมูลเท่านั้น ไม่ได้เลือก cell, คอลัมน์, item หรือโมเดลจากผล
- บนข้อมูลของวิชา กฎนี้เปลี่ยน 6 cells: PresidentMarriage.SpouseName 1 (James Buchanan), PresidentHolding.VicePresidentName 4
  (John Tyler 1841, Millard Fillmore 1850, Andrew Johnson 1865, Chester A Arthur 1881) และ PresidentHolding.RunnerUp 1 (George Washington 1789)
  ทุก cell หมายถึงค่าที่ไม่มีอยู่จริง (ไม่มีคู่สมรส ไม่มีรองประธานาธิบดี ไม่มีผู้ได้อันดับสอง)
- ไม่มี text column อื่นเก็บ 'None' และไม่มีค่าอื่นที่ทำหน้าที่เดียวกัน ตาราง Ecommerce ไม่ถูกแตะ
- CSV ของวิชาไม่แก้ กฎใช้ที่ขั้นโหลดของงานวิจัย

**เหตุผล**
1. NULL คือ mark ที่ SQL ใช้แทนการไม่มีค่าข้อมูล: ISO/IEC 9075 (SQL-92 §3.1.3 r); ข้อความตามฉบับร่าง DIS 9075 กรกฎาคม 1992) นิยาม null value ว่า
   "A special value, or mark, that is used to indicate the absence of any data value."
   และ PostgreSQL 16 Documentation (Appendix M Glossary, "Null") เขียนว่า "It represents the absence of a definite value."
   ในทฤษฎีฐานข้อมูลเชิงสัมพันธ์ (relational model) null value เป็นเครื่องมือหลักแทนข้อมูลที่ไม่ครบ และแนวทางของ Codd ใช้ three-valued logic
   (Imielinski และ Lipski, JACM 31(4):761–791, 1984, doi:10.1145/1634.1886)
2. ข้อมูลของวิชาเข้ารหัสการไม่มีค่าสองแบบ: ในแถวของ James Buchanan ค่าที่ไม่มีของ SpouseBirthDay, MarriageYear และ MarriageStatus
   เป็นช่องว่าง (โหลดเป็น NULL) แต่ชื่อคู่สมรสเก็บเป็น string 'None' กฎนี้ทำให้การเข้ารหัสเป็นแบบเดียว
3. instrument ตีความ 'None' เป็นการไม่มีค่ามาตั้งแต่ suite v0: gold ของ Q48 เขียน `RunnerUp IS NOT NULL AND RunnerUp <> 'None'`
   และ notes ระบุว่าเป็น NULL trap ที่ตั้งใจ (`suite/README.md` ลงเวลาไฟล์ 5 ส.ค. 2026; ยืนยันด้วย git ได้ตั้งแต่ commit 7 ส.ค. 2026 07:44)
   บนฐานเดิม trap นี้ไม่ทำงานเพราะ RunnerUp ไม่มี NULL
4. ที่มาของการตัดสิน: ผู้เขียนสั่งตรวจเมื่อ 13 ต.ค. 2026 ระหว่างออกแบบข้อ primary key ใหม่ (rubric: uniqueness และ nullity)
   และกำหนดให้เปลี่ยนตามนิยามของ NULL; ขอบเขตแบบ uniform (ทุก 'None') ถูกบันทึกก่อนคำนวณผลกระทบเต็ม
   (หลักฐาน: บันทึกลงวันที่ใน log การทำงานของผู้เขียน 13 ต.ค. 2026 และเวลาของไฟล์สร้างฐาน; ไม่มี commit ที่ลงเวลาก่อนการคำนวณ)

**ฐานของ record**
- ตั้งแต่ amendment นี้ ฐานของ record คือ `k3n`: สร้างจาก CSV และ `setup_db.sql` ชุดเดิมด้วย `harness/db/build_k3n.sh` (ตรวจ sha256 ของ CSV ทั้งห้าไฟล์และ `setup_db.sql` เทียบ `harness/db/k3n_inputs.sha256` ก่อนโหลด)
  (ตารางที่ไม่มี 'None' โหลดด้วย `\copy … CSV HEADER` แบบเดิม; PresidentMarriage และ PresidentHolding โหลดผ่าน staging
  ด้วย `NULLIF(col, 'None')` ตามลำดับบรรทัดของ CSV)
- fingerprint ของทุกตารางของ k3 (ก่อนและหลัง Gate 1a) และ k3n (สร้างสองครั้ง) บันทึกใน FREEZE STAMP ด้านล่างด้วย `harness/db/db_fingerprint.py`
  - การเทียบข้ามเครื่องใช้ rows, columns, md5_order_free และ mi_md5 ของ party, president, presidentholding, presidentmarriage และ ecommerce
    และ rows กับ rowhash_md5 ของ ecommerce1m
  - md5 ตามลำดับ physical, ctid และตัวนับ DML เป็นข้อมูลประกอบ เพราะต่างข้ามเครื่องได้แม้ข้อมูลเท่ากัน
- คำว่า "ข้อมูลใน DB" และ "DB ของ record" ใน R-v1.3 (AMENDMENT-7 Part C), AMENDMENT-8 และ AMENDMENT-9 หมายถึง k3n
- RQ3 (plan quality) ใช้ schema E ซึ่งกฎไม่แตะ จึงไม่เปลี่ยน; Ecommerce1M ใน k3n คัดลอกจาก k3 ของเครื่อง run-of-record ใน Gate 1a
  (`K3N_ECOM1M_FROM_REF=1`; ตรวจ rows และ rowhash_md5 เท่ากับ k3) เพราะการสร้างใหม่ด้วย `scale_ecommerce.py` ทำซ้ำไม่ได้
  (ผลขึ้นกับ PYTHONHASHSEED; ทดสอบ) amendment นี้ไม่อ้างว่า Ecommerce1M เหมือนเดือน ส.ค. ทุก byte แต่ระบุว่าคัดลอกจาก k3 ที่ Gate 1a
  พร้อม rows และ rowhash; ตารางหลักตรวจด้วย fingerprint ของ k3 ก่อนและหลัง

**สิ่งที่ไม่เปลี่ยน**
- `results/results.jsonl` ทุก byte ไม่มี model call ใหม่สำหรับ log เดือนสิงหาคม (prompt มีเพียง DDL และคำถาม SQL จึงไม่ขึ้นกับข้อมูล)
- ข้อความโจทย์ของ core 60 ข้อทั้ง EN และ TH ไม่เปลี่ยนเพราะกฎข้อมูลนี้ (การซ่อม Q27 ของรอบ ต.ค. เป็นมติ D11 แยกต่างหาก ดู AMENDMENT-7 Part C3)
- กฎ R-v1.3 (D1–D3, G1–G4, N1–N4) และสถิติตามบรรทัด 47–57 และ AMENDMENT-4
- prompt ของแขน values: value block ของ schema P และ E เหมือนกันทุก byte บนสองฐาน
  (sha256 P `32e422929b84fa12ed45d0752e45f25c8ebaa2ae077adb17d95e8f2e7fb61713`, E `5a9fb96ffd03bf08cb723f5f4f1f87161aaf642f83faf015bab6852f3255987c`;
  ทดสอบ และยืนยันด้วยการสร้างของผู้เขียนใน Gate 1a)
- answer key: v1.3n (`suite/k3n_suite_v1.3n.tsv`) = v1.3 ยกเว้น alternative ของ Q20 ที่เขียนเป็น `SpouseName IS NOT NULL` แทน `<> 'None'`
  (grade ของ log เหมือนกันทุก byte ระหว่างสองรูป) และข้อความ rationale ของ Q16, Q20, Q48
  รอบ ต.ค. ใช้ `suite/k3n_suite_v1.3n_oct.tsv` = v1.3n ที่ซ่อม Q27 (AMENDMENT-7 Part C3; มติ D11) ซึ่งไม่เกี่ยวกับกฎข้อมูลนี้

**สิ่งที่เปลี่ยนในงานที่ยังไม่รัน**
- ชุดขยาย: ลบ clause ที่อ้าง 'None' และ guard `<> 'None'` ใน X13, X14, X26 (ผลของ gold บน k3n เท่าเดิม) และแก้ metadata ที่อ้าง 'None'
  ก่อนตรึง AMENDMENT-9 และก่อน model call แรกของชุดขยาย
- grader หลาย instance (MI-1b; AMENDMENT-9): base เป็น k3n; PK1 ใช้ 5 instance, FK1 ใช้ 3 instance และ FK2 ใช้ 2 instance ที่สร้างจาก k3n;
  FK3 grade แบบ instance เดียวบน k3n

**ฐานหลักและ sensitivity (กำหนดก่อน re-grade ทางการ)**
- ฐานหลัก: ทุกการวิเคราะห์ใช้ k3n (re-grade log เดือนสิงหาคม, รอบ ต.ค. ทั้งแขน base และ values, chat check, ชุดขยาย, ข้อ primary key) ส่วนผลหลักของเล่มมาจากรอบ ต.ค. ตาม AMENDMENT-7 Part 0
- Sensitivity: การวิเคราะห์เดียวกันบน k3 (encoding เดิมของวิชา) อยู่ใน artifact
- ข้อสรุปใดที่ต่างกันระหว่างสองฐานต้องเขียนในเล่มทั้งสองแบบ

**การเปิดเผย**
- ผู้ร่าง (ผู้ช่วย AI) เห็นผลกระทบแบบทดสอบก่อนร่างฉบับนี้: exploratory ของ D7 ข้อ 4.6 (instance ที่ RunnerUp เป็น NULL ทำให้ llama −10 runs)
  และผลเต็มของกฎ uniform ต่อ log เดือนสิงหาคม ชุดขยาย และข้อ primary key
- ผู้เขียนอ่าน D7 ข้อ 4.6 ก่อนสั่งเมื่อ 13 ต.ค. 2026: ไม่ (ผู้เขียนแจ้ง 13 ต.ค. 2026 ว่าตัดสินจากนิยามของ NULL ก่อนเห็นผล);
  ผู้เขียนอ่านผลเต็มก่อนอนุมัติฉบับนี้: ใช่
- ทิศของผล (ทดสอบ; scratch; ผู้ร่างเห็นก่อนเขียน): บน log ส.ค. กฎข้อมูลร่วมกับ key v1.3n เปลี่ยนผลเฉพาะ llama3.1:8b 15 runs จากถูกเป็นผิด
  (EN Q25 ×5, EN Q48 ×5, TH Q48 ×5) และไม่มี run ใดจากผิดเป็นถูก; การเปลี่ยนระดับ item จาก key v1.2 บน k3 ไป key v1.3n บน k3n
  คือ 46 cells จากผิดเป็นถูกและ 2 cells จากถูกเป็นผิด; ผลของกฎข้อมูลอย่างเดียวภายใต้ key v1.2 มาจาก `transitions_v13n.py` ใน addendum
- ผลที่เป็นคุณต่อข้อสรุปของผู้เขียน (ทดสอบ): ไม่มีข้อสรุปเชิงคุณภาพที่กลับทิศ และสัดส่วน silent ของ frontier คงที่ (91.4%)
  ผลที่เป็นโทษ (ทดสอบ): p_Holm ของ EN−TH ของ llama3.1:8b เพิ่มจาก .0647 เป็น .1758 (n=59) และจาก .0369 เป็น .1064 (n=60)
  และ p ของ typhoon2-8b เทียบ llama3.1:8b ใน EN เพิ่มจาก .0044 เป็น .0127
- ค่าทางการจากการรันของผู้เขียนบันทึกใน addendum ลงวันที่หลัง Gate 2 และตัวเลขในเล่มใช้เฉพาะค่าทางการ
- กฎไม่ถูกแก้หลังเห็นผลกระทบ และใช้กับทุก cell ที่เข้าเงื่อนไข

**Deviation log**
| ชนิด | เหตุผล | ช่วงเวลา | แผนเดิม | สิ่งที่ทำ | ผลต่อการตีความ |
|---|---|---|---|---|---|
| เปลี่ยนการเข้ารหัสข้อมูลหลังรัน | 'None' ใน 6 cells แทนค่าที่ไม่มีอยู่จริง ขัดกับนิยาม NULL ของ SQL และกับ NULL trap ที่ออกแบบใน Q48 | หลังรัน หลัง review; ก่อน re-grade ทางการและก่อนเก็บข้อมูลเดือนตุลาคม | ฐาน k3 ตาม CSV ของวิชา | ฐานของ record เป็น k3n; ผลบน k3 รายงานเป็น sensitivity; ไม่มี model call ใหม่ | ไม่มีข้อสรุปเชิงคุณภาพที่กลับทิศ (ทดสอบ); ค่าทางการอยู่ใน addendum หลัง Gate 2; ข้อสรุปที่ต่างกันระหว่าง k3 และ k3n เขียนในเล่มทั้งสองแบบ |

**FREEZE STAMP ของกฎข้อมูล (กรอกตอน commit Gate 1b)**
- sha256 ของ `harness/setup_db.sql`, `harness/db/build_k3n.sh`, `harness/db/db_fingerprint.py`, `harness/db/k3n_inputs.sha256`
  และไฟล์ fingerprint ใน `results/db/` (k3 ก่อนและหลัง, k3n สองรอบ, cell diff และ verify):

| ไฟล์ | sha256 |
|---|---|
| `harness/setup_db.sql` | `80a8058f6f29a896f998fc28a34408e2b3e1b46a8742ca2e606caef2b2f19825` |
| `harness/db/build_k3n.sh` | `e64eaa4bb1f5d88273eab6c94734bcfa0b1c335360744fc8767541cd2ef811f9` |
| `harness/db/db_fingerprint.py` | `2cd25051ebd1f019181bb0db1cec69b09d2b2aa6cf9a7a7ab32e8b151c1d3d11` |
| `harness/db/k3n_inputs.sha256` | `4de6dec6a00628d2240cb2d3af5a0b3e4f173054a2502577b65a8494101631d6` |
| `harness/db/diffs/k3_pk_n_named.sql` | `2a74cda2e8ca97f0aeda779da13fe361058da0a24863d7fab0e5a16c224ab69f` |
| `harness/db/diffs/k3_pk_n_dup.sql` | `499e7bc3c3ea2c31d1d16fa4de686e71226e1134ab3f77a74cbc50e6540d29e8` |
| `harness/db/diffs/k3_pk_n_pnull.sql` | `583b1badb46794c930bff1cf7f0949589bb4f5b7bd62f61770af505eb21000d9` |
| `harness/db/diffs/k3_pk_n_spdup.sql` | `d30d99356a70cbb94b785a02cef77e75b5c21c8e07fdcd4f6ecbe3e4e14e8d34` |
| `harness/db/diffs/k3_fk_i_null.sql` | `50f8193c1ba21ca4be938d1acf8cf6dff07791216841bfd7332e6c46b3263c58` |
| `harness/db/diffs/k3_fk_i_orphan.sql` | `6b1f47f4c1f490dbd5b464170d3be10ab84f82922639f50e4adf77bef464f3c9` |
| `harness/db/expected/k3_fp_scratch_TESTONLY.tsv` | `84bf58432f4e45e502ac28dcfe4805a7d18908f9fb06096372f8551e54292d01` |
| `harness/db/expected/k3n_fp_scratch_TESTONLY.tsv` | `f3ea8fe31e5ea0760d89fb4ce639616e322fd6aec35d5dfc589ba378d376a875` |
| `results/db/k3_fp_before.tsv` | `48d18642021a2b986b5ef33199061987581708b2a649b44e282867e729cf03fb` |
| `results/db/k3_fp_after.tsv` | `6949e602a485354d2982dcac9f9e873f811e1a5ce2c6cbd85ad72306fa382ec7` |
| `results/db/k3n_fp_run1.tsv` | `1b4432fedf4f42702a32d7534ed2a6ae80fc8d830b1757f91d9124b85470f263` |
| `results/db/k3n_fp_run2.tsv` | `1ed258dceeb68f5d7b3eeb2c2380a1041d0eddf642199db902ea03786524c6e8` |
| `results/db/k3_vs_k3n_cell_diff.tsv` | `5d3b629e74031dafe8be1910ebdf2134b64743595d4c801f8618d6cf47bb2807` |
| `results/db/k3_vs_k3n_verify.txt` | `a45348b39939371cf9c725953f36b55d3e79f021d09303db34f672d62b6b0c64` |

- fingerprint ของ k3n รอบที่ 1 (rows, md5_order_free และ mi_md5 ต่อตาราง):

| ตาราง | rows | md5_order_free | mi_md5 | rowhash_md5 |
|---|---|---|---|---|
| party | 9 | `f5337930ead99317af870fcf32efa229` | `6250b7aa843028f85553bdb9ff168a84` | `6adf4c2c7c97b28a1fd64aba412d505b` |
| president | 45 | `94872caea01738c0251371461f0d0489` | `e1acee981170d87378b3734b209d5302` | `658c669489cf0c269715f8377ea32f9b` |
| presidentholding | 49 | `43fad2964d9c9f1ac0ac1b1019621f49` | `dc9cf90624f53415a14b4bb6af82edc0` | `645bdfe7870bab9b788bf8de9c846026` |
| presidentmarriage | 49 | `8ac8e8af82d87fd76082d5ef17c4ce54` | `97efe4cd845f5d56d1dbfff276761b40` | `abbd5871d9e6e7f673b48b4500c31df6` |
| ecommerce | 2390 | `37707d52ace94baf8a01fd02b9dd26a8` | `0779fea2d57b82e6d9c15b046411bbe8` | `e6b2c9b463da16e2bd1b11d796a46d8a` |
| ecommerce1m | 1000000 | - | - | `732ac1b720eee5e487a4d94a6f2a3aa6` |

- `suite/k3n_suite_v1.3n.tsv` sha256: `195839ec46f902901f03e90965c00bb1b78b4ef6bc970f4cabb0ed0272997366`
- PostgreSQL ของเครื่อง run-of-record: version() และ locale (datcollate, datctype, provider): `PostgreSQL 16.9 (Homebrew) on aarch64-apple-darwin24.4.0, compiled by Apple clang version 17.0.0 (clang-1700.0.13.3), 64-bit`; locale ของ k3 และ k3n: datcollate C, datctype C, provider libc (`c`), encoding UTF8
- commit, เวลา และสถานะ push: บันทึกใน addendum ของ commit Gate 2

### Part C — answer key v1.3 (มติ D7)

**C1 เหตุผลและอำนาจ**
- **อำนาจตาม prereg:** บรรทัด 62 อนุญาตให้แก้ gold ที่ผิดซึ่งพบหลังรัน โดยบันทึกเป็น amendment พร้อมเหตุผล
  และบรรทัด 70 กำหนดรูปแบบของการแก้
  - บรรทัด 62 ครอบเฉพาะการแก้ gold SQL (D1) และการขยาย acceptance set ต่อข้อ (D2)
  - กฎทั่วไป G1–G4 เปลี่ยนวิธีวัดตามบรรทัด 42 และการตัด Q27 (D3) เป็น exclusion หลังรัน ซึ่งบรรทัด 59–62 ไม่ได้ให้ไว้
    ทั้งสองเรื่องจึงบันทึกเป็น deviation ใน Part D-5 และรายงานผลตาม key v1.2 คู่กันเสมอ (C5)
- **มติผู้เขียน D7 (12 ต.ค. 2026):** สำหรับ defect ทุกข้อของ gold หรือ instrument
  ต้องมีเหตุผลที่ methodologist ยอมรับได้จึงจะไม่แก้ ถ้าไม่มี ต้องแก้
  - เหตุผล "แก้แล้วตารางเปลี่ยน" ไม่ใช้ในข้อใดเลย
- **การ audit**
  - ตรวจ gold หลังรันครบ 60 ข้อ โดยผู้ช่วย AI สามชุด (ชุดละ 20 ข้อ)
  - ผู้ช่วยอีกชุดตรวจซ้ำด้วยการรัน SQL ใหม่แยกกัน
  - ผู้เขียนพิจารณาและอนุมัติรายข้อ และผู้ตรวจคนที่สองอ่านความหมาย D2c จากข้อความโจทย์โดยไม่เห็นผลของโมเดล (รับครบ)
- **ไม่มีการเรียกโมเดลใหม่:** re-grade log เดิมทั้ง 3,600 records แบบ deterministic
  SQL ของโมเดลยังเป็น run-of-record ตามบรรทัด 61

**C2 กฎเดียว R-v1.3 (ใช้กับทุกข้อทุกภาษา; ตัดสินจากข้อความโจทย์ gold SQL และข้อมูล ไม่ใช้ผลของโมเดล)**
- **นิยาม:** คำตอบถูกเมื่อผลบน DB ของ record เป็นคำตอบของโจทย์ตามที่เขียนในภาษานั้น
- **ตรึงไว้ไม่เปลี่ยน**
  - ข้อความโจทย์ (บรรทัด 61)
  - ข้อมูลใน DB ของ record (k3n ตามกฎข้อมูล) และ log ของโมเดล
  - projection หรือชุดคอลัมน์ตาม AMENDMENT-2
  - การเทียบ NULL และ string แบบตรงตัว
  - majority of 5 และสถิติตามบรรทัด 47–57
- **แก้ key เฉพาะสามกรณี**
  - **D1** ผลของ gold ไม่ใช่คำตอบของโจทย์ คือความหมายผิด หรือผลขึ้นกับพฤติกรรมของ engine เช่น NULLS FIRST ให้แก้ gold SQL
  - **D2** gold ตรึงสิ่งที่โจทย์ไม่ได้ขอ ให้ขยาย acceptance set ให้ครบทุกแบบที่ข้อความโจทย์ยอมให้
    - (a) ลำดับแถวเมื่อโจทย์ไม่ขอ, ลำดับของแถวที่เสมอ และทิศของ tiebreak ที่โจทย์ไม่ระบุ
      ในทางกลับกัน ถ้าโจทย์ขอลำดับแต่ gold ไม่บังคับ ให้บังคับ (ข้อนี้ลดคะแนนได้อย่างเดียว)
    - (b) รูปแบบของค่า ได้แก่ ลำดับคอลัมน์, ชนิดหรือ scale ของตัวเลข, date กับ timestamp เวลาเที่ยงคืน,
      รูปแบบเดือนหรือทศวรรษ, การปัดเศษที่โจทย์ไม่ได้ขอ และเครื่องหมายของผลต่าง
      - การปัดเศษ (ใช้กับทุกข้อ): เมื่อ gold ปัดเศษที่โจทย์ไม่ได้ขอ ให้เทียบที่ความละเอียดของ gold
        คำตอบที่ไม่ปัดหรือปัดละเอียดกว่าจึงถูก ส่วนคำตอบที่ปัดหยาบกว่า gold ผิด เพราะเสียความละเอียดที่ key มี
        (ข้อที่เข้ากรณีนี้ใน v1.3 คือ Q57)
    - (c) ถ้อยคำในภาษานั้นเปิดให้อ่านเป็นหน่วย ระดับ (grain) หรือขอบเขตอื่น
    - (d) คำที่มีนิยามมาตรฐานมากกว่าหนึ่งแบบ
  - **D3** gold คืน 0 แถวบน DB ของ record ให้ตัดข้อออกจาก primary analysis และรายงานแบบคงข้อไว้เป็น sensitivity
    (เหตุผลเดียวกับ AMENDMENT-1 ที่ถือว่า gold ว่างเป็น defect และแก้ Q24 กับ Q40 ก่อนรัน
    แต่หลังรันแก้ข้อความโจทย์ไม่ได้ตาม N1 จึงตัดข้อแทน)
- **กฎทั่วไปใน grader (`grade_v13.py`; ใช้กับทุกข้อ)**
  - G1 ไม่ให้คะแนนลำดับคอลัมน์ (column permutation) แต่จำนวนคอลัมน์ต้องตรง (เกณฑ์หลัก; มติผู้เขียน 13 ต.ค. 2026 ข้อ 1)
    - ข้อยกเว้น: เมื่อโจทย์ให้คอลัมน์มีบทบาทต่างกันจนสลับแล้วความหมายเปลี่ยน ให้คะแนนลำดับภายในกลุ่มคอลัมน์ที่มีบทบาท (คอลัมน์ `col_roles` ของ suite)
    - core: Q17 (ปีเริ่ม/ปีสิ้นสุด), Q22 (ประธานาธิบดี/ผู้ได้อันดับสอง), Q28 (ประธานาธิบดี/รองประธานาธิบดี), Q35 (ปีเริ่มแรก/ปีสิ้นสุดสุดท้าย),
      Q42 (คืน/ไม่คืน), Q49 (ระยะเวลา/อันดับ) และ Q54 (รายได้รวม/ผลต่าง); ชุดขยาย: X34, X37, F7C-6 (และ FK4 ถ้าใช้ข้อสำรอง; AMENDMENT-9)
      core และชุดขยายใช้กฎเดียวกัน; ไม่รวม Q16/Q20/Q23 (ความสัมพันธ์สมมาตรและค่าบอกบทบาทเอง) และ Q58/Q59 (คอลัมน์ต่าง domain)
    - sensitivity: G1 ล้วน (`--no-col-roles`) และเทียบตามตำแหน่งทั้ง projection (`--colperm off`)
  - G2 ตัวเลขเทียบด้วยค่า ไม่ขึ้นกับชนิด (int, NUMERIC, float) หรือ scale โดยปัดที่ 6 ตำแหน่งทศนิยม (half-up)
  - G3 date เท่ากับ timestamp หรือ timestamptz เวลาเที่ยงคืนของวันเดียวกัน และไม่ให้คะแนน time-zone suffix
  - G4 ให้คะแนนลำดับแถวเฉพาะเมื่อโจทย์ภาษานั้นขอ (คำขอ top-k นับเป็นคำขอลำดับ)
    แถวที่เสมอกันบน sort key ที่โจทย์ขอสลับกันได้
- **เหตุผลที่ยอมรับได้สำหรับการไม่แก้ (ใช้กับทุกข้อเหมือนกัน)**
  - **N1** defect อยู่ในข้อความโจทย์ ซึ่งเป็น stimulus ที่โมเดลเห็นไปแล้ว
    ทำเป็น errata ของรุ่นถัดไป เว้นแต่ defect เปลี่ยนคำตอบ ซึ่งจะเข้า D2c หรือ D3
  - **N2** defect อยู่ที่ข้อมูล แต่ gold ยังถูกต่อข้อมูลที่เก็บ
    โจทย์ถามจาก DB ของวิชานี้ คำตอบจึงขึ้นกับ DB (DB-relative) และทดสอบ instance ที่แก้ข้อมูลแล้วว่าไม่เปลี่ยน grade
    (ข้อนี้ไม่ใช้กับการเข้ารหัส 'None': บน k3n การเข้ารหัส NULL เปลี่ยน grade ของ log ส.ค. 15 runs (ทดสอบ) จึงจัดการด้วยกฎข้อมูล ไม่ใช่ N2)
  - **N3** SQL ที่ผิดบังเอิญได้ผลตรงกับ gold บน DB เดียว ขณะที่ key ถูกและไม่ว่าง
    - เป็นสมบัติของ metric ที่ลงทะเบียนไว้ในบรรทัด 42
    - การสร้าง neighbor DB เฉพาะข้อที่เห็นโมเดลผ่านจะเป็นการแก้ที่ขึ้นกับผล
    - test suite เต็มรูปแบบ (Zhong et al. 2020) คือ metric ใหม่
  - **N4** ธรรมเนียมที่ลงทะเบียนก่อนรันและไม่ขัดกับโจทย์ ได้แก่ projection ตรงตัวตาม AMENDMENT-2

**C3 รายข้อ before → after (key เปลี่ยน 24 ข้อ; ไฟล์เต็มใน `suite/CHANGELOG_v1.2_to_v1.3.md`)**

จำนวนแถวและค่าในหัวข้อนี้ได้จากการรัน gold บนสำเนา scratch (ทดสอบ) selftest_v13.py ของผู้เขียนเป็นตัวยืนยัน

D1 แก้ gold SQL (3 ข้อ)
- **Q19** (gold เดิมตัดรองประธานาธิบดีที่ขึ้นตำแหน่งในปีเดียวกัน)
  - ก่อน: `SELECT DISTINCT h.VicePresidentName FROM PresidentHolding h JOIN PresidentHolding h2 ON h.VicePresidentName = h2.PresidentName WHERE h2.YearHolding > h.YearHolding;` (8 แถว)
  - หลัง: เปลี่ยน `>` เป็น `>=` (10 แถว เพิ่ม John Tyler และ Andrew Johnson ซึ่งข้อมูลแสดงการสืบทอดในปีเดียวกัน)
- **Q42** (ลำดับคอลัมน์ของ gold สวนกับลำดับในโจทย์ทั้งสองภาษา)
  - ก่อน: `SELECT Brand, SUM(CASE WHEN ReturnStatus = 'No Return' THEN 1 ELSE 0 END) AS kept, SUM(CASE WHEN ReturnStatus <> 'No Return' THEN 1 ELSE 0 END) AS returned FROM Ecommerce GROUP BY Brand;`
  - หลัง: `SELECT Brand, SUM(CASE WHEN ReturnStatus <> 'No Return' THEN 1 ELSE 0 END) AS returned, SUM(CASE WHEN ReturnStatus = 'No Return' THEN 1 ELSE 0 END) AS kept FROM Ecommerce GROUP BY Brand;`
  - ภายใต้ G1 ผลต่อคะแนนเท่ากัน การสลับนี้ทำให้ sensitivity แบบ positional ถูกต้อง ข้อนี้ยังอยู่ในชุด VG
- **Q50** (NULLS FIRST จัดประธานาธิบดีที่ไม่มีคู่สมรสเป็นอันดับหนึ่ง และ gap มีเครื่องหมาย)
  - ก่อน: `SELECT p.PresidentName, p.YearBorn - EXTRACT(YEAR FROM m.SpouseBirthDay::date) AS gap FROM President p JOIN PresidentMarriage m ON p.PresidentName = m.PresidentName ORDER BY ABS(p.YearBorn - EXTRACT(YEAR FROM m.SpouseBirthDay::date)) DESC, p.PresidentName ASC LIMIT 3;`
  - หลัง: `SELECT p.PresidentName, ABS(p.YearBorn - EXTRACT(YEAR FROM m.SpouseBirthDay::date)) AS gap FROM President p JOIN PresidentMarriage m ON p.PresidentName = m.PresidentName WHERE m.SpouseBirthDay IS NOT NULL ORDER BY gap DESC, p.PresidentName ASC LIMIT 3;`
  - เพิ่ม norm `1:abs`, sort_keys `1,0` และ alt ที่ใช้ tiebreak ชื่อ DESC

D2 ขยาย acceptance set หรือปรับการบังคับลำดับ (20 ข้อ)

| ข้อ | กฎ | v1.2 | v1.3 |
|---|---|---|---|
| Q02 | D2a | ordered ตรงตัว รวมลำดับของปีที่เสมอ | ordered, sort_keys `1` (ปีที่เสมอสลับกันได้) |
| Q04 | D2a | tiebreak ชื่อ ASC เท่านั้น | เพิ่ม alt ชื่อ DESC (EN, TH) |
| Q12 | D2a | tiebreak OrderID DESC เท่านั้น | เพิ่ม alt OrderID ASC (EN, TH); sort_keys `1,0` |
| Q20 | D2c | 49 แถว (นับแถว placeholder ของ Buchanan) | เพิ่ม alt 48 แถว; v1.3n เขียน alt เป็น `WHERE m.SpouseName IS NOT NULL` บน k3n (EN, TH) |
| Q25 | D2c | gap logic (2 แถว) | เพิ่ม alt EN ตามวงเล็บ `HAVING COUNT(DISTINCT YearHolding) >= 2` (4 แถว); TH ไม่เปลี่ยน |
| Q31 | D2c | 7 พรรคจาก President | เพิ่ม alt 9 พรรค `Party LEFT JOIN President` (EN, TH) |
| Q33 | D2c | เฉลี่ยต่อ record | เพิ่ม alt TH เฉลี่ยต่อประธานาธิบดี |
| Q39 | D2a, D2b | month เป็น timestamptz; ordered ทั้งสองภาษา | norm `0:month2024`; order_en = yes, order_th = no |
| Q46 | D2c | ต่อ record | เพิ่ม alt TH: tenure รวมต่อประธานาธิบดี |
| Q47 | D2a | tiebreak ชื่อ ASC | เพิ่ม alt EN ชื่อ DESC (TH ระบุทิศแล้ว) |
| Q49 | D2a, D2c, D2d | ไม่บังคับลำดับ; RANK ต่อ record | gold เติม `ORDER BY term_len DESC` (sort_keys `1`); alt EN: DENSE_RANK; alt TH: DENSE_RANK และแบบต่อประธานาธิบดี (RANK, DENSE_RANK) |
| Q51 | D2a | tiebreak OrderID DESC | เพิ่ม alt EN OrderID ASC (TH ระบุ "มากสุด") |
| Q52 | D2a, D2c | ไม่บังคับลำดับ; ต่อคำสั่งซื้อ 2,390 แถว | gold เติม `ORDER BY OrderDate` (sort_keys `0`); เพิ่ม alt ต่อวัน 243 แถว (EN, TH) |
| Q54 | D2b | month เป็น timestamptz | norm `0:month2024` |
| Q55 | D2a | tiebreak ชื่อสินค้า ASC | เพิ่ม alt ชื่อสินค้า DESC (EN, TH) |
| Q56 | D2d | PERCENTILE_CONT | เพิ่ม alt PERCENTILE_DISC (EN, TH) |
| Q57 | D2b | ROUND 2 ตำแหน่ง เทียบ string ตรงตัว | norm `1:round2` (เทียบที่ 2 ตำแหน่งซึ่งเป็นความละเอียดของ gold; คำตอบที่ปัด 1 ตำแหน่งยังผิด) |
| Q58 | D2a | tiebreak OrderID ASC | เพิ่ม alt OrderID DESC (EN, TH) |
| Q59 | D2a, D2b | `ORDER BY decade` (ordered ทั้งที่โจทย์ไม่ขอ) | ตัด ORDER BY ออก; unordered; norm `0:decade` |
| Q60 | D2d | ค่าเฉลี่ยรวม partial window ของ 6 วันแรก | เพิ่ม alt strict window (6 วันแรกเป็น NULL หรือไม่แสดง) (EN, TH) |

D3 ตัดข้อ (1 ข้อ; ใช้กับ suite v1.3 และ v1.3n ที่ใช้ re-grade log ส.ค.)
- **Q27:** gold คืน 0 แถวบน DB ของ record (ไม่มีลูกค้าที่สั่งซื้อสองครั้งในวันเดียวกัน)
  - คำตอบใดที่คืนผลว่างได้คะแนนถูก
  - v13_status = excluded; primary n=59; รายงาน n=60 เป็น sensitivity ของ log ส.ค.
  - ไม่ใช้ neighbor DB เพราะ TH ขอ "CustomerID และ OrderID" ไม่ได้ขอคู่ของคำสั่งซื้อ (ขัดบรรทัด 37)
    acceptance set ของ TH จึงต้องเขียนหลังเห็นผล

D11 ซ่อม Q27 สำหรับรอบ ต.ค. (มติผู้เขียน 14 ต.ค. 2026; ใช้กับรอบ ต.ค. เท่านั้น)
- **เหตุผล:** รอบ ต.ค. เป็น experiment ใหม่ด้วยวิธีเดิม (Part 0) จึงแก้โจทย์ของข้อที่ gold ว่างได้ก่อนถาม
  แบบเดียวกับ AMENDMENT-1 ที่แก้ Q24 และ Q40 ก่อนรัน รอบ ต.ค. จึง grade ครบ 60 ข้อ (100 ข้อเมื่อรวมชุดขยาย) แทนการตัด Q27
- **ข้อความ EN:** "Find pairs of orders placed by the same customer in the same month (show CustomerID and both OrderIDs; list each pair once)."
- **ข้อความ TH (ผู้เขียนเขียน; ฉบับสุดท้าย):** "หาคู่ของคำสั่งซื้อที่สั่งโดยลูกค้าคนเดียวกันในเดือนเดียวกัน (โดยให้แสดง CustomerID และ OrderID ของทั้งสองคำสั่งซื้อ และให้แสดงแต่ละคู่เพียงแค่ครั้งเดียวเท่านั้น)"
- **gold:** self-join เดิมที่เปลี่ยนเงื่อนไขวันเดียวกันเป็นเดือนเดียวกัน
  `SELECT e1.CustomerID, e1.OrderID, e2.OrderID FROM Ecommerce e1 JOIN Ecommerce e2 ON e1.CustomerID = e2.CustomerID AND date_trunc('month', e1.OrderDate) = date_trunc('month', e2.OrderDate) AND e1.OrderID < e2.OrderID;`
  - v13_status = primary, v13_rule = D11 และ gold_sql_v12 ว่าง (key v1.2 ไม่มี gold ของโจทย์ฉบับซ่อม)
  - คอลัมน์อื่นของ Q27 เหมือน suite ของ ส.ค. และไม่มี alt เพราะผู้เขียนไม่ได้บันทึกความหมายอื่นของโจทย์ใหม่
- **ผลบน k3n (ทดสอบ; อ่านเฉพาะ gold และคำตอบที่ผู้ร่างเขียนเพื่อตรวจถ้อยคำ ไม่มีคำตอบของโมเดล):** gold ได้ 6 คู่;
  คำตอบที่แสดงคู่ทั้งสองทิศได้ 12 แถว (ผิด เพราะโจทย์ให้แสดงแต่ละคู่ครั้งเดียว); การอ่านเป็น "ภายใน 30 วัน" ได้ 9 แถว (ผิด);
  การเทียบเดือนด้วย EXTRACT(MONTH) โดยไม่ดูปีได้ 6 แถวเท่ากับ gold เพราะข้อมูลทั้งหมดอยู่ในปี 2024; คำตอบที่สลับลำดับ OrderID
  ทั้งสองคอลัมน์ยังถูกตาม G1; gold เดิมได้ 0 แถว
- **ไฟล์:** `suite/k3n_suite_v1.3n_oct.tsv` คือ `suite/k3n_suite_v1.3n.tsv` ที่แทนเฉพาะบรรทัดของ Q27 (บรรทัดอื่น 59 บรรทัดและ header
  เหมือนทุก byte) สร้างและตรวจซ้ำด้วย `build_oct_core_suite.py` จากไฟล์ซ่อม Q27 (sha256 ของสามไฟล์อยู่ใน FREEZE STAMP)
- **กฎของสองรอบ**
  - re-grade log ส.ค. ใช้ suite ของ ส.ค. ซึ่งคง Q27 เดิมเป็น excluded (D3 ข้างบน)
  - การเทียบ ส.ค.–ต.ค. และ drift ใช้ 59 ข้อที่ถามเหมือนกันในสองรอบ
  - prompt ของแขน base ของรอบ ต.ค. เหมือน ส.ค. ทุก byte ยกเว้น call ของ Q27 (Part 0 ข้อ 11)
  - RQ3 ของรอบ ต.ค. ใช้ gold ฉบับซ่อม และ RQ3 ของ log ส.ค. ไม่เปลี่ยน (Q27 มี eff = no จึงไม่อยู่ใน RQ3 ทั้งสองรอบ)
- **selftest:** `harness/selftest_v13n.py` ตรวจ suite ทั้งสองฉบับ: suite ของ ส.ค. มี Q27 เป็นข้อ excluded ข้อเดียว (59 primary)
  และ suite ของรอบ ต.ค. ไม่มีข้อ excluded (60 primary); ข้อที่ต่างจาก v1.2 ได้มีเฉพาะข้อในทะเบียน `core_repaired`
  ของ `harness/suite_columns.json`

metadata ของ G4 (ไม่นับเป็นการแก้ key รายข้อ)
- เพิ่ม sort_keys ให้ข้อ ordered ที่เหลือ ได้แก่ Q32 (`1,0`), Q36 (`1`), Q38 (`1,0`) และ Q45 (`1`)
- ใน memo D7 ไม่มี run ใดของสี่ข้อนี้เปลี่ยนผลเพราะ metadata นี้ (ทดสอบ)

ตัวจำแนก VG
- เงื่อนไข relevance ของ Q48 ตัดสินใน Part B2.1 ไม่ใช่การแก้ key

**C4 ข้อที่คงไว้พร้อมเปิดเผย และข้อที่ไม่ต้องทำ**

| ข้อ | ประเด็น | การตัดสิน | เหตุผล |
|---|---|---|---|
| Q60, Q57, Q58, Q52, Q41, Q43 | คำตอบที่พ่วงคอลัมน์ที่โจทย์ไม่ได้ขอ | คงไว้; รายงาน extra-column tolerance เป็น exploratory | N4 และ tolerance นี้จะให้คะแนน run ที่ผิดจริง |
| Q55 | วงเล็บไม่ระบุ Category | คงไว้; errata | N4 (AMENDMENT-2 ระบุ Q55 ไว้ในธรรมเนียม (a)) |
| Q21, Q25 (llama TH), Q38 (llama TH), Q58 | logic ผิดแต่ได้ผลตรงบน DB เดียว | คงไว้; เปิดเผย; instance เพื่อนบ้านเป็น exploratory | N3 |
| Q48 | บน k3 NULL trap ไม่ทำงาน (RunnerUp ไม่มี NULL); บน k3n trap ทำงาน (RunnerUp ของ Washington 1789 เป็น NULL) และถ้อยคำ TH | คงไว้; เปิดเผย; errata ใน CHANGELOG v1.2→v1.3 เรื่องนี้ไม่เป็นจริงบน k3n (CHANGELOG v1.3→v1.3n) | N1 |
| Q01, Q02, Q07, Q08, Q10, Q18, Q39/Q54 (ตัวกรองปี), Q41 (HAVING >100), Q44, Q47/Q51/Q55 (tiebreak), Q55 (การรวมยอด) | เงื่อนไขขอบที่ DB เดียวแยกไม่ออก | คงไว้; หนึ่ง clause ใน Limitations | N3 (และ N1 สำหรับ Q41) |
| ข้อมูล President และ OrderID (Q19, Q22, Q24, Q28, Q09, Q16, Q18, Q20, Q07) | ชื่อและข้อเท็จจริงทางประวัติศาสตร์ไม่ตรง, การสมรสที่ขาด, OrderID ซ้ำ 3 ค่า | คงไว้; บันทึกใน DATA_PROVENANCE; คำตอบขึ้นกับ DB | N2 |
| Q24 (ระบุแยกเพราะงานขยาย suite ส่งมาให้ D7 ตัดสิน) | ชื่อ VP เก็บแบบสั้น ('Chester Arthur', 'Harry Truman', 'Lyndon Johnson', 'George Bush') ไม่ตรงกับ PresidentName ('Chester A Arthur', 'Harry S Truman', 'Lyndon B Johnson', 'George H W Bush') gold แบบ anti-join ตรงตัวจึงนับสี่คนนี้ว่าไม่เคยเป็น VP | คงไว้; เปิดเผยใน DATA_PROVENANCE | N2: ชื่อเป็นตัวระบุใน DB ของวิชา คำตอบที่คาดในวิชาคือ anti-join ตรงตัว และ instance ที่ normalize ชื่อแล้วไม่เปลี่ยน grade ของ run ใดนอกจาก Q19 (ทดสอบ; memo D7 §4.9) |
| Q14 | EN ก็ต้องทำ value grounding | คงไว้; footnote และรายงาน VG แบบมีและไม่มี Q14 | gold ถูก; ประเด็นอยู่ที่การจัดกลุ่มข้อ |
| คำผิดและถ้อยคำไทย (Q07, Q18, Q27, Q33, Q35, Q37, Q43, Q45, Q47), Q08 | stimulus ที่โมเดลเห็นแล้ว | errata ของรุ่นถัดไป | N1 |
| Q16 | แถวของ Buchanan ที่ไม่มีคู่สมรส (SpouseName เป็น NULL บน k3n) | คงไว้ | N2: โจทย์ถามประธานาธิบดีทุกคน แถวนี้จึงเป็นคำตอบที่ถูก |
| Q23, Q32, Q47 (LEFT JOIN Party) | ตรวจแล้วไม่ใช่ defect | ไม่ทำ | ดูเหตุผลรายข้อใน memo D7 |

**C5 Primary, sensitivity และการรายงานทั้งสองฉบับ (กำหนดก่อน re-grade)**
- **Primary (รอบ ต.ค.; Part 0):** key v1.3n บน k3n กับ suite รอบ ต.ค. (Q27 ฉบับซ่อม; มติ D11), n=60, G1 เปิดพร้อมข้อยกเว้นคอลัมน์มีทิศทาง (C2)
  - ใช้กับทุกตารางและทุกประโยคในเล่มที่มาจากแขน base ของรอบ ต.ค.
  - เป็น key ของ Part A, Part B, AMENDMENT-8 และ AMENDMENT-9
- **log ส.ค. (ข้อมูลรอง):** key v1.3n บน k3n กับ suite ของ ส.ค., n=59 (Q27 เดิมเป็น excluded ตาม D3)
- **Sensitivity ที่รายงานคู่**
  1. key v1.2 ตามที่ preregister บน log ส.ค. (n=60; `results/graded.csv` เดิม)
  2. log ส.ค. ที่คง Q27 เดิม (n=60)
  3. เทียบคอลัมน์ตามตำแหน่ง (G1 ปิด) และ G1 ล้วนที่ไม่ใช้ข้อยกเว้นคอลัมน์มีทิศทาง ทั้งสองรอบ
  4. ฐาน k3 ด้วย key v1.3 (artifact เท่านั้น; ครอบ 59 ข้อที่ถามเหมือนกัน เพราะ suite v1.3 ไม่มี Q27 ฉบับซ่อม)
- **กฎการรายงาน:** ข้อสรุปใดที่ต่างกันระหว่าง primary กับ sensitivity ชุดใดชุดหนึ่ง ต้องเขียนในเล่มทั้งสองแบบ
  - เช่น นัยสำคัญหลัง Holm ของ EN−TH ของโมเดลใดใน log ส.ค. ที่ขึ้นกับ Q27
- **ตารางเต็มทุกชุด:** อยู่ใน artifact; suite v1.2, graded.csv และ paper/generated ฉบับเดิมเก็บไว้ไม่แก้
- **RQ3 cost reference (ตัดสินแล้ว; มติผู้เขียน 13 ต.ค. 2026 ข้อ 6):** gold v1.2 ที่คำนวณใหม่บนฐาน k3n
  - รันบนสำเนา `k3n_rq3` ของ k3n (สร้างด้วย `createdb -T k3n`, เฟส indexed แล้ว noindex แล้วลบ) เพื่อไม่แตะ catalog และ statistics ของ k3n
  - ผลหลักใช้ SQL ตัวแทนจากแขน base ของรอบ ต.ค.; ผลรองใช้ log ส.ค. (กฎเลือก SQL ตัวแทนเดิม: cell ที่ถูกโดย majority → record แรกที่ถูก)
  - ข้อที่ซ่อมตามมติ D11 ใช้ gold ฉบับซ่อมในรอบ ต.ค. และ gold เดิมใน log ส.ค. (`harness/plan_quality.py` รับ suite รอบ ต.ค. ผ่าน `--d11-gold-suite`);
    Q27 มี eff = no จึงไม่อยู่ในชุดข้อของ RQ3 และ reference gold ของ 11 ข้อ eff ไม่เปลี่ยน (ทดสอบ)
- **alt keys ที่ไม่มีผลต่อ log ส.ค. (ตัดสินแล้ว: คงไว้):** tiebreak กลับทิศ, Q31, Q20, Q56, Q60 และ DENSE_RANK
  - เหตุผล: รอบ ต.ค. และ chat check สร้างคำตอบใหม่ และการตัดสินนี้ทำก่อนมีคำตอบใหม่ใดๆ
  - alt ใดถูกตัดเฉพาะเมื่อผู้ตรวจคนที่สองไม่รับความหมายนั้น (C6 ข้อ 2)

**C6 ขั้นตอน**
1. ผู้เขียนตัดสินแล้วทุกจุด ได้แก่ G1, reading ของ D2c, Q27 (D3 สำหรับ log ส.ค. และ D11 สำหรับรอบ ต.ค.), ชุด VG (B2.1),
   การนับใน abstract (B2), clause เรื่อง gap ใน abstract (A9), alt keys และ RQ3 reference (ค่าอยู่ใน FREEZE STAMP)
   - FREEZE STAMP บันทึกว่าผู้เขียนตัดสินหลังจาก memo D7 ซึ่งมีตัวเลขทดสอบเข้าถึงได้ในโฟลเดอร์โครงการ แต่ผู้เขียนไม่ได้อ่านตารางผลรายโมเดลใน memo
2. ผู้ตรวจคนที่สองของ reading ของ D2c (Q20, Q25 EN, Q31, Q33 TH, Q46 TH, Q49 TH และ Q52) อ่านจากข้อความโจทย์โดยไม่เห็นผลของโมเดล
   และรับทุก reading จึงไม่มี alt ใดถูกตัด
   - ห้ามเปลี่ยน reading หลังมีตัวเลขทางการ
3. คัดลอกไฟล์เข้าโปรเจกต์ใน Gate 1a (ขั้นคัดลอกของ RUNBOOK v2) ได้แก่
   - `suite/`: k3n_suite_v1.3n.tsv (suite ของ ส.ค.), k3n_suite_v1.3n_oct.tsv (suite ของรอบ ต.ค.; มติ D11), k3_suite_v1.3.tsv,
     CHANGELOG_v1.2_to_v1.3.md และ CHANGELOG_v1.3_to_v1.3n.md (หัวข้อ 5 เป็นมติ D11)
   - `harness/`: grade_v13.py และ selftest_v13.py (ฉบับอ้างอิงไม่แก้), grade_v13n.py, selftest_v13n.py, selftest_mi.py, parity_grader.py,
     parity_check_v13.py (สำเนาไม่แก้), suite_columns.json, สคริปต์ของ runner และการวิเคราะห์ (รวม plan_quality.py, make_figures.py,
     consistency_aug_oct.py และ make_vg_sets.py), build_ext_suite.py และ answers_mi_PREREG_v2_frozen.py
   - `harness/db/` (สร้าง k3n, fingerprint และ MI instance) และ `harness/chatapp/` (kit ของ AMENDMENT-8)
   - `suite/ext_inputs/`: input ของตัวสร้างชุดขยายที่ไม่มีชื่อบุคคล
   - เครื่องมือของ `kst_rev/` ที่ต้องตรึงถูกคัดลอกเข้า `harness/` เพราะ `kst_rev/` ไม่อยู่ใน git ยกเว้นไฟล์ที่อยู่นอก git ต่อไป ได้แก่
     ตัวสร้าง suite ของรอบ ต.ค. (`build_oct_core_suite.py`) และไฟล์ซ่อม Q27: sha256 ของไฟล์เหล่านี้อยู่ใน FREEZE STAMP
     ของ amendment นี้พร้อม label กลาง และไฟล์แนบใน artifact;
     transitions_v13.py, paper_numbers_v13.py และ flagged_gap_v13.py ถูกแทนด้วย transitions_v13n.py และ paper_numbers_v13n.py;
     vg_numbers_v13.py ไม่ใช้ (อ่านผลของโมเดล)
   - `chat_draw_check_v13.py` ใช้กฎสุ่มแบบเดิม (ต่อ tier) ที่ AMENDMENT-8 ถอนแล้ว ห้ามใช้สร้างรายการข้อทางการ (เปิดเผยใน artifact เท่านั้น)
4. ตรวจก่อน commit (ไม่สร้างตัวเลขผลใหม่)
   - `selftest_v13n.py` บน v1.3n/k3n (suite ของ ส.ค. และ suite ของรอบ ต.ค.) และ `selftest_v13.py` บน v1.3/k3 ต้อง PASS ได้แก่
     ข้อความโจทย์ตรง v1.2 (ยกเว้น Q27 ของ suite รอบ ต.ค. ซึ่งเป็นข้อเดียวในทะเบียนข้อที่ซ่อม; มติ D11), ทุก key execute ได้ deterministic
     และให้คะแนนตัวเองถูก และไม่มี primary gold ว่าง
   - suite ของรอบ ต.ค. ต้องเท่ากับ suite ที่สร้างใหม่จาก suite ของ ส.ค. และไฟล์ซ่อม Q27 ทุก byte (`build_oct_core_suite.py --check`)
   - `grade_v13n.py --legacy` บนฐาน k3 (`dbname=k3`) บวก `parity_check_v13.py` ต้องได้ผลตรง `results/graded.csv` ครบ 3,600/3,600
   - `parity_grader.py` ต้องได้ IDENTICAL ทุกโหมดระหว่าง grade_v13.py และ grade_v13n.py (พิมพ์เฉพาะ hash ไม่พิมพ์ความแม่นยำ)
5. commit และ push ใน Gate 1b
6. re-grade ทางการของ log ส.ค. (Gate 2; ข้อมูลรองตาม Part 0)
   - บน k3n ด้วย v1.3n: `results/v13n/graded_v13n.csv`, `graded_v13n_withQ27.csv`, `graded_v13n_positional.csv`
     และ `graded_v12_on_k3n.csv` (ขั้นกลางของ transitions)
   - sensitivity บน k3 ด้วย v1.3: `results/v13/graded_v13.csv`
   - grade ของรอบ ต.ค. (ข้อมูลหลัก) ทำใน Gate 3 ด้วย suite รอบ ต.ค. (มติ D11): `results/rc1/graded_rc1.csv` (n=60),
     `graded_rc1_positional.csv` และ `graded_rc1_nocolroles.csv`
7. สร้างผลปลายน้ำใหม่ทั้งหมดด้วย `--arm base`
   - ตารางหลักของเล่ม (Gate 3): analyze.py และ analyze_typhoon.py บน `graded_rc1*.csv` (n=60, positional และ G1 ล้วน),
     phi_tableiv.py, empty_split_v13.py, plan_quality.py ทั้งสองเฟส, analyze_log_v13.py, make_tables.py และ make_figures.py
     ลง `results/rc1/base60/` และ `paper/generated/`
   - ชุดเดียวกันบน log ส.ค. (Gate 2) ลง `results/v13n/` เท่านั้น ไม่เขียน `paper/generated/`
   - make_figures.py: เล่มใช้เฉพาะ fig_tiers; สคริปต์ยังเขียน fig_slope.pdf จาก input แขน base ของรอบ ต.ค. จนกว่า Gate 4 จะตัด `\includegraphics`
   - `paper/generated` เดิมคัดลอกเก็บไว้ที่ `paper/generated_v12` ก่อนเขียนทับใน Gate 3
8. งานปลายน้ำทุกงานใช้ key v1.3n บน k3n ได้แก่ Part A, Part B, AMENDMENT-8, AMENDMENT-9 และตาราง CI ของ D8

**C7 การเปิดเผยและทิศของผล**
- **ช่องทางที่ตรวจพบ:** defect บางข้อถูกตรวจพบจากผลของโมเดล เช่น Q50 ที่ไม่มีโมเดลใดผ่าน
  แต่การตัดสินแก้ทุกข้อใช้ข้อความโจทย์ gold และข้อมูลเท่านั้น
- **ตัวเลขที่ผู้ร่างเห็น (ทดสอบ):** re-grade log ด้วย key v1.3 บนสำเนา scratch
  - ระดับ run: 230 runs จากผิดเป็นถูก และ 3 runs จากถูกเป็นผิด
  - ระดับ item: 47 cells จากผิดเป็นถูก และไม่มี cell ใดจากถูกเป็นผิด
  - บน k3n ด้วย key v1.3n (ทดสอบ): ระดับ item 46 cells จากผิดเป็นถูก และ 2 cells จากถูกเป็นผิด
    (ความต่างจาก k3 มาจาก llama3.1:8b สาม cells ได้แก่ EN Q25, EN Q48 และ TH Q48)
  - ผู้ร่างเห็นผลรายโมเดลและรายข้อด้วย (memo D7)
- **ทิศของกฎ**
  - G1 ช่วยโมเดล local เป็นหลัก ส่วน D2b และ D2c ช่วยโมเดล frontier เป็นหลัก
  - ส่วนของ D2a ที่บังคับลำดับ (Q49, Q52) ลดคะแนนได้อย่างเดียว
  - D3 ตัด cell ที่ได้คะแนนถูกออก 8 cells
  - Q19 ทำให้ gemini-flash 3 runs จากถูกเป็นผิด
  - Q50 เลือกความหมายที่ทำให้ 25 runs ของ frontier ยังผิด (ทั้งหมดทดสอบ)
- **ตัวเลขทางการ:** มาจากการรันของผู้เขียนเท่านั้น

**C8 ข้อความในเล่มที่ต้องแก้ตาม Part C (correctness)**
- บรรทัด 180–183 tiebreak clause
- บรรทัด 196–201: "calendar conventions stated in-item" ไม่จริงสำหรับ Q08 และ Q29 และคำว่า "requires" (B2.1)
- บรรทัด 252–262: self-test 60/60 พิสูจน์ได้เฉพาะ executability กับ determinism และ "five dated amendments"
- บรรทัด 307–316: คำบรรยายการให้คะแนนต้องตรงกับ grade_v13.py และ "on the run-of-record database"
- บรรทัด 416–418: "bit-stable" (B4)
- ประโยคที่มีตัวเลขทุกประโยคตามรายการใน memo D7 §6.4

---

### Part D — Deviation log ที่ทราบแล้ว (รูปแบบตาม Willroth & Atherton 2024)

ทุกรายการมีหกช่อง: ชนิด, เหตุผล, ช่วงเวลา, แผนเดิม, สิ่งที่ทำ และผลต่อการตีความ

**D-1 CI ใน Table IV เป็นแบบ unpaired (มติ D8 ทาง A)**
- **ชนิด:** implementation ของสถิติไม่ตรงกับที่ลงทะเบียน
- **แผนเดิม:** บรรทัด 50–52 "Δaccuracy พร้อม Newcombe paired CI"
- **สิ่งที่เกิด**
  - `newcombe_paired()` ใน `harness/analyze.py` ตั้ง phi = 0
    interval ทุกแถวของ Table IV ในเล่มที่ส่งจึงเป็น Newcombe hybrid-score interval สำหรับสัดส่วนอิสระ (unpaired)
  - ขณะที่ §IV และ caption เรียกว่า paired
- **ช่วงเวลา:** มีอยู่ตั้งแต่ analyze.py ฉบับแรก (7 ส.ค. 2026) และพบเมื่อ 8 ต.ค. 2026 (self-assessment 3.1)
- **สิ่งที่ทำ (ทาง A)**
  - คงสูตรเดิม และเปลี่ยน label ใน §IV และ caption เป็น
    "Newcombe hybrid-score interval without the paired correlation correction (conservative)"
  - เพิ่มหนึ่ง clause ในเล่มว่าต่างจาก prereg ที่ระบุ paired interval และบันทึกเป็น deviation ใน artifact (ตามข้อแนะนำ D8 ทาง A)
  - ตัวเลขใน Table IV สร้างใหม่จาก key v1.3 (Part C) ด้วยสูตรเดิม
    ทาง A ในมติ D8 หมายถึงคงสูตร ตัวเลขเปลี่ยนเพราะ Part C เท่านั้น
  - p ของ exact McNemar และ Holm ไม่เกี่ยวกับรายการนี้
- **เงื่อนไขของคำว่า "conservative" (ตรึงก่อน re-grade)**
  - interval แบบไม่แก้ pairing กว้างกว่าแบบ paired เฉพาะเมื่อความถูกใน EN กับ TH มีสหสัมพันธ์บวก
  - ใช้คำว่า "(conservative)" ได้เมื่อ phi ของตาราง 2×2 ระดับ item ไม่ติดลบในทุกแถวของ Table IV จากผลทางการ
  - ถ้ามีแถวใด phi ติดลบ ให้ใช้ "(not corrected for pairing)" แทน และเปิดเผยแถวนั้น
  - แถวที่ phi ไม่นิยามเพราะ margin เป็นศูนย์: ตั้ง phi = 0 (covariance เป็นศูนย์พอดีเมื่อ margin คงที่) และใส่ footnote
    "phi undefined (zero margin), set to 0"; ป้าย "(conservative)" ยังใช้ได้ถ้าแถวอื่นไม่ติดลบ; ตรวจ Newcombe (1998) กับต้นฉบับก่อนอ้าง
  - ผู้เขียนคำนวณ phi ด้วย `harness/phi_tableiv.py` ที่ตรึงใน Gate 1b บน `results/rc1/graded_rc1.csv` กับ `--arm base` และ suite รอบ ต.ค. (ผลหลัก; n=60 ตามมติ D11)
    และบน `results/v13n/graded_v13n.csv` (ผลรอง)
- **เหตุผลที่ไม่เปลี่ยนเป็น paired:** การเปลี่ยนวิธีหลังได้ review ไปในทิศที่ทำให้ผลดูแรงขึ้นเป็นการเลือกที่ขึ้นกับผล
  (ทดสอบ: สูตร paired ให้ lower bound มากกว่า 0 ใน 5/6 โมเดลภายใต้ key v1.2) ทาง A คงทิศอนุรักษ์และเปิดเผย
- **ผลต่อการตีความ**
  - interval กว้างกว่าแบบ paired เมื่อความถูกใน EN กับ TH มีความสัมพันธ์บวก
  - ข้อสรุปเชิงอนุมานใช้ McNemar กับ Holm อยู่แล้ว
  - ในเล่ม CI ใช้บรรยายขนาดผลเท่านั้น

**D-2 แถว 'Credit Card' ใน Table I และการแปลค่านี้**
- **ชนิด:** การแปลไม่ตรงตัวอย่างใน protocol และการจัดหมวดในตารางผิด
- **แผนเดิม:** บรรทัด 35–36 ยก 'Credit Card' เป็นตัวอย่าง named entity ที่ให้ทับศัพท์หรือคงภาษาอังกฤษ
- **สิ่งที่เกิด**
  - โจทย์ไทยของ Q13 ใช้ "บัตรเครดิต" ซึ่งเป็นคำแปล (คำไทยประสมคำยืม) ไม่ใช่การทับศัพท์ชื่อเฉพาะ
  - Table I ของเล่มจัดแถวนี้ไว้ใต้หมวด "Thai-script name" (หมวดเดียวกับ เวอร์จิเนีย)
- **ช่วงเวลา:** คำว่า "บัตรเครดิต" อยู่ในโจทย์ไทยของ Q13 ตั้งแต่ suite v1 (6 ส.ค. 2026) จนถึง v1.2;
  พบเมื่อ 8 ต.ค. 2026 (self-assessment 3.7)
- **สิ่งที่ทำ**
  - ย้ายแถวไปหมวด "Translated value" ใน Table I
  - ไม่แก้ข้อความโจทย์ (N1)
- **ผลต่อการตีความ:** ไม่กระทบการให้คะแนน
  - Q13 เป็น VG ทั้งในกรณีแปลและกรณีทับศัพท์ เพราะ literal `'Credit Card'` ไม่ปรากฏในโจทย์ไทยทั้งสองแบบ
  - tag `value_translated` (บรรทัด 38) ต้องตรวจให้ตรงกับการแปลจริง

**D-3 เวลาที่เพิ่ม Typhoon เข้า roster (มติ D9)**
- **ชนิด:** เพิ่มโมเดลระหว่างเก็บข้อมูล นอก roster ที่ลงทะเบียน
- **แผนเดิม:** roster 5 โมเดล
  - preregistration_v0 (mtime 6 ส.ค. 2026 19:29:27) และ FROZEN (สร้าง 6 ส.ค. 2026 21:21:07 ตาม file birth time)
  - ได้แก่ GPT mini-class, Gemini Flash, Claude Sonnet-class, llama3.1:8b และ qwen2.5-coder:7b
- **บันทึก (จากบันทึก; ICT; ts ของ log เป็นเวลาท้องถิ่น; ผู้ช่วยอ่านจาก git, file timestamp และ log; ผู้เขียนไม่ได้ตรวจซ้ำทีละรายการ)**
  - 6 ส.ค. 22:01:37: model call แรก (gemini-flash smoke)
  - 7 ส.ค. 07:15–07:35: llama31-8b และ qwen25-coder-7b เก็บครบ
  - 07:44:43: commit แรก fd2e116 ซึ่งยังมี 5 โมเดล
  - 07:50:48: commit 45d1bc1 "ollama arms complete (1200 records, dev-preview graded)"
    - ผลของ preview ไม่ถูกเก็บในไฟล์หรือ commit ใด
  - 09:01–10:07: claude-sonnet เก็บครบ (HTTP 400 ระหว่าง 08:07–08:24 ตาม AMENDMENT-3)
  - 10:10–11:24: gemini-flash เก็บครบ ถึงจุดนี้ preregistered arms ครบ 4 ใน 5 แขน
  - 11:25:40: เรียก typhoon2-8b ครั้งแรก ได้ 404 ทั้ง 1,200 ครั้ง
    - เวลานี้เป็นขอบบนของเวลาตัดสินใจเพิ่ม Typhoon
  - 14:46:33–14:57:27: typhoon2-8b เก็บครบ
  - 15:08:29: commit 2f8db3d บันทึก AMENDMENT-3 และ AMENDMENT-4
  - 16:49:41–17:08:35: gpt-mini เก็บครบเป็นแขนสุดท้าย
  - 17:26: เขียน graded.csv (grade ของ record บน PostgreSQL)
  - 13 ส.ค. 18:08: เพิ่ม paired McNemar ระหว่าง typhoon2-8b กับ llama3.1:8b (commit 1281512) ซึ่งไม่อยู่ใน prereg
- **สิ่งที่ทำ**
  - เล่มเปิดเผยหนึ่งประโยคว่า roster ที่ลงทะเบียนมี 5 โมเดล และ Typhoon ถูกเพิ่มด้วย amendment ระหว่างเก็บข้อมูล
    หลังเก็บ 4 ใน 5 แขน และหลัง preview ของ local สองแขน แต่ก่อนแขนสุดท้าย ก่อนการ grade ของ record
    และก่อนการวิเคราะห์ยืนยันใดๆ
  - contrast ทุกตัวของ Typhoon รวม paired McNemar กับ base เป็น exploratory
  - timeline เต็มอยู่ใน artifact
- **ผลต่อการตีความ**
  - การวิเคราะห์ของ 5 โมเดลที่ลงทะเบียนไม่เปลี่ยน ยกเว้นขนาด family ของ Holm
    AMENDMENT-4 กำหนด Holm ข้าม 6 โมเดล ซึ่งเข้มกว่าข้าม 5 จึงอนุรักษ์สำหรับ 5 โมเดลเดิม
  - ข้อความ "preregistered evaluation of six models" ในเล่มต้องแก้
- **ความต่างระหว่างบันทึกกับความจำของผู้เขียน (ใช้บันทึกเป็นหลัก) (ผู้เขียนตรวจแล้ว 13 ต.ค. 2026; ใช้บันทึกเป็นหลักตามมติ D9)**
  1. **ตรงกับบันทึก**
     - ผู้เขียนกำหนดจำนวนโมเดลเองตั้งแต่ต้น (roster 5 โมเดล) และ AMENDMENT-4 เพิ่มเพียงหนึ่งตัว (capped ที่ 1)
     - Typhoon ถูกเพิ่มก่อนผลทางการ ได้แก่ ก่อนการ grade ของ record ก่อนตารางใดๆ และก่อน draft ของเล่ม
     - DeepSeek ไม่เคยอยู่ใน roster หรือ models.json ฉบับใด
  2. **ต่างจากบันทึก:** "ollama มาพร้อมกับ Typhoon"
     - llama3.1:8b และ qwen2.5-coder:7b อยู่ใน roster ตั้งแต่ v0 (6 ส.ค.) และเป็นแขนแรกที่เก็บครบ
     - Typhoon ถูกเพิ่มทีหลังเพียงตัวเดียว
     - ที่มาที่เป็นไปได้ของความจำ: Typhoon รันผ่าน Ollama และการ import GGUF เป็นงาน Ollama แยกในวันเดียวกัน
  3. **ต่างจากบันทึกบางส่วน:** "ตอนแรกใช้ Claude, GPT, Gemini"
     - ใน v0 ทั้งห้าโมเดลอยู่ใน roster พร้อมกัน
     - ลำดับการเก็บจริงคือ gemini (smoke) → llama → qwen → claude → gemini → typhoon → gpt
  4. **ยืนยันไม่ได้จากบันทึก:** "เพิ่ม Typhoon ก่อนผลออก" ในระดับข้อมูล
     - การตัดสินใจเกิดหลังเก็บ 4 ใน 5 แขน และหลัง preview ของ local สองแขน
     - ผู้เขียนแจ้งเมื่อ 12 ต.ค. 2026 ว่าไม่ได้เปิดดูผล preview และตัดสินใจเพิ่ม LLM ไทยเพราะโจทย์เป็นภาษาไทย
       บันทึกยืนยันหรือหักล้างข้อนี้ไม่ได้
     - เหตุผลที่บันทึกใน AMENDMENT-4 คือ matched pair กับ llama31-8b และการตอบคำถามเรื่องโมเดลไทยของ reviewer เวทีไทย
  5. **ไม่มีร่องรอยในบันทึก:** การพิจารณา DeepSeek ก่อน 6 ส.ค.
     - บันทึกมีเพียง AMENDMENT-4 (7 ส.ค.) ซึ่งยก DeepSeek, Doubao และ SEA-LION ไปเป็น Future Work
     - qwen2.5-coder (จากทีม Qwen ของ Alibaba) อยู่ใน roster ตั้งแต่ v0

**D-4 รายการอื่นที่ทราบแล้ว**

| รายการ | แผนเดิม | สิ่งที่เกิด | สิ่งที่ทำ | ผลต่อการตีความ |
|---|---|---|---|---|
| stability | บรรทัด 53 "unanimity rate (3/3 ตรงกัน)" | ใช้ 5 runs ตามบรรทัด 26–28 | บันทึกว่าบรรทัด 53 พิมพ์ผิด; วิเคราะห์ใช้ 5/5 | ไม่มี |
| จำนวนข้อ eff | บรรทัด 44 "12 ข้อ" | suite มี eff = yes 11 ข้อ (Q12, Q14, Q36, Q38, Q39, Q45, Q51, Q52, Q53, Q55, Q60) ในทุกรุ่นตั้งแต่ v0 ถึง v1.3 (ตรวจระหว่างทบทวน) | บันทึกตามจริง; RQ3 ใช้ 11 ข้อ | ไม่มี |
| Typhoon vs base | ไม่อยู่ใน prereg | เพิ่มเมื่อ 13 ส.ค. 2026 (1281512) | ติดป้าย exploratory (D-3) | abstract ต้องลดระดับ claim |
| เวลา commit ของ AMENDMENT-3/4 | amendment ต้องอยู่ก่อนเหตุการณ์ | commit 15:08:29 หลัง claude 400 errors (08:07–08:24) และหลัง typhoon เก็บครบ (14:57:27) | บันทึกตามจริง; ฉบับใหม่ใช้ Gate ที่บังคับ push ก่อน | เวลาที่เขียนข้อความ amendment ยืนยันจาก git ไม่ได้ |
| เวลา freeze | prereg ก่อน call แรก | commit แรก (07:44:43) อยู่หลัง 1,214 records ที่สำเร็จ (gemini-flash smoke 14, llama 600, qwen 600; จากบันทึก ผู้ช่วยนับ); วัน freeze ยืนยันได้จาก file timestamp เท่านั้น | เล่มเขียนตามหลักฐานที่มี (TEXTS_D4_D9_D7) | ห้ามอ้างว่า git ยืนยันเวลา freeze |
| จำนวน amendment | เล่มเขียน "five dated amendments" | ณ วันส่งมีหกฉบับ (AMENDMENT-6) | แก้ข้อความในเล่มตาม index | ไม่มี |
| ความเสถียรของ local | AMENDMENT-3 "deterministic โดยพิสูจน์แล้ว 60/60 ทุกช่อง" | SQL text ต่างกันในบาง cell (ทดสอบ: 6/360) แม้ grade เอกฉันท์ | ตัดสินตามผลของ B4 | "bit-stable" ต้องแก้ถ้า B4 ยืนยัน |
| answer key หลังรัน | key v1.2 | key v1.3 (Part C) | primary v1.3; รายงาน v1.2 คู่กัน | ตาม Part C5 |

**D-5 วิธีวัดและ exclusion ที่เปลี่ยนหลังรัน (Part C)**
- **ชนิด:** เปลี่ยน operationalization ของตัววัดที่ลงทะเบียน และเพิ่ม exclusion หลังเห็นผล
- **แผนเดิม**
  - บรรทัด 42: "ถูก iff result set ตรง gold (unordered multiset เว้นข้อที่มี ORDER BY)"
  - บรรทัด 59–62: กำหนดเฉพาะ parse-fail = ผิด และให้แก้ gold ที่ผิดได้ ไม่มีกฎตัดข้อ
- **สิ่งที่ทำ**
  - G4 บังคับลำดับตามคำขอของโจทย์แทนการดู ORDER BY ของ gold (เช่น Q39 TH ไม่บังคับลำดับแม้ gold มี ORDER BY)
  - G1 ไม่ให้คะแนนลำดับคอลัมน์ ส่วน G2 และ G3 เทียบค่าตัวเลขและวันที่ตามค่า (grade.py v1.2 เทียบเป็น string)
  - D3 ตัด Q27 ออกจาก primary analysis ของ log ส.ค. (n=59); รอบ ต.ค. ซ่อม Q27 แทนตามมติ D11 (D-11)
- **ช่วงเวลา:** ตัดสินหลังรันและหลังเห็นผลทั้งหมดของ log (Part C7) และก่อน re-grade ทางการ
- **ผลต่อการตีความ**
  - ผลตาม key v1.2 และ grader เดิม (`results/graded.csv`) รายงานคู่กันใน artifact
  - ข้อสรุปใดที่ต่างกันระหว่างสองฉบับ หรือระหว่าง primary กับ sensitivity ต้องเขียนในเล่ม (C5)
  - ทิศของผลเปิดเผยใน C7

**D-6 run-of-record ของเล่มฉบับแก้ (prereg บรรทัด 61; Part 0)**
- **ชนิด:** เปลี่ยนแหล่งของตัวเลขในเล่ม
- **แผนเดิม:** บรรทัด 61 "ทุกตัวเลขในเปเปอร์ = run-of-record บนเครื่องผู้เขียน" ซึ่งในเล่มที่ส่งคือ log ส.ค.
- **สิ่งที่ทำ:** ตัวเลขหลักของเล่มฉบับแก้มาจากรอบ ต.ค. บนเครื่องผู้เขียน (Part 0) log ส.ค. ไม่ถูกแก้และใช้เทียบความสอดคล้อง
- **ช่วงเวลา:** ตัดสิน 14 ต.ค. 2026 ก่อน model call แรกของรอบ ต.ค. และก่อน regrade ทางการ
- **ผลต่อการตีความ:** ตัวเลขในเล่มเปลี่ยนจากฉบับที่ส่ง และ Response ชี้แจงความต่าง; ยังเป็นการรันบนเครื่องผู้เขียนตามบรรทัด 61

**D-7 Ollama digest ไม่ได้บันทึกในเดือน ส.ค. (prereg บรรทัด 69)**
- **ชนิด:** ข้อที่ลงทะเบียนไว้แต่ไม่ได้ทำ
- **แผนเดิม:** บรรทัด 69 ระบุว่า harness จะบันทึกชื่อรุ่นของ API และ Ollama digest อัตโนมัติในการรันครั้งแรก
- **สิ่งที่เกิด:** `results/results.jsonl` มีเพียง model_echo ที่เป็นชื่อ tag ของ Ollama ไม่มี digest และโมเดล local บนเครื่องถูกลบก่อน 12 ต.ค. 2026 จึงกู้ค่าไม่ได้
- **สิ่งที่ทำ:** รอบ ต.ค. บันทึก digest และ metadata ใน provenance_gate1a, provenance_before และ provenance_after และ runner ล็อก digest ก่อน local call แรก (Part 0 ข้อ 5)
- **ผลต่อการตีความ:** ตัวตนของน้ำหนักโมเดล local ในเดือน ส.ค. ยืนยันไม่ได้ ข้อนี้ใช้กับข้อมูล ส.ค. เท่านั้น และผลของ local ติดป้าย exploratory อยู่แล้ว

**D-8 ลำดับการถามของแขน base ในโมเดล local ต่างจากเดือน ส.ค.**
- **ชนิด:** ความต่างของขั้นตอนที่ไม่กระทบ prompt หรือ payload
- **แผนเดิม:** แขน base ใช้วิธีเดิม (prompt และ payload เหมือน ส.ค.)
- **สิ่งที่เกิด:** ส.ค. ถาม llama31-8b และ qwen25-coder-7b แบบ item-major; รอบ ต.ค. ถามแบบ run-major และสลับกับแขน values (A4)
- **สิ่งที่ทำ:** เปิดเผยตาม Part 0 ข้อ 6; ตรวจว่า prompt และ payload ของแขน base เหมือน ส.ค. ทุก byte (Gate 1a)
- **ผลต่อการตีความ:** สถานะ prefix cache ของ Ollama ต่างกันระหว่างสองรอบ ความต่างระดับ raw output ระหว่างรอบอาจมาจากสาเหตุนี้

**D-9 การเข้ารหัสข้อมูลเปลี่ยนจาก k3 เป็น k3n**
- รายละเอียดอยู่ในกฎข้อมูลของ amendment นี้ (หัวข้อ Deviation log ของส่วนนั้น)

**D-10 Metric 4: error taxonomy (prereg บรรทัด 45)**
- **ชนิด:** วิธีที่ลงทะเบียนไว้แต่ไม่ได้ทำ และการเปลี่ยนวิธีล่วงหน้าสำหรับรอบ ต.ค.
- **แผนเดิม:** บรรทัด 45 ให้ code ความผิดตามรายการปิด (wrong-join / missing-group / hallucinated-column / wrong-filter / syntax / other)
  สองรอบห่างกันอย่างน้อย 3 วัน (intra-rater)
- **สิ่งที่เกิด (ส.ค.):** ไม่ได้ code ด้วยมือสองรอบ Metric 4 ของเล่มที่ส่งใช้การจัดกลุ่มอัตโนมัติแบบ deterministic ของ `analyze_typhoon.py`
- **สิ่งที่ทำ (ต.ค.; ประกาศก่อนมีข้อมูล):** Metric 4 ใช้ taxonomy อัตโนมัติ B6 ของ `analyze_typhoon.py` กับทั้งสองชุดข้อมูล และไม่ code หมวดเชิงความหมาย
- **ผลต่อการตีความ:** taxonomy เป็นการจัดกลุ่มเชิงกลไก ไม่ใช่การ code เชิงความหมาย และไม่มีค่า agreement ของ intra-rater

**D-11 Q27 ซ่อมสำหรับรอบ ต.ค. (มติ D11; Part C3)**
- **ชนิด:** แก้ข้อความโจทย์และ gold ของหนึ่งข้อสำหรับรอบ ต.ค. ซึ่งเป็น experiment ใหม่ด้วยวิธีเดิม (Part 0)
- **แผนเดิม:** บรรทัด 61 ตรึงข้อความโจทย์; Part C ตัด Q27 ตาม D3 (n=59)
- **สิ่งที่ทำ:** รอบ ต.ค. ถาม Q27 ฉบับซ่อม (EN และ TH ใหม่ และ gold ที่เทียบเดือนเดียวกัน) และ grade ครบ 60 ข้อ;
  log ส.ค. ไม่เปลี่ยนและคง Q27 เดิมเป็น excluded; prompt ของแขน base ต่างจาก ส.ค. เฉพาะ call ของ Q27 (Part 0 ข้อ 11)
- **ช่วงเวลา:** ตัดสิน 14 ต.ค. 2026 ก่อน model call แรกของรอบ ต.ค.; ผู้ร่างเห็นเฉพาะผลของ gold และคำตอบที่เขียนเพื่อตรวจถ้อยคำบน k3n
  (ทดสอบ; Part C3) ไม่มีคำตอบของโมเดลต่อโจทย์ฉบับซ่อม
- **ผลต่อการตีความ:** core ของรอบ ต.ค. มี 60 ข้อ จึงเทียบกับเล่มที่ส่ง (n=59) ได้โดยตรงเฉพาะบน 59 ข้อที่ถามเหมือนกัน (Part 0 ข้อ 3);
  ผลของ Q27 ในรอบ ต.ค. เป็นผลของโจทย์ใหม่ ไม่ใช่การวัดซ้ำของโจทย์เดิม

---

### Gates — สิ่งที่ต้อง commit และ push ก่อนแต่ละขั้น (Gate 1c เดิมรวมเข้า Gate 1b)

**Gate 0 (เตรียม; ไม่มีการวัด)**
- ผู้ช่วย implement และทดสอบเครื่องมือทั้งหมดแบบ TEST-ONLY (ไม่มี model call)
- ผู้เขียนตอบคำถามที่บล็อก อนุมัติ ext_decisions (รวมข้อความ EN ตามตัวอักษรของ FK2 และ X19 และกฎข้อสำรอง)
  และอนุมัติรายการแก้ amendment รวม Part 0
- ext_decisions มี sha256 สองค่า: ค่าของเนื้อหาที่ผู้เขียนอนุมัติ และค่าของไฟล์ที่ตรึงหลังตั้ง author_approved
  (ต่างกันเฉพาะ author_approved และช่องบันทึกการอนุมัติ); Gate 1a เทียบค่าหลัง และ AMENDMENT-9 หัวข้อ 3 บันทึกทั้งสองค่า

**Gate 1a (ผู้เขียนรันบนเครื่อง run-of-record ทีละคำสั่ง; ไม่มี model call และไม่สร้างตัวเลขผลใหม่)**
- สร้าง k3n สองครั้ง (คัดลอก Ecommerce1M จาก k3) และ fingerprint ของ k3 ก่อนและหลัง
- คัดลอก suite ของ ส.ค. และ suite ของรอบ ต.ค. และตรวจว่า suite ของรอบ ต.ค. เท่ากับ suite ที่สร้างใหม่จาก suite ของ ส.ค.
  และไฟล์ซ่อม Q27 ทุก byte (มติ D11)
- parity ของ grader (3,600/3,600 บน k3) และ parity_grader (IDENTICAL); selftest ของ suite ทั้งสองฉบับ; สร้างและ record MI instance; ชุด VG; ไฟล์ hint
- dry-run ของ core จาก suite รอบ ต.ค. และตรวจ prompt ด้วย key ปลอม (ข้อยกเว้นเดียวคือ call ของแขน base ของ Q27);
  suite ชุดขยายฉบับ frozen และ selftest_mi บน suite frozen; dry-run ของชุดขยาย
- provenance gate1a (metadata เท่านั้น); anonymity sweep; freeze stamp; ตรวจ prereg หลังต่อท้าย

**Gate 1b (commit และ push ครั้งเดียว; ต้องเกิดก่อนทุกข้อต่อไปนี้)**
- (a) re-grade ทางการใดๆ (b) การรันทางการใดๆ ของ Part B (c) model call แรกของรอบ ต.ค. (แขน base, แขน values และชุดขยาย)
  (d) การสุ่มข้อและแชตแรกของ chat check
- **เนื้อหาของ commit:** `prereg/preregistration_FROZEN.md` ที่ต่อท้ายด้วย AMENDMENT-6, AMENDMENT-7 (Part 0 ก่อน แล้วกฎข้อมูลและ Part C),
  AMENDMENT-8 (ส่วนออกแบบ) และ AMENDMENT-9 พร้อมไฟล์ทุกไฟล์ใน FREEZE STAMP (รายการ path ชัดเจนใน `gate1b_paths.txt`)
- เวลา commit (รูปแบบ ts ของ runner) ใช้เป็น `--not-before` ของ core และชุดขยาย
- hash เวลา และสถานะ push ของ commit นี้บันทึกใน addendum ของ commit Gate 2 (commit ใส่ hash ของตัวเองไม่ได้)

**Gate 2 (log ส.ค.; ข้อมูลรองตาม Part 0; หลัง Gate 1b push)**
- re-grade log ส.ค. บน k3n และ sensitivity บน k3, Part B ของ log ส.ค. และ RQ3 ของ ส.ค.
  เขียนเฉพาะ `results/v13n/` และ `results/v13/` (ไม่เขียน `paper/generated/`)
- สุ่มข้อ chat check จาก `results/v13n/graded_v13n.csv` ตามกฎของ AMENDMENT-8
- commit และ push FREEZE STAMP ของ AMENDMENT-8 และ addendum ของ commit Gate 1b ก่อนแชตแรก

**Gate 3 (รอบ ต.ค.; ข้อมูลหลัก; การรันและการ grade เริ่มได้หลัง Gate 1b push โดยไม่ต้องรอ Gate 2; ขั้นที่ใช้ผลของ Gate 2 คือการเทียบความสอดคล้อง, การวิเคราะห์ H1–H4 (ซึ่งคำนวณ drift เทียบกับ log ส.ค. ในคำสั่งเดียวกัน) พร้อม audit และตารางที่สร้างจากผลนั้น และ addendum กับ commit ผล ทำหลัง Gate 2)**
- ตรวจยอดเครดิตตาม A5 ข้อ 1 → provenance before → terminal 1: core API ตามลำดับของ A4 แล้วชุดขยาย API;
  terminal 2: core local แล้วชุดขยาย local → provenance after → check_rc1_log.py (check 1–7 PASS; check 8 รายงาน)
  → grade ด้วย suite รอบ ต.ค. → ตารางหลักของเล่มจากแขน base (n=60) ลง `paper/generated/` → H1–H4 และ sensitivity ของคู่ที่ไม่พร้อมกัน
  → audit → ชุดขยาย → การเทียบความสอดคล้องกับ ส.ค. บน 59 ข้อที่ถามเหมือนกัน → commit ผล
- ไม่มี Ollama parity gate (Part 0 ข้อ 5)
- chat check ภายใน ±7 วันของแขน B และ 84 แชตภายใน 3 วัน (AMENDMENT-8)

**Gate 4 (claim list)**
- ผู้เขียนอนุมัติ claim list before → after ก่อนแก้ main.tex (ตัวเลขในเล่มเปลี่ยนจากฉบับที่ส่งตาม Part 0)
- scenario ของ A9 เลือกด้วย band เท่านั้น

**Gate ข้าม workstream:** AMENDMENT-9 อยู่ใน commit เดียวกับ Gate 1b จึงไม่มี call ใดของ Gate 3 ก่อน AMENDMENT-9 push

### FREEZE STAMP ของ AMENDMENT-7 (กรอกตอน commit)
- วันเวลา commit, git commit และสถานะ push: บันทึกใน addendum ของ commit Gate 2 (commit ใส่ hash ของตัวเองไม่ได้)
- การตัดสินของผู้เขียน
  - G1 primary: ใช่ (มติ 13 ต.ค. 2026 ข้อ 1) พร้อมข้อยกเว้นคอลัมน์มีทิศทาง (Part C2)
  - reading ของ D2c: คงครบ (ผู้ตรวจคนที่สองรับทุก reading)
  - Q27: log ส.ค. คง Q27 เดิมเป็น excluded (n=59 เป็นผลของ log ส.ค. และ n=60 เป็น sensitivity); รอบ ต.ค. ซ่อม Q27 ตามมติ D11
    และ n=60 เป็นผลหลัก (Part C3)
  - ชุด VG: VG10 (VG9 เป็น sensitivity)
  - การนับใน abstract: set-based ตามมติ D6 (GF อยู่ใน RQ2)
  - clause เรื่อง gap ใน abstract: ใส่ทุก scenario ยกเว้น G-d และใส่ใน RQ2 ทุก scenario
  - alt keys: คงไว้
  - RQ3 reference: gold v1.2 คำนวณใหม่บน k3n (ข้อที่ซ่อมตามมติ D11 ใช้ gold ฉบับซ่อมในรอบ ต.ค.)
  - ผู้ตรวจคนที่สอง: ทำ และรับครบ (ผู้ตรวจไม่เห็นผลของโมเดล)
  - ผู้เขียนตัดสินข้างต้นหลังจาก memo D7 ซึ่งมีตัวเลขทดสอบเข้าถึงได้ในโฟลเดอร์โครงการ แต่ผู้เขียนไม่ได้อ่านตารางผลรายโมเดลใน memo: ใช่
- suite core ของรอบ ต.ค.: `suite/k3n_suite_v1.3n_oct.tsv` สร้างจาก `suite/k3n_suite_v1.3n.tsv` และไฟล์ซ่อม Q27 ด้วย `build_oct_core_suite.py`
  (sha256 ของ suite และ sha256 ของตัวสร้างและไฟล์ซ่อมซึ่งอยู่นอก git อยู่ในตารางหัวข้อ AM-7 ข้างล่าง)
- รายการ VG ที่ได้: VG10 = Q01, Q07, Q09, Q13, Q14, Q15, Q21, Q30, Q42, Q48 (`suite/vg_set_v13n.txt`); VG9 (sensitivity) = VG10 ไม่รวม Q48 (`suite/vg_set_v13n_VG9.txt`)
- block sha256: P `32e422929b84fa12ed45d0752e45f25c8ebaa2ae077adb17d95e8f2e7fb61713` / E `5a9fb96ffd03bf08cb723f5f4f1f87161aaf642f83faf015bab6852f3255987c`
- สถานะ billing และยอดเครดิตก่อนเริ่ม: บันทึกใน addendum ของ Gate 3 (A5 ข้อ 1); billing ของ project Gemini ในเดือน ส.ค.: ไม่ทราบ
- PostgreSQL ของเครื่อง run-of-record (version และ locale): `PostgreSQL 16.9 (Homebrew) on aarch64-apple-darwin24.4.0, compiled by Apple clang version 17.0.0 (clang-1700.0.13.3), 64-bit`; locale ของ k3 และ k3n: datcollate C, datctype C, provider libc (`c`), encoding UTF8
- `ollama --version`: 0.32.5
- digest
  - llama3.1:8b: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` (ID ใน `ollama list`: 46e0c10c039e; Q4_K_M)
  - qwen2.5-coder:7b: `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` (ID ใน `ollama list`: dae161e27b0e; Q4_K_M)
  - typhoon2-8b: `b3768487ef30c179e5c395fdf8ae508057446de3cbb0e5b8169859d3b4d41c39` (ID ใน `ollama list`: b3768487ef30; Q4_K_M)
  - GGUF sha256: `63a0e0730cc131abbd2d2ab7ddde27bf9aac530143e4b1f824d03399c4567770`

sha256 ของไฟล์ (ตารางจาก `freeze_stamp.py --manifest freeze_manifest_gate1b.tsv` หัวข้อ PREREG, AM-7 และ AM-8;
หัวข้อ PREREG มีเฉพาะแถวบรรทัด 1–115 เพราะ prereg ทั้งไฟล์เปลี่ยนเมื่อวางตารางนี้ และ sha256 ของ prereg หลังต่อท้ายบันทึกใน addendum ของ Gate 2):

#### PREREG
| ไฟล์ | sha256 |
|---|---|
| `prereg/preregistration_FROZEN.md` (บรรทัด 1–115) | `269e5f0996627419154ef9c032e36a92dbecb6f5b7e8f7394f1002b279a375d0` |

#### AM-7
| ไฟล์ | sha256 |
|---|---|
| `harness/db/rq3_drop_indexes.sql` | `cfaa524ed2e0e78df0b0e9219800f36012ad289599a384535d2127ec1df8c631` |
| `suite/k3n_suite_v1.3n.tsv` | `195839ec46f902901f03e90965c00bb1b78b4ef6bc970f4cabb0ed0272997366` |
| `suite/k3n_suite_v1.3n_oct.tsv` | `96b8e9f2e48398111aa6b2d555995a2b726a54e62efe1474668477dda7eed46b` |
| `suite/k3_suite_v1.3.tsv` | `7e46649c2bc65a22a7471bf1db3e8494d8354bda2e1f26fafe45d90434b96121` |
| `suite/CHANGELOG_v1.2_to_v1.3.md` | `a2aa583d4b5825f525dd321478471234c4ce3187ce500f8a9e34a77d8e8973aa` |
| `suite/CHANGELOG_v1.3_to_v1.3n.md` | `afadd88e867808c2060b440063b9ed5876ba3ad07b338476249c3f1ccba8fc13` |
| `harness/grade_v13.py` | `aed86b26bd83548a215ee1999bd9c47d524558af1ca34b03909bc1144518e038` |
| `harness/selftest_v13.py` | `f67fc516dfe7b498e8b73f2a7a7949d9968283619871d45af34e3b9e33cafef4` |
| `harness/grade_v13n.py` | `e1dedbdced9035ecc1326339b3a1564e250fa746fda75dba79571d3c15d8b511` |
| `harness/selftest_v13n.py` | `9fb9836baa18943356bd1400d642ecc867a3e98b420c3d53a290fec68b441013` |
| `harness/parity_grader.py` | `717bb365041d4ebe4eb09986f3ebf0e46f137f63c6f1d36e99f1ec0c320458e1` |
| `harness/parity_check_v13.py` | `85d575b43a99d50ef9bc93c444380fed28b428ba1fc03a4a603c8b1755b9e8a2` |
| `harness/suite_columns.json` | `46afcc4f3ef5a63702f2940bdf41efd2bbcfee13fa152474fa591284c83f65ce` |
| grade_v13n.diff | `1033c2655f5c2f1b3f3c08312a2ef3e4b8cd5b0274b69c914d4fbe6a680353a6` |
| build_oct_core_suite.py | `14d76c3d38733409126470fb0c1c27905e655f44fd0b3e4225bf108bef68b6d8` |
| Q27_REPAIR_2026-10-14.tsv | `229ea98ac5744b89b8b39a1e4f6a78ee2419163fa44a3a185d965d738509ae3b` |
| `suite/k3_suite_v1.2.tsv` | `c4ed472e7c15fac2461dd6ddbd85f3b4519351e820516017a49910d8a2338021` |
| `suite/value_hints_v1.json` | `2ea5efb413182b7929310f30bb312175776e63ea18eec0616ac7bbd0cc38919c` |
| `results/rc1/prompts_rc1.jsonl` | `8e420057ea7f81225debd1e2d9fbf2c22f987177a36e87054cbff3dde5e1f5bd` |
| `harness/runner.py` | `ed0c562adda217e0bb8e1706d33fda28769b329802cd4a8455b7c7daae62192f` |
| `harness/make_value_hints.py` | `7573ace4751d860a2410071bdebbc9a699a88db01ecaf3286717ddb15d442296` |
| `harness/check_prompts_rc1.py` | `21caf033a417defb0c0bb12c88265e3620348986c3c81c69a9af4d549533bca7` |
| `harness/provenance_rc1.py` | `c319872d47eb33a6f5ae77e2a23f427e42c6535a0ea9b76ce24610cb89756a00` |
| `results/rc1/provenance_gate1a.json` | `31a849c10b9e12773f32f798f1591e5691d20dac85151c0e76c526d8566608c5` |
| runner_rc1.diff | `9ead655827ad43f82b6ae2ab88e054c4a63da02f7fdc16ca16a745e7317bc8c2` |
| `harness/models.json` | `019ec1785ae857d4fd798048145c7453911dc43a9255f6f13fb70c060ce7b099` |
| scan.py | `a85917967a816d4f649f9f84817655fb0dab4e32e97d4829ecb2e4a3a102acac` |
| scan_old_vg_classifier.py | `b28f3737904f599248d23ac203a78496b79f390d57e7eaee4d6b336f3174e8e7` |
| scan_new_vg_classifier.py | `7debc50a85507f0192cc2c4a5ee2e8750a22709006198620b82880a894594925` |
| `harness/vg_classifier.py` | `ec911d7a5e6ef2cb58d34d817ab0ffb618524485de099cf2b215b1122933b526` |
| `harness/analyze_rc1.py` | `f2fa8d2690a12a2acfa48289a1de3b8cd402673ef741c9fecb180d469bac024e` |
| `harness/make_audit_sheet_rc1.py` | `1d9c615261ec991a8fd34b59a54db5ed79243b48fb67d7246e297a8d66c7a3bb` |
| `harness/audit_agreement_rc1.py` | `e7f2b762fa17c60251bbe124136183bdaed689785b16fd2f8f0d3ba89b5d272a` |
| `harness/check_rc1_log.py` | `1592e06ee60703ea75a532059143ee6d8ee2bd38612ef4e3e712e45107e18dfa` |
| `harness/make_table_rc1.py` | `cbe10a11185abcb6697ed968823041915a2e32161f5b41003b647219acbe5bf5` |
| `harness/analyze_log_v13.py` | `800bda33e502e73224a2b985944078476d8fe000674097daca04fd0cf9ff33e6` |
| `harness/empty_split_v13.py` | `c1645519c98a45d61bd5edb27487e2ea904cb0aceffff810f269d3e463ad18e3` |
| `harness/phi_tableiv.py` | `e781e3348fab17ecc1b8cc1b8bb1d1f300a5478f5e9daba82578fbcdc4b75aa5` |
| `harness/analyze.py` | `2a7eda5a0b22d789aa41a3fca13a99c19d4c48dea92bf1e767f03f8bd87bfadc` |
| `harness/analyze_typhoon.py` | `f692e1b284b383888ac3e1527c721638203a2bbe2e28b32738c4521fb8ea4287` |
| `harness/make_tables.py` | `90ff96b8a8341ddb2e8fd5b16d3b84f038b27ae771f844b48ccc3ded369e3a49` |
| `harness/make_figures.py` | `e14d3e440f070fec1dd322baa878d79d38aaa1cc3d69fcdd64ba51d2380f5f6f` |
| `harness/plan_quality.py` | `5a641fb0de87d4951fec77968fa8ceb751f02f46ad33c1a0bffc64d8cc5fd2a7` |
| `harness/consistency_aug_oct.py` | `23eea59a177484805be876b53e75bb02b8f5372995197a40355c19bc1e2f80ef` |
| `harness/cost_rc1.py` | `013b9b7506032b2394ae74056c605273cfeac8ad568f98c86b5ed95b0ed2eeff` |
| `harness/transitions_v13n.py` | `fd45aa143b157e3b6c6a4899552563c90e0a9e20f83a90bd3778bd60d8648500` |
| `harness/paper_numbers_v13n.py` | `9a715628e17dffbb37920adcc2e8af0c588379ccdf2cc9c7f2294077789ba601` |
| `harness/make_vg_sets.py` | `a6f7efc9ffabeeb9ddc3f0df8a970fc6027d5bff038f09a6749a369c560faa6c` |
| `harness/vg_rule.py` | `1fd1e28e7fb47806f789e536ba5bd40c537f3b40c0dadcf4719ebdf9c38423f3` |
| `harness/indexes.sql` | `3e1d62076cb72a07974253600abe9eac9d041650e54bebcb93b04eeacb1ad6a1` |
| `suite/vg_set_v13n.txt` | `4685db6e818efd1bb2fb5447210f7085d385270cb91008edd84a2a7426bc6188` |
| `suite/vg_set_v13n_VG9.txt` | `d40cd61579ed900feffbffe4c17a2a6ee8d2c99027e620a39c17c39026baaebe` |

#### AM-8
| ไฟล์ | sha256 |
|---|---|
| `harness/chatapp/draw_chat_items_v13.py` | `12632f46b26904c909d538746135c17df333a4b6f212e92124da925306a0f9e5` |
| `harness/chatapp/make_chat_cells.py` | `5d3e00d3747456d501266a34f423c3bfdcc108df7b744ccdfdf8ff83c379f00e` |
| `harness/chatapp/make_chat_log_xlsx.py` | `6b2261bde3cbda82c75f2bb2e3e5e809e6d15eef459de16de0787f055a19bc2b` |
| `harness/chatapp/chat_log_export.py` | `3ee663cb4991bcdc40a3ec2ab5b535e6ec94d45c4a3521f6bfb8723c2e2bcf60` |
| `harness/chatapp/chatapp_to_results.py` | `f70be7fb86e75bdc554f7b3f9847954b98bd63e47fe7cc8156e9b22f6ff6eb67` |
| `harness/chatapp/vg_outcome.py` | `659dff5696df68a0fa4a7f673f5fce3d78b6bcebae07d13c0e7408298da7fc0d` |
| `harness/chatapp/chat_silence_sheet.py` | `d1b0e5ffc63f214b495bbce4adf8e50d9dc31c265638aa8b59b425abcd6b7ec6` |
| `harness/chatapp/chat_report.py` | `9df39cfbecf3038c7f9cc87aa04e117a63e180863e2c414d242f0c1d5cdf3995` |
| extract_cases.json | `3fe0ddfe305ceaad4772601729b1ac70f358867598a33ce06170250a98f28bb4` |

## AMENDMENT-8 (19 ต.ค. 2026 — chat-app consistency check; ส่วนออกแบบ commit ก่อน re-grade ทางการ และรายการข้อ commit ก่อนแชตแรก; ตอบ KST 2027 R1-W2, R1-RC2 และ R2)

**สถานะ:** ส่วนเสริมเชิงพรรณนาหลังได้ผล major revision
- ไม่เปลี่ยน run-of-record, answer key (AMENDMENT-7 Part C), grader หรือสถิติหลักใดๆ
- ไม่ใช่การ validate และไม่มีการทดสอบสถิติ

**1. วัตถุประสงค์และคำที่ใช้**
- **คำถามของ check:** รูปแบบความผิดพลาดที่พบใน API proxy ปรากฏใน free chat app จริงหรือไม่ ณ วันที่ทดสอบ
  - รูปแบบที่ตรวจคือความผิดด้าน value grounding และการที่ความผิดไม่มีคำเตือน
  - check นี้ไม่ใช่การประมาณ accuracy ของ app
- **คำในเล่มและใน Response**
  - เรียก check นี้ว่า "chat-app consistency check" ห้ามใช้คำว่า validation
  - Form B เรียกว่า "instructor-written student-style prompt" ห้ามเรียกว่า student-generated หรือ student prompt
  - โมเดลที่เรียกผ่าน API เรียกว่า "free-tier proxies"
  - ระบุวันที่ป้อนแชต (หรือช่วงวันที่ ซึ่งไม่เกิน 3 วันตามหัวข้อ 6) และคำว่า "single shot" ทุกครั้งที่รายงานผล

**2. Apps และการจับคู่กับ API proxy (ตรึงตาม roster เดิม ห้ามเพิ่มหลังเห็นผล)**
- ChatGPT (free plan) คู่กับ gpt-mini (`gpt-5.4-mini-2026-03-17`)
- Gemini app (free) คู่กับ gemini-flash (`gemini-3.6-flash`)
- Claude.ai (free plan) คู่กับ claude-sonnet (`claude-sonnet-5`)
- app อื่น เช่น Copilot หรือ DeepSeek อยู่ใน Future Work

**3. บัญชีและการตั้งค่า**
- **บัญชี:** ใช้บัญชี free แยกต่างหากครบทั้งสาม app ไม่มี subscription และผู้เขียนสร้างและล็อกอินเอง
  - ห้ามใช้บัญชีแบบเสียเงินที่ผู้เขียนใช้อยู่
  - Gemini ต้องใช้บัญชี Google ส่วนบุคคล (@gmail.com) ที่ไม่มีแผน AI แบบเสียเงิน
    ห้ามใช้บัญชี Google Workspace ของมหาวิทยาลัย เพราะ Workspace ใช้ข้อกำหนดและบริการต่างจาก consumer free tier
- **การตั้งค่าก่อนแชตแรก**
  - ปิด memory, การอ้างอิงแชตเก่า (reference to past chats), personalization และ custom instructions
  - ปิดการใช้ข้อมูลเพื่อฝึกโมเดลเท่าที่ app เปิดให้ปิด เพื่อกันไม่ให้ suite รั่วก่อน release
  - ไม่เลือกโหมด reasoning, search หรือ deep research เอง ใช้ค่า default ของ free plan
- **สภาพแวดล้อม:** ใช้ desktop browser ตัวเดียวกันทั้งสาม app ไม่ใช้ VPN และบันทึก browser กับเวอร์ชัน และภาษาของ UI
- **หลักฐาน:** screenshot หน้า settings ของทุก app ก่อนแชตแรกและหลังแชตสุดท้าย แล้ว crop ข้อมูลบัญชีออก

**4. Items (18 ข้อ)**
- **VG_chat (10 ข้อ ตรึง):** Q01, Q07, Q09, Q13, Q14, Q15, Q21, Q30, Q42, Q48 (ชุด VG10 ตามกฎ AMENDMENT-6 ซึ่งเป็นชุดหลักของ AMENDMENT-7 B2.1)
  - หมายเหตุ Q48: gold เทียบ literal 'None' ซึ่งบน k3n ไม่ใช่ค่าที่เก็บแล้ว (AMENDMENT-7 B2.1) Q48 ยังนับใน k = 10
- **non-VG (8 ข้อ; ใช้เฉพาะ Form B ภาษาไทย) สุ่มด้วยกฎต่อไปนี้ (ตรึงก่อน re-grade ทางการ; ขอบเขตของการปิดตาดูหัวข้อ 14)**
  1. **pool:** primary items (v13_status = primary) ที่ไม่อยู่ใน VG_chat (49 ข้อ)
  2. **E (error pool):** ข้อใน pool ที่ frontier proxy อย่างน้อยหนึ่งตัวผิดโดย majority ในภาษาไทย
     ตาม re-grade ทางการของ log ส.ค. บน k3n (`results/v13n/graded_v13n.csv` อ่านด้วย `--arm base`) (frontier proxy คือ gpt-mini, gemini-flash และ claude-sonnet)
  3. **C (correct pool):** ข้อใน pool ที่ frontier proxy ทั้งสามตัวถูกโดย majority ทั้ง EN และ TH
     ข้อที่ไม่อยู่ใน E และไม่อยู่ใน C (ผิดเฉพาะ EN) ไม่ถูกสุ่ม
  4. **การสลับลำดับ:** สร้าง `rng = random.Random(20261012)`
     แล้วเรียง E ตาม qid และ `rng.shuffle` จากนั้นเรียง C ตาม qid และ `rng.shuffle` ด้วย rng ตัวเดิมต่อกัน
  5. **take(pool, k)**
     - รอบแรก: ไล่ตามลำดับที่สลับแล้ว รับข้อเมื่อ tier ของข้อนั้นยังไม่ถูกรับในการเรียก take ครั้งนี้ จนครบ k
       (tier ที่รับจาก E ไม่ห้ามการรับ tier เดียวกันจาก C)
     - รอบที่สอง: เติมจากข้อที่เหลือตามลำดับเดิมจนครบ k
  6. **การเลือก**
     - `e = take(E, min(4, |E|))` และ `c = take(C, 8 − len(e))`
     - ถ้า C ไม่พอ ให้เติมจาก E ที่เหลือ
     - NONVG = e ตามด้วย c
  7. **ผลลัพธ์:** รายการข้อ และ `sha256(",".join(VG_chat + NONVG))` ที่บันทึกใน FREEZE STAMP
- **เหตุผลของกฎ**
  - E ทำให้ check ครอบความผิดแบบ non-empty ซึ่งเป็น headline ของเล่มและอยู่นอก VG เป็นส่วนใหญ่
  - C เป็นตัวกันกรณีที่ app แย่กว่า proxy โดยรวม
  - E นิยามจากภาษาไทย เพราะ cell ของ non-VG ถามเป็นภาษาไทยเท่านั้น
  - การเลือกแบบมีเงื่อนไขกับผลของ API เป็นการจงใจ และต้องเปิดเผยในเล่ม
  - ฐานของการสุ่มเป็นข้อมูลรองตาม AMENDMENT-7 Part 0 (log ส.ค. ที่ regrade บน k3n) เลือกเพื่อให้รายการข้อตรึงได้ก่อนรอบ ต.ค.
    กฎไม่ขึ้นกับผลของรอบ ต.ค. และการเปรียบเทียบที่รายงานทุกตัวใช้แขน B ของรอบ ต.ค.
  - Q27 เป็นข้อ excluded ใน log ส.ค. จึงไม่อยู่ในฐานการสุ่ม และ Q27 ฉบับซ่อมของรอบ ต.ค. (AMENDMENT-7 Part C3) ไม่เข้า chat check
- **ถอนของเดิม:** รายการเดิม Q12, Q02, Q19, Q16, Q39, Q40, Q60, Q47 และรายการ NONVG ที่เขียนตายตัวใน `make_chat_cells.py`
  - เหตุผล: รายการเดิมสุ่มจากผลของ key v1.2 ซึ่ง Q12, Q19 และ Q39 อยู่ใน error pool เพราะ key ผิด (AMENDMENT-7 Part C)

**5. Cells และ prompt**
- **cells ต่อ app:** Form A × TH × VG_chat 10 + Form B × TH × (VG_chat 10 + NONVG 8) = 28
  รวมสาม app เป็น 84 แชต
- **ลำดับ:** สลับลำดับ cells ด้วย `random.Random(20261012)` จากลำดับก่อนสลับที่ `make_chat_cells.py` สร้าง (ตรึงด้วย sha256)
  และใช้ลำดับเดียวกันทั้งสาม app
  ผู้เขียนทำ cell ที่ i ครบทั้งสาม app ติดกัน (สาม tab) ก่อนไป cell ที่ i+1
- **Form A:** ข้อความเดียว = `SYSTEM.format(ddl=DDL_<schema>) + "\n\n" + question_th`
  - คือข้อความเดียวกับ prompt ของ harness แต่วางเป็น user message เพราะ app ไม่มีช่อง system
- **Form B (TH):** ข้อความตามนี้ทุกตัวอักษร
  `ช่วยเขียนคำสั่ง SQL (PostgreSQL) ให้หน่อย\n\nโครงสร้างตาราง:\n{DDL}\n\nโจทย์: {question_th}`
  - Form B ไม่ห้ามคำอธิบาย จึงเห็นได้ว่า app อธิบาย ถามกลับ หรือเตือนเรื่องค่าที่เก็บจริงหรือไม่
- **ไฟล์ prompt:** `make_chat_cells.py` สร้างไฟล์ prompt หนึ่งไฟล์ต่อ cell จากค่าคงที่ใน `harness/runner.py`
  - ข้อความเหมือนกันทุก byte ทั้งสาม app
  - `cells.tsv` บันทึก sha256 ของแต่ละ prompt และ manifest hash อยู่ใน FREEZE STAMP

**6. วิธีป้อนและเวลา**
- **ป้อนด้วยมือเท่านั้น:** ผู้เขียนคัดลอกข้อความจากไฟล์ prompt วางในแชตใหม่แล้วกดส่งเอง
  - ห้ามใช้ script, bot, browser extension หรือ agent ที่ควบคุม browser ทุกชนิด รวมถึงเครื่องมือ browser ของ Claude
  - ใช้ `pbcopy` โหลดข้อความจากไฟล์ prompt เข้า clipboard และ `pbpaste` บันทึกคำตอบที่คัดลอกลงไฟล์ raw ได้
    ส่วนการวางในแชตและการกดส่งทำด้วยมือ
- **หนึ่ง cell คือหนึ่งแชตใหม่แบบ single turn:** ห้าม regenerate, ห้าม edit และห้ามถามซ้ำ
- **turn 2:** ใช้เฉพาะเมื่อ app ถามกลับแทนการให้ SQL
  - ส่งข้อความตายตัวครั้งเดียว: `ช่วยเขียนคำสั่ง SQL ให้เลย ตามสมมติฐานที่คิดว่าน่าจะถูกที่สุด`
  - turn 1 เป็นผลหลัก ถ้า turn 1 ไม่มี SQL ให้นับว่าผิดและ code เป็น ASKED
  - turn 2 เป็นผลรอง
- **rate limit หรือ banner แจ้งการสลับโมเดล:** หยุดรอ แล้วทำต่อจาก cell ที่ยังไม่เสร็จ ไม่ข้ามและไม่ทำซ้ำ บันทึก banner
- **ความผิดของผู้ป้อน:** เช่น วางผิดหรือกดส่งก่อน ให้ตั้ง status เป็น void พร้อมเหตุผล
  แล้วทำ cell นั้นใหม่ในแชตใหม่ โดยไม่ลบแถวเดิม
- **เวลา**
  - ทำครบ 84 แชตภายใน 3 วันปฏิทิน: แชตที่ส่ง (status done และ void ที่ส่งแล้ว) ทุกแถวอยู่ในวันปฏิทินติดกันไม่เกิน 3 วัน (เวลาไทย)
  - อยู่ภายใน ±7 วันจากแขน B: ทุกวันที่ของแชตอยู่ในช่วงตั้งแต่วันแรกลบ 7 วัน ถึงวันสุดท้ายบวก 7 วัน
    ของ record ภาษาไทยแขน B ของรอบ ต.ค. ของ proxy คู่กัน ถ้าไม่ผ่าน ใช้ทางสำรองของหัวข้อ 9 พร้อมป้าย "not concurrent"
  - ลำดับ cell-major (หัวข้อ 5: cell ที่ i เสร็จครบทั้งสาม app ก่อน cell ที่ i+1 เริ่ม): cell ที่เริ่มก่อน cell ก่อนหน้าเสร็จครบ
    ไม่ทำให้การ export ล้ม แต่ `chat_log_export.py` พิมพ์จำนวน และ `chat_report.py` รายงานเป็น deviation พร้อมลำดับของ cell นั้น
  - แถว void (หัวข้อ 6) คงอยู่ใน log ทุกแถว: แถว void ที่ส่งแล้วต้องมีเวลาส่งและนับในช่วง 3 วัน ส่วนแถว void ที่ไม่ได้ส่ง
    ต้องมีหมายเหตุขึ้นต้นว่า "not sent"; การทำใหม่ของ cell เดียวกันเป็น attempt ถัดไป และใช้แถว done เพียงแถวเดียวต่อ cell
  - บันทึกเวลาส่งและเวลาได้รับ (ICT) ทุก cell

**7. การบันทึก (append-only)**
- **คำตอบ:** คัดลอก verbatim ด้วยปุ่ม copy ของ app ลงไฟล์ `raw/<app>_<prompt_id>.md` (turn 2 แยกไฟล์)
  และห้ามแก้ไฟล์ raw หลังบันทึก
- **screenshot:** ถ่ายทุก cell และ crop ชื่อ อีเมล และรูปบัญชีออกก่อนใส่ artifact
- **`log_index.tsv`:** app, order, prompt_id, status, ts_sent_ict, ts_done_ict,
  ui_model_label (ตามที่ UI แสดง หรือ "not shown"), limit_banner, tools_visible, turn2_sent, raw_file, raw2_file, screenshot และ note
- **ข้อห้าม:** ห้ามสร้าง share link สาธารณะของแชต

**8. การให้คะแนนและการ code**
- **แปลง log:** `chatapp_to_results.py` แปลง log เป็น JSONL รูปแบบเดียวกับ runner
  (model_key = `app-<app>-<form>`, run = 1)
- **กฎสกัด SQL** (กรณีทดสอบ 35 กรณีตรึงในตาราง `extract_cases.json` ของ kit; sha256 อยู่ใน FREEZE STAMP ของ AMENDMENT-7 หัวข้อ AM-8)
  - Form A ใช้ `runner.extract_sql` ตรงตัว (กฎเดียวกับแขน API): fence ที่ tag ไม่ใช่ 'sql' เป็น parse failure และนับผิด
    สอง statement ใน block เดียวเป็น parse failure และ fence ที่ `runner.extract_sql` อ่านไม่ได้ (เช่น fence บรรทัดเดียว) เป็น parse failure
  - sensitivity ที่ประกาศล่วงหน้าของ Form A: รับ fence ที่มี tag คำเดียว sql, postgresql, pgsql หรือ psql (ไม่สนตัวพิมพ์)
    และรายงานจำนวน cell ที่เปลี่ยน รวมทั้งระดับต่อ app ที่เปลี่ยนตาม
  - Form B ใช้ code block แรกถ้ามี แล้วใช้ statement แรกระดับบนสุด (ตัดที่ `;` แรกนอก literal, comment และ dollar quote)
    - fence ตามแบบ CommonMark: เปิดด้วย backtick ติดกันอย่างน้อยสามตัว (ที่ตำแหน่งใดก็ได้ แบบเดียวกับ `runner.extract_sql`)
      หรือ tilde อย่างน้อยสามตัวที่ต้นบรรทัด และปิดด้วยอักขระชนิดเดียวกันที่ยาวไม่น้อยกว่า; backtick ที่ตามด้วย backtick อีกตัว
      ในบรรทัดเดียวกันเป็น inline code ไม่ใช่ fence
    - ส่วนที่เหลือของบรรทัดเปิด fence เป็น info string และคำแรกคือ tag: ตัดบรรทัดนี้ทิ้ง เว้นแต่ info string ขึ้นต้นด้วย SELECT หรือ WITH
      (ถือเป็น code) หรือเป็น tag ตามด้วย SELECT หรือ WITH (ข้อความหลัง tag เป็น code)
    - ถ้าไม่มี code block ใช้บรรทัดแรกที่ขึ้นต้นด้วย SELECT หรือ WITH จนถึง `;` แรกระดับบนสุดหรือจบข้อความ (ไม่หยุดที่บรรทัดว่าง);
      บรรทัดที่ขึ้นต้นด้วย 'Select' แบบตัวพิมพ์ประโยคถือเป็นข้อความภาษาอังกฤษ ไม่ใช่ SQL
  - ถ้า app ให้หลาย query ใช้ query แรก เพราะนักศึกษาจะคัดลอก query แรก
  - **NO_SQL:** กฎเดียวกันทั้งสอง form คือข้อความที่กฎสกัดของ form นั้นคืนมาไม่มีบรรทัดที่ขึ้นต้นด้วย SELECT หรือขึ้นต้นด้วย WITH
    ตามด้วยชื่อแล้ว AS ( (รับ RECURSIVE และรายการคอลัมน์ในวงเล็บหลังชื่อ) ในตัวพิมพ์ใดก็ได้; SQL ที่ให้เฉพาะใน inline code เป็น NO_SQL
  - SQL ที่พบแต่ parse หรือ execute ไม่ได้เป็น "SQL present, wrong"; ทั้งสองแบบนับผิด และ NO_SQL ไม่เป็น GF
  - **parse failure ในการ code VG:** SQL ที่ parse ไม่ผ่านถูกจัดคลาสเป็น run ที่ไม่มี SQL (NO_PRED) จึงไม่เป็น GF
    ซึ่งเป็นกฎเดียวกับ run ที่ parse ไม่ผ่านของแขน API (AMENDMENT-7 B2.3); `chat_report.py` รายงานจำนวน cell ที่จะเป็น GF
    ถ้าจัดคลาสจาก SQL ที่สกัดได้ทั้งที่ parse ไม่ผ่าน พร้อมระดับที่จะได้ (ตัวบอกประกอบ ไม่ใช่กฎ)
  - turn 2 ที่ส่งทั้งที่ turn 1 มี SQL รายงานเป็น deviation และยัง grade turn 2 เป็นผลรอง
- **การให้คะแนน:** `grade_v13n.py` กับ suite v1.3n บน PostgreSQL 16.9 ฐาน k3n (grader และ key เดียวกับ AMENDMENT-7; `--arms chat`)
  - sensitivity: grade บนฐาน k3 ด้วย suite v1.3 และเทียบกับแขน B ภาษาไทยของรอบ ต.ค. ที่ grade บน k3 (artifact เท่านั้น)
    ถ้าข้อสรุปต่างกันระหว่างสองฐาน ให้เขียนในเล่มทั้งสองแบบ
- **VG code ของทุก cell ใน VG_chat:** ใช้ตัวจำแนกของ AMENDMENT-7 B2.3 (`harness/vg_classifier.py`; vocabulary จาก k3n) กับ SQL ที่สกัดได้
  - **grounding failure (GF) cell** คือ cell ที่มี SQL แต่ผิดภายใต้ key v1.3 และตัวจำแนกจัดเป็น THAI_COPY หรือ INVENTED (cell ที่ไม่มี SQL เป็น NO_SQL ไม่ใช่ GF)
    ซึ่งเท่ากับนิยาม GF ของ AMENDMENT-7 B2.2 เมื่อมี run เดียว (ตัวจำแนกใช้กับ run ที่ผิดเท่านั้น)
  - **clean cell** คือ cell ที่ execute แล้วถูก หรือจัดเป็น GROUNDED หรือ STORED
  - `lit_elsewhere` (จาก `vg_outcome.py`) เป็นตัวบอกเสริมเชิงกลไก
    คือ literal อังกฤษที่ถูกต้องปรากฏที่อื่นในคำตอบ แต่ไม่อยู่ใน SQL ที่นำมาให้คะแนน
- **query ที่ execute ได้แต่ผิด:** แยก silent-empty กับ silent-non-empty ตามนิยามของ AMENDMENT-7 B1
- **silence code (เฉพาะ Form B; ผู้เขียน code เอง)**
  - ใช้กับทุก cell ที่ SQL ผิดหรือไม่มี SQL
  - FLAGGED: คำตอบเตือนว่าค่าที่เก็บจริงอาจต่าง แนะนำให้ตรวจค่า หรือให้ query ตรวจค่า เช่น SELECT DISTINCT
  - ASKED: ถามกลับแทนหรือก่อนให้ SQL
  - SILENT: ไม่เข้าทั้งสองแบบ
  - code สองรอบห่างกันอย่างน้อย 3 วัน (ธรรมเนียมเดียวกับ error taxonomy ของ prereg) และรายงาน agreement ก่อนแก้ความต่าง
  - cell ที่สองรอบไม่ตรงกัน ผู้เขียนอ่านซ้ำและบันทึก code สุดท้ายพร้อมเหตุผล
  - sheet ของการ code ซ่อนชื่อ app สถานะ VG และป้ายถูกผิด ใช้ code_id ทึบ และสลับลำดับต่างกันในแต่ละรอบ; รอบที่สองไม่แสดง code ของรอบแรก
    และเริ่มได้หลังรอบแรกอย่างน้อย 3 วัน (72 ชั่วโมง)
  - กุญแจของทุก workbook (app, prompt_id และ qid; สำหรับ audit รวมคลาสของตัวจำแนก) อยู่ในไฟล์แยกที่ใช้ชื่อเดียวกับ workbook
    และลงท้ายด้วย `_key.json` ซึ่งผู้ code ไม่เปิดระหว่าง code; workbook ไม่มีกุญแจแม้ใน sheet ที่ซ่อน
  - code_id และลำดับแถวมาจาก seed สาธารณะ 20261012 การปิดตาจึงเป็นแบบขั้นตอน ไม่ใช่การเข้ารหัส
  - รายงาน % agreement, Cohen's κ และตาราง 3×3 และเปิดเผยว่ารูปแบบคำตอบอาจบอก app ได้
- **audit ปิดตาของตัวจำแนก B2.3:** ใช้กับ cell VG_chat ที่ผิด (ทั้งสอง form ทั้งสาม app) แบบเดียวกับแขน values
  (seed 20261012, ซ่อน app, form และคลาส) ตัวจำแนกเป็นผลหลัก รายงาน % agreement และ Cohen's κ; เปิดเผยว่าผู้ code เป็นผู้ป้อนแชตเอง

**9. ตัวเปรียบเทียบ**
- **ตัวเปรียบเทียบหลัก:** แขน B ภาษาไทยของ AMENDMENT-7 Part A (majority of 5) ของ proxy ค่ายเดียวกัน ซึ่งเก็บในช่วงเดียวกัน
- **กรณีแชตของ app ใดอยู่นอกช่วง ±7 วันจากแขน B:** ตัวเปรียบเทียบยังเป็นแขน B ภาษาไทยของรอบ ต.ค. ของ proxy ค่ายเดียวกัน
  และติดป้าย "not concurrent" (log ส.ค. ห่างจากแชตมากกว่านั้น จึงไม่ได้พร้อมกันมากกว่า)
- **กรณีแขน B ของโมเดลนั้นใช้ไม่ได้ตาม AMENDMENT-7 A5:** ใช้ log ส.ค. ที่ regrade ภายใต้ key v1.3n บน k3n
  (`results/v13n/graded_v13n.csv` และ `results/results.jsonl`) และติดป้าย "not concurrent"
- **concordance ระดับ item:** ต่อ app ต่อ item ดูว่าผล execution ตรงกับ proxy หรือไม่ (k/n)
  และบน VG_chat ดูว่าสถานะ GF ตรงกับ proxy หรือไม่

**10. กฎตีความสามระดับ (ตรึงล่วงหน้า; รายงานทุกทิศทาง)**
- **k = 10:** จำนวน VG_chat items ในชุด VG10 ของ AMENDMENT-7 B2.1 ทุกเกณฑ์ด้านล่างนับเฉพาะ 10 ข้อนี้
- **ระดับต่อ app**
  - **reproduced:** Form A มี GF cell อย่างน้อยหนึ่ง cell
  - **not reproduced:** ไม่มี GF cell ทั้ง Form A และ Form B และ Form A มี clean cells อย่างน้อย k − 1
  - **partially reproduced:** กรณีอื่นทั้งหมด ได้แก่
    - Form A ไม่มี GF แต่ Form B มี
    - หรือไม่มี GF ทั้งสอง form แต่ Form A มี clean cells น้อยกว่า k − 1
- **กฎถ้อยคำในเล่ม**
  - **ทุก app:** รายงานจำนวน GF cell เป็น "a of k" พร้อมวันที่ป้อนและ "single shot" เสมอ ห้ามแปลงเป็นร้อยละพร้อม CI
  - **app ที่ "reproduced":** เขียนได้ว่า "the failure also appeared in the free [app]"
  - **app ที่ "not reproduced" แต่ proxy (แขน B) มี GF บนข้อเดียวกัน:**
    ต้องเขียนว่า "not observed in [app] on [date], although its API proxy showed it"
  - **app ที่ "not reproduced" และ proxy ไม่มี GF:** เขียนว่าทั้ง app และ proxy ไม่แสดงความผิดแบบนี้
  - **ไม่มี app ใด "reproduced":** เล่มต้องระบุว่าข้อค้นพบด้าน value grounding ยืนยันได้ในระดับ API proxy เท่านั้น
    - ถ้าทุก app เป็น "not reproduced": เขียนได้ว่า free apps ไม่แสดงความผิดนี้ในวันที่ทดสอบ
    - ถ้ามี app ใดเป็น "partially reproduced": ห้ามเขียนว่า free apps ไม่แสดงความผิดนี้ ให้ใช้ถ้อยคำของ partially สำหรับ app นั้น
    - ข้อเสนอใน Discussion เรื่องค่าที่เก็บจริงต้องเขียนในระดับ proxy
  - **"partially reproduced":** เขียนตามจริงว่าเกิดเฉพาะใน Form B หรือว่าคำตอบของ app ไม่สะอาดพอที่จะสรุป
- **กฎเรื่องความเงียบ (Form B ต่อ app)**
  - ถ้า FLAGGED + ASKED มีอย่างน้อยครึ่งหนึ่งของ cell ที่ผิดหรือไม่มี SQL
    ห้ามบรรยายความผิดของ app นั้นว่า silent และให้เขียนว่า "flagged or asked in m of n wrong replies"
  - ถ้าน้อยกว่าครึ่ง เขียนได้ว่า "most wrong replies gave no warning (s of n)" โดย s คือจำนวนคำตอบที่ code เป็น SILENT
    (s = n − m เมื่อ m = FLAGGED + ASKED) ประโยคนี้จึงอ่านเป็นจริงตามตัวเลขที่ใส่
- **non-VG (Form B, 8 ข้อ):** รายงานเชิงพรรณนาเท่านั้น ได้แก่ จำนวนข้อที่ถูก, concordance กับ proxy,
  การแยก empty กับ non-empty ของข้อที่ผิด และ silence code

**11. การรายงาน**
- นับเชิงพรรณนาเท่านั้น ไม่มี CI และไม่มีการทดสอบ
- ตารางเต็มต่อ app × form × item อยู่ใน artifact
- ในเล่มใช้ย่อหน้าสั้น ความยาวขึ้นกับ page budget
- รายงานทุกทิศทาง รวมกรณีที่ app ไม่แสดงความผิดพลาดของ proxy

**12. ข้อจำกัดที่ประกาศล่วงหน้า**
- **ขนาดและเวลา:** ช่วงไม่เกิน 3 วัน, single shot ต่อ cell และ n = k = 10 ต่อ app ต่อ form บน VG
- **โมเดลใน app:** app เปลี่ยนโมเดลหรือ routing ได้โดยไม่แจ้ง ไม่มีเลขเวอร์ชัน
  และ free plan อาจสลับไปรุ่นเล็กเมื่อเกินโควตา จึงบันทึกป้ายโมเดลที่ UI แสดงทุก cell
- **Form A:** วางเป็น user message ไม่ใช่ system message จึงไม่เท่ากับเงื่อนไขของ API ทุกประการ
- **ผู้ป้อน:** คือผู้เขียน ไม่ใช่นักศึกษา และ Form B เป็นสำนวนที่ผู้สอนเขียน
- **drift:** ความต่างจาก run-of-record เดือน ส.ค. แยกได้ผ่านแขน B ที่รันพร้อมกันเท่านั้น

**13. จริยธรรมและข้อกำหนดการใช้งาน**
- **ไม่มีผู้เข้าร่วมวิจัย:** ผู้เขียนป้อน prompt ที่ผู้เขียนเขียนเองลงบัญชีของตนเอง จึงไม่มีข้อมูลของมนุษย์อื่น
  - amendment นี้ไม่อ้างว่ามีการอนุมัติด้านจริยธรรมใดๆ
- **prompt ที่นักศึกษาเขียนจริงและ classroom study:** เป็น phase 2 ตามบรรทัด 4 ของ prereg
  และต้องผ่านการพิจารณาจริยธรรมและได้รับความยินยอม (consent) ก่อนเก็บข้อมูล ซึ่งยังไม่ได้ดำเนินการ
- **ข้อกำหนดการใช้งาน**
  - ข้อกำหนดผู้ใช้ทั่วไปของ Anthropic ห้ามการเข้าถึงบริการด้วยวิธีอัตโนมัติ (ยกเว้นผ่าน API key)
    และของ Google ห้ามการเข้าถึงเนื้อหาด้วยวิธีอัตโนมัติที่ขัดกับ machine-readable instructions
    (workflow ก่อนหน้าอ่านจากหน้าจริงเมื่อ 12 ต.ค. 2026; เล่มและ Response จะอ้างข้อกำหนดเหล่านี้เฉพาะเมื่อผู้เขียนเปิดอ่านหน้าจริงแล้ว)
  - หน้าข้อกำหนดของ OpenAI ตอบ 403 ต่อผู้ช่วย เล่มและ Response จะอ้างข้อกำหนดเหล่านี้เฉพาะเมื่อผู้เขียนเปิดอ่านหน้าจริงแล้ว

**14. ข้อมูลที่ผู้ร่างเห็น (เปิดเผย)**
- ผู้ร่างเห็นผลทางการของ key v1.2 ซึ่งเป็นฐานของรายการ non-VG เดิมที่ถอนไปแล้ว
- ผู้ร่างเห็นผลของการสุ่มแบบเดิม (ต่อ tier) ด้วย seed เดียวกันบนผลทดสอบของ key v1.3
  - error pool ของ T1 ว่าง, T2 ได้ Q25, T3 ได้ Q41, T4 ได้ Q57
  - correct pool ได้ Q10, Q16, Q31 และ Q59 (ทดสอบ)
- ผู้ร่างเห็นผลของการสุ่มแบบกฎเดิม (ต่อ tier) บนผลทดสอบของ key v1.3n บน k3n ด้วย (T2 ได้ Q25 และ correct pool มี Q16)
- กฎในหัวข้อ 4 เขียนหลังเห็นผลข้างต้น เพื่อแก้ปัญหา pool ว่าง
- dry-run ของ Gate 0 (14 ต.ค. 2026; ทดสอบ) รันกฎใหม่ของหัวข้อ 4 บน regrade ทดสอบของ log ส.ค. บนสำเนา k3n เพื่อตรวจว่าคำสั่งของผู้เขียนทำงานได้
  ผลเก็บแบบปิดตัวเลข (ตัวเลขทุกตัวแทนด้วย #) และไม่แสดง ผู้ร่างเห็นเพียงว่าได้ 18 ข้อและ 28 cells ต่อ app ไม่เห็นรายการข้อ
- รายการทางการได้จากการรันของผู้เขียนบน regrade ทางการเท่านั้น
- **ขอบเขตของการปิดตา:** re-grade ด้วย key v1.3 เป็น deterministic ผลทางการที่ใช้สุ่มจึงคาดว่าจะเท่ากับผลทดสอบที่ผู้ร่างเห็นแล้ว
  (ผู้เขียนเห็นเฉพาะตัวเลขทดสอบบางตัวที่บันทึกไว้ใน master log) และ memo D7 แสดงผลการสุ่มแบบเดิมบน v1.3 (ผู้เขียนไม่ได้อ่านตารางผลรายโมเดลใน memo)
  รายการข้อจึงคำนวณได้ล่วงหน้าจากข้อมูลที่มีอยู่
  การตรึงกฎก่อน re-grade ทางการจึงตรึงขั้นตอน ไม่ได้ปิดตาจากผลของ proxy
  ส่วนที่ปิดตาจริงคือคำตอบของ chat app ซึ่งยังไม่มีจนกว่าจะถึงแชตแรก
- ผู้ทบทวนร่าง (12 ต.ค. 2026 ดึก) ไม่ได้รันกฎใหม่เช่นกัน

## AMENDMENT-9 (19 ต.ค. 2026 — ชุดขยาย 40 ข้อของรอบ ต.ค.; commit พร้อม Gate 1b ก่อน model call แรกของรอบ ต.ค.)

**สถานะ:** ส่วนเพิ่มของรอบ ต.ค. ซึ่งเป็น experiment ใหม่ด้วยวิธีเดิม (AMENDMENT-7 Part 0) ผลทั้งหมดของชุดขยายเป็นเชิงพรรณนา
- ไม่เปลี่ยน core 60 ข้อ, H1–H4, answer key ของ core (AMENDMENT-7 Part C) หรือสถิติหลักใดๆ
- ไม่เข้า H1–H4 และไม่นับรวมในการนับของมติ D6

**ที่มา:** decision ของ KST 2027 ลงวันที่ 10 ต.ค. 2026 (ขนาดของ suite), มติผู้เขียน 13 ต.ค. 2026 (ชุดขยาย 40 ข้อ, การ grade หลาย instance MI-1b,
ข้อสำรองและการใช้ AI) และ 14 ต.ค. 2026 (การตัดสินคำแปลและการตัด EN ให้มีเนื้อความเท่ากับ TH, มติ D10 และ D11)
(บันทึกใน `KST_REVISION_2026-10-12.md`)

**ฐานข้อมูล key และ grader:** ฐาน k3n ตามกฎข้อมูลของ AMENDMENT-7, กฎ R-v1.3 (G1–G4) และ `harness/grade_v13n.py` ตัวเดียวกับ core

### 1. รายการข้อ
- ชุดขยาย 40 ข้อตามลำดับรัน: X01, X02, X03, X04, X05, X07, X08, X09, X10, X11, X12, X13, X14, X17, X18, X19, X20, X21, X23, X24, X25, X26, X27, X28, R5, F7C-6, F7C-2, F7C-8, F7C-1, F7C-3, X33, X34, X35, X36, X37, X38, PK1, FK1, FK2, FK3
- ตระกูล (ลำดับรันเรียงตามตระกูล F1 ถึง F10): F1 5, F2 4, F3 4, F4 5, F5 3, F6 4, F7 5, F8 4, F9 2, F10 4; tier: T2 3, T3 3, T4 34
- ข้อสำรอง: F7C-7, F7C-5, F7C-4, FK4 (ไฟล์ข้อสำรองติดป้าย DRAFT จนกว่าจะใช้กฎข้อสำรอง)
- ข้อที่ตัด: X06, X15, X16, X22, X29, X30, X31, X32, X39, X40, R1, R2, R3, R4
- ข้อมีทิศทาง: X34, X37, F7C-6 และ FK4 ถ้าใช้ข้อสำรอง
- ข้อหลาย instance (กฎ MI-1b): PK1, FK1, FK2; FK3 grade แบบ instance เดียวบน k3n
- ข้อ VG ตามกฎของ AMENDMENT-6 บนข้อความไทยฉบับสุดท้าย (ทดสอบ): X10, X26, X27, F7C-1, F7C-2, F7C-3

### 2. กฎข้อสำรอง
กฎข้อสำรองของ AMENDMENT-9: (1) ค่าตั้งต้นคือไม่ใช้ข้อสำรอง และไฟล์ข้อสำรองติดป้าย DRAFT ทุกแถว (2) ข้อสำรองแทนข้อในชุด 40 ข้อได้เฉพาะก่อน call แรกของชุดขยาย และเฉพาะเมื่อผู้เขียนยืนยันว่าข้อนั้นมีข้อบกพร่องของคำแปลที่ทำให้ EN และ TH ถามคนละคำถาม โดยบันทึกเป็น addendum ลงวันที่ ซึ่งตรึง suite ฉบับ FROZEN ใหม่และ prompts ของ dry-run ก่อน call แรก (3) การเลือกใช้ข้อสำรองในตระกูลเดียวกันก่อน (F7: F7C-7, F7C-5, F7C-4; F10: FK4) ถ้าตระกูลนั้นไม่มีข้อสำรอง ใช้ตามลำดับ F7C-7, F7C-5, F7C-4, FK4 ข้อสำรองที่นำมาใช้ต้องแก้ TH ตามรายงานการตรวจคำแปลก่อนตรึง และรันครบทั้งหกโมเดล (2 ภาษา × 5 run แขน base) โดย FK4 ใช้ข้อยกเว้นลำดับคอลัมน์ที่มีทิศทางตาม brief 1.2 (4) หลัง call แรกของชุดขยายไม่มีการแทนหรือตัดข้อใด ข้อที่พบว่า gold ผิดแก้ด้วย R-v1.3 (D1/D2) และรายงานทั้งผลตาม key เดิมและ key ที่แก้ (5) การแทนที่ทุกครั้งรายงานในเล่ม

### 3. การสร้าง suite และการตรึง
- **ตัวสร้าง:** `harness/build_ext_suite.py` สร้าง `suite/k3n_ext_suite_v1.0.tsv`, `suite/k3n_ext_reserves_v1.0.tsv` และ `suite/ITEM_CHANGES_ext_v1.0.tsv`
  ด้วย `--freeze` บนฐาน k3n ใน Gate 1a และเขียน `results/ext/build/ext_build_report.md` กับ `results/ext/build/ext_inputs.sha256`
- **input:** ระบุด้วย label กลางแทนชื่อไฟล์: selection_xlsx, translation_fixes_xlsx, typo_fixes, item_changes, items_json,
  sql_TESTONLY (digest ของโฟลเดอร์ และไฟล์ SQL ทุกไฟล์ที่ตัวสร้างอ่าน), item_changes_add, metadata_refresh และ ext_decisions
  - sha256 ของทุก input อยู่ใน `ext_inputs.sha256` และในตาราง FREEZE STAMP (หัวข้อ 10); input ที่อยู่นอก git บันทึกเฉพาะ sha256 พร้อม label
- **เงื่อนไขของ `--freeze`:** ปฏิเสธเมื่อช่องการตัดสินใดของ TRANSLATION_FIXES ว่าง, เมื่อ ext_decisions ยังไม่ได้รับอนุมัติ,
  เมื่อ sha256 ของ ext_decisions ไม่เท่ากับค่าที่ผู้เขียนพิมพ์ (`--approved-decisions-sha256`) และเมื่อไม่ได้ส่งชื่อย่อของสถาบันให้การตรวจตัวตน
  (`--anon-extra`); ข้อที่ไม่ใช่ข้อหลาย instance ซึ่ง gold ว่างบน k3n ถูกปฏิเสธ
- sha256 ของเนื้อหา ext_decisions ที่ผู้เขียนอนุมัติ (ก่อนตั้ง author_approved): `03144a34d6f197db8e18ba13fc4689a6d8150b85447e5c6ab2e4a7b571f73c7d`
- sha256 ของไฟล์ ext_decisions ที่ตรึง (หลังตั้ง author_approved; ต่างจากเนื้อหาที่อนุมัติเฉพาะ author_approved และช่องบันทึกการอนุมัติ)
  ซึ่งผู้เขียนพิมพ์ในขั้นตรึง: `8c333fac7dec3201e84b86dedb150f0a5c8a12cf6088931e0f36a1b0860091d2`
- **ข้อความ EN ตามตัวอักษรที่ผู้เขียนอนุมัติ** (สองข้อที่ช่องข้อเสนอของ workbook ไม่ใช่ข้อความ EN ที่ใช้ได้):
  - FK2: "Suppose President.PartyName is a foreign key that refers to Party.PartyName and is declared ON DELETE RESTRICT, so a party cannot be deleted while any president refers to it. List the parties that could be deleted from Party without violating this foreign key (show PartyName)."
  - X19: "Find presidents whose total years served exceed the average of the presidents born in the same state (show president name and total years served, one row per president)."
- ข้อความ EN ของข้ออื่นตัดให้มีเนื้อความเท่ากับ TH ตามที่ผู้เขียนอนุมัติ (30 ข้อ; 14 ต.ค. 2026) และข้อความ TH ใช้การแก้คำผิดและการตัดสินคำแปลที่บันทึกแล้ว
- `suite/ITEM_CHANGES_ext_v1.0.tsv` บันทึกการเปลี่ยนทุกข้อเทียบกับ workbook การคัดเลือก

### 4. ข้อหลาย instance
- **กฎ MI-1b (ข้อหลาย instance):** คำตอบของข้อที่อยู่ใน manifest `harness/db/mi_manifest_k3n.json` (รูปแบบ kst-mi-2)
  ถูกเมื่อมี key ที่ยอมรับเพียงหนึ่ง key ที่ตรงกับผลของคำตอบบนทุก instance ที่ manifest ระบุสำหรับข้อนั้น
  โดยใช้การเรียงคอลัมน์ (column permutation) แบบเดียวกันบนทุก instance
  - key ที่ยอมรับ คือ gold หลัก หรือ alternative หนึ่งตัวของภาษาของคำตอบ (คำตอบภาษาอังกฤษเทียบ `alt_gold_en`
    คำตอบภาษาไทยเทียบ `alt_gold_th`); การผ่านด้วย key ต่างกันบน instance ต่างกันถือว่าผิด
  - การเทียบบนแต่ละ instance ใช้กฎ R-v1.3 (G1–G4) และ col_roles ของข้อเหมือนข้อที่ใช้ instance เดียว
    ชุด permutation ที่ key นั้นผ่านต้องมีส่วนร่วมอย่างน้อยหนึ่งแบบในทุก instance;
    instance ที่ทั้ง key และคำตอบได้ผลว่างไม่จำกัด permutation
  - คำตอบที่รันไม่สำเร็จ (error หรือ timeout) บน instance ใด ถือว่าผิด
  - sensitivity แบบ positional (correct_positional) ถูกเมื่อ permutation เอกลักษณ์ (identity) อยู่ในส่วนร่วมนั้น
- **instance ต่อข้อ:** PK1 ห้า instance (k3n, k3_pk_n_named, k3_pk_n_dup, k3_pk_n_pnull, k3_pk_n_spdup);
  FK1 สาม instance (k3n, k3_fk_i_null, k3_fk_i_orphan); FK2 สอง instance (k3n, k3_fk_i_null);
  FK3 ไม่อยู่ในรายการข้อหลาย instance ของ manifest และ grade แบบ instance เดียวบน k3n;
  ข้อสำรอง FK4 ไม่อยู่ในรายการข้อหลาย instance ของ manifest
- **ข้อยกเว้นจาก D3 ของ FK1:** gold ของ FK1 ว่างบน k3n และบน k3_fk_i_null โดยตั้งใจ
  (ค่า NULL ของ foreign key ที่ยอมให้เป็น NULL ไม่ใช่การละเมิด) กฎ D3 ที่ตัดข้อที่ gold ว่างบนฐานที่รันจึงไม่ใช้กับ FK1;
  ข้อหลาย instance ถูกตัดได้จากสถานะ `v13_status` ของ suite เท่านั้น และ grader ปฏิเสธ suite ที่ตัดข้อใน manifest
- **การตรวจก่อน grade:** ฐานหลักและทุก instance ต้องมี fingerprint ตรงกับค่าที่ `harness/db/build_instances.py --record`
  บันทึกใน manifest บนเครื่อง run-of-record และ gold ต้องให้ผลตาม `expected_gold` ของ manifest บนทุก instance
  มิฉะนั้น grader ไม่ grade
- **การรายงาน:** exec_ok หมายถึงรันสำเร็จบนทุก instance; n_rows มาจากฐานหลัก; matched_gold คือ key ที่ผ่านกฎ MI-1b
  (ว่างเมื่อผิด); ไฟล์ `--mi-log` บันทึกผลราย instance และ `harness/analyze_ext.py` รายงานตารางความล้มเหลวราย instance
  (fail_reason มาจาก instance แรกตามลำดับของ manifest ที่ไม่มี key ใดตรง หรือเป็น 'wrong-result'
  เมื่อผ่านด้วย key ต่างกันหรือ permutation ไม่ตรงกันระหว่าง instance)
- กฎนี้แทนกฎ MI-1 ของร่างเดิม (ซึ่งยอมให้ permutation ต่างกันระหว่าง instance) ตามข้อค้นพบของการตรวจทานวันที่ 13 ต.ค. 2026
  ก่อนการลงทะเบียน
- **คำตอบที่ตรึงล่วงหน้า:** `harness/answers_mi_PREREG_v2_frozen.py` (gold, คำตอบถูกแบบอื่น และ foil ของ PK1, FK1 และ FK2 พร้อมผลที่คาดต่อ instance)
  ตรึงด้วย sha256 ก่อนรันบน instance ใดที่สร้างจาก k3n และ `harness/selftest_mi.py` ตรวจว่าทุกคำตอบได้ผลตามที่คาด
- ผล selftest_mi บน suite frozen: PASS (`SELF-TEST MI-1b: PASS`; manifest สถานะ RECORDED; คำตอบที่ถูกตามกฎ MI-1b: PK1 11 จาก 45, FK1 4 จาก 13 และ FK2 4 จาก 7; ผลของทุกคำตอบตรงกับผลที่คาดในไฟล์คำตอบที่ตรึง (prediction misses 0); guard ปฏิเสธ input ที่ผิดครบ 10 กรณี)

### 5. ข้อมีทิศทาง (ข้อยกเว้นของ G1)
- กฎเดียวกับ core (AMENDMENT-7 Part C2): ให้คะแนนลำดับภายในกลุ่มคอลัมน์ที่มีบทบาทเท่านั้น (คอลัมน์ `col_roles` ของ suite)
  - X34 `2,3`, X37 `0,1`, F7C-6 `0,1` และ FK4 `1,2` ถ้าใช้ข้อสำรอง
  - ข้อยกเว้นลำดับคอลัมน์ของ FK4 ที่กฎข้อสำรอง (หัวข้อ 2) อ้างถึงด้วย "brief 1.2" (มติของผู้เขียนเรื่อง G1 ในเอกสารเตรียมงาน) คือ col_roles `1,2` ข้างบน
- sensitivity: G1 ล้วน (`--no-col-roles`) และเทียบตามตำแหน่งทั้ง projection (`--colperm off`)

### 6. การรัน
- **ขนาด:** 40 ข้อ × 2 ภาษา × 5 runs = 400 records ต่อโมเดล แขน base อย่างเดียว ทั้งหกโมเดล (รวม 2,400 records)
- **runner และ payload:** ตัวเดียวกับ core (AMENDMENT-7 A2–A5) รวม echo lock; dry-run บันทึก prompt ที่ไม่ซ้ำกัน 80 แบบ และตรวจด้วย `harness/check_prompts_rc1.py`
  ก่อน call แรก; live run ปฏิเสธ suite หรือ prompt log ที่ติดป้าย DRAFT
- **ลำดับ:** ในแต่ละ terminal รัน core ของทุกโมเดลก่อน แล้วชุดขยายตามลำดับโมเดลเดียวกัน (terminal 1: gpt-mini, gemini-flash, claude-sonnet;
  terminal 2: llama31-8b, qwen25-coder-7b, typhoon2-8b) และใช้ `--not-before` เดียวกับ core (เวลา commit ของ Gate 1b)
- **ไฟล์ผล:** `results/ext/results_ext_api.jsonl` และ `results/ext/results_ext_local.jsonl` (append-only และ resume ได้)
- **ก่อน grade:** `harness/check_rc1_log.py` ต้อง PASS check 1–7 (ชุดขยายไม่มี check 8 เพราะไม่มีคู่ของสองแขน)

### 7. การให้คะแนน
- `harness/grade_v13n.py` กับ suite ชุดขยายบน k3n พร้อม manifest ของข้อหลาย instance (`--mi-manifest`) และไฟล์ผลราย instance (`--mi-log`)
- ก่อน grade ผู้เขียนตรวจ gold, fingerprint และ schema ของทุก instance ซ้ำ (`harness/db/build_instances.py --check-gold-only`)
- sensitivity: เทียบตามตำแหน่ง (`--colperm off`) และ G1 ล้วน (`--no-col-roles`); บนฐาน k3 grade เฉพาะ 37 ข้อที่ใช้ instance เดียว (artifact เท่านั้น)
- ข้อใดถูกตัดได้จากสถานะ `v13_status` ของ suite เท่านั้น gold ว่างไม่ตัดข้อหลาย instance (FK1 คงอยู่)

### 8. การวิเคราะห์ที่ประกาศล่วงหน้า
- ผลของชุดขยายทั้งหมดจาก `harness/analyze_ext.py` เป็นผลเชิงพรรณนา (exploratory/descriptive) และรายงานทุกทิศ:
  accuracy ต่อโมเดล × ภาษาพร้อม Wilson 95%, จำนวนข้อที่ถูกต่อ family F1–F10, EN−TH discordant b/c และ exact McNemar ต่อโมเดล (ไม่อ้าง Holm),
  การแยก loud / silent-empty / silent-non-empty, ตารางความล้มเหลวราย instance ของข้อ MI และ positional sensitivity ของ X34, X37 และ F7C-6
- ชุดขยายไม่เข้า H1–H4 และไม่นับรวมในการนับของมติ D6
- pooled 100 ข้อ (core 60 ของรอบ ต.ค. แขน base ซึ่งรวม Q27 ฉบับซ่อม + ชุดขยาย 40): sensitivity ที่ประกาศล่วงหน้า
  รายงาน accuracy ต่อโมเดล × ภาษาพร้อม Wilson 95% และ exact McNemar EN–TH ทุกทิศ และไม่ใช้ยกระดับ claim;
  ผลหลักแยกชุด (core 60 เป็นผลหลัก ชุดขยาย 40 เป็นผลเชิงพรรณนา); log ส.ค. ไม่ถูกรวมกับข้อมูลรอบ ต.ค.
- VG ของชุดขยาย (X10, X26, X27, F7C-1, F7C-2, F7C-3; ทดสอบ): รายงานจำนวนคลาสของ B2.3 เชิงพรรณนาใน artifact และไม่เกินหนึ่งประโยคในเล่ม
- ข้อ MI (PK1, FK1, FK2) ไม่เข้าการแยก empty/non-empty เพราะ n_rows มาจาก base instance เท่านั้น และรายงานตารางราย instance แยก
- ตาราง hardness แบบ Spider คำนวณจาก gold ที่ตรึงของ 100 ข้อ (core 60 ของรอบ ต.ค. และชุดขยาย 40) อยู่ใน artifact และไม่ใช้เลือกข้อหรือวิเคราะห์
- sensitivity บน k3: grade 37 ข้อที่ใช้ instance เดียว (ตัด PK1, FK1, FK2) บน k3 ใน artifact เท่านั้น

### 9. การเปิดเผย
- ค่า literal ของ PK1 (ค่าสังเคราะห์ที่ผู้เขียนอนุมัติ 14 ต.ค. 2026 และเปิดเผยตามนี้): ชื่อคู่สมรสสังเคราะห์ 'Planted Spouse' ใน instance named,
  ชื่อซ้ำ 'Mary Todd' ใน instance spdup, แถว Buchanan ของฉบับ named เป็นแถวที่ PresidentName เป็น NULL ใน instance pnull
  และแถวซ้ำเฉพาะ key ของ Cleveland สถานะ 'Widowed' ใน instance dup
- ก่อนตรึงคำตอบและ instance ผู้ช่วยเห็นผลจำลองของคำตอบ PK 45 แบบบน instance ที่จำลองด้วย CTE (TEST-ONLY) ไม่มีผลของโมเดลและไม่มีข้อมูลนักศึกษา
- คำตอบรูป COUNT(DISTINCT ชื่อที่ต่อด้วยตัวคั่น) เทียบ COUNT(*) ถือว่าถูก ชุด instance ไม่แยกกรณีตัวคั่นชนกัน
  การ grade หลาย instance จึงเป็นขอบบนของความถูก
- ถ้อยคำของ PK1: หลังตัด EN ให้มีเนื้อความเท่ากับ TH ตามที่ผู้เขียนอนุมัติ ทั้ง EN และ TH ไม่ระบุชื่อตาราง PresidentMarriage
  เพราะคู่คอลัมน์ (PresidentName, SpouseName) มีอยู่เฉพาะในตาราง PresidentMarriage โจทย์จึงไม่กำกวม
- foil ของ PK1 ที่ไฟล์คำตอบติดป้าย 'classroom' คือ SQL ที่ผู้ช่วยร่างจากรูปคำตอบสองรูปที่ผู้เขียนรายงานจากห้องเรียน
  (uniqueness-only และ nullity-only ของ PK; drafted by the assistant from answer forms reported by the author) ไม่มีข้อความหรือจำนวนจากนักศึกษา;
  constant YES/NO และ catalog-based เป็น assistant-devised loophole foil; foil ของ FK เป็น derived from the instructor's answer key หรือ assistant-devised;
  ไฟล์คำตอบ (`harness/answers_mi_PREREG_v2_frozen.py`) ตรึงด้วย sha256 ก่อนรันบน instance ใดที่สร้างจาก k3n
- author_class: 'author' = โจทย์ที่ผู้เขียนเขียน (ชุด 200 ข้อ และ R5); 'assistant-drafted' = EN ที่ผู้ช่วยร่าง (F7C-*, ข้อใหม่ของ F8/F9,
  PK1, FK1–FK3) และ PK1, FK1–FK3 ระบุ 'adapted from the author's exam item' เพิ่ม
- การใช้ AI: ผู้ช่วยร่าง gold SQL ของทุกข้อในชุดขยาย และร่างหรือดัดแปลง EN ของข้อที่ระบุข้างบน ผู้เขียนอนุมัติทุกข้อ (ai_drafted = yes)
- ไฟล์ข้อสำรองเผยแพร่ใน artifact พร้อมป้าย 'not run' และ hash อยู่ใน amendment นี้ทุกกรณี
- ลำดับรัน: ในแต่ละ terminal รัน core ของทุกโมเดลก่อน แล้วชุดขยายตามลำดับโมเดลเดียวกัน แขน base และ NOT_BEFORE เดียวกับ core
- FK3 ไม่อยู่ใน manifest และ grade แบบ instance เดียวบน k3n

**การตรวจ foil และ alternative ก่อนตรึง**
- ก่อนตรึง ผู้ช่วยรัน foil (คำตอบผิดที่เขียนล่วงหน้า) และ alternative (คำตอบถูกแบบอื่น) ของชุดขยายบน k3n เทียบกับ gold ที่ตรึง (ทดสอบ)
  - ชุด F7C (8 ข้อรวมข้อสำรอง 3 ข้อ): foil ผิด 40/41 ภายใต้ G1 และ 41/41 เมื่อใช้ col_roles (foil ที่สลับทิศของ F7C-6 ถูกภายใต้ G1 ล้วน);
    alternative ถูก 30/30
  - ชุด X และ R5 (31 ข้อ): ชุดตรวจคือบันทึกทั้งหมดของการคัดเลือกบน k3 คือ foil 191 รายการ และ alternative 83 รายการ
    (รวม gold ของรอบคัดกรอง 6 รายการ); ตัวเลขในแบบงาน (185/203 และ 89/89) ไม่มีไฟล์ต้นทาง จึงใช้ตัวเลขที่สร้างจากบันทึก
  - ถอน 3 รายการที่เขียนสำหรับ gold เดิมของ X37 (gold เปลี่ยนหลังการคัดเลือกตามมติ 13 ต.ค.: ตัด CASE ที่แปลงชื่อและเทียบชื่อตามที่เก็บ):
    foil 'no_name_mapping' (ตอนนี้เป็นความหมายของ gold เอง) และ alternative 'two_level_join_no_recursion' และ
    'replace_based_mapping_cycle_guard'; รายการที่ถอนไม่นับเป็นถูกหรือผิด
  - หลังถอน: foil ผิด 174/190 และ alternative ถูก 81/81; foil 16 รายการที่ได้ผลถูกบน k3n มีคำอธิบายครบ ได้แก่ 11 รายการที่ถูกบน k3 อยู่แล้ว,
    1 รายการที่ต่างจาก gold เฉพาะลำดับคอลัมน์ (ถูกตาม G1) และ 4 รายการที่อ่าน cell ซึ่งเปลี่ยนจาก 'None' เป็น NULL บน k3n
  - foil ใหม่ของ X37 ที่นับเฉพาะคู่ที่ต่อกันตรง (10 แถว) ผิดตามคาด (gold 11 แถว)

**ข้อมูลที่ผู้ร่างเห็นก่อนตรึง**
- ข้อของชุดขยายถูกเลือกหลังผู้ร่างและผู้เขียนเห็นผลของ log ส.ค. บน core และผู้ช่วยร่างบางข้อ (ป้าย author_class) ผลของชุดขยายจึงเป็นเชิงพรรณนาเท่านั้น
- ผลของ gold ทุกข้อบน k3n (จำนวนแถวและคอลัมน์; ทดสอบ) ที่ตัวสร้าง suite พิมพ์ในรายงานการสร้าง
- ผลของคำตอบที่ตรึงของข้อหลาย instance บน instance ที่สร้างจาก k3n (ทดสอบ): gold ของ PK1 บนห้า instance เป็น NO, YES, NO, NO, YES;
  คำตอบที่ถูกตามกฎ MI-1b คือ PK1 11 จาก 45 แบบ, FK1 4 จาก 13 แบบ และ FK2 4 จาก 7 แบบ
- ผลของ foil และ alternative ตามหัวข้อการตรวจ foil ข้างบน
- ไม่มีผลของโมเดลใดต่อข้อของชุดขยาย เพราะยังไม่มีการเรียกโมเดล

### 10. FREEZE STAMP ของ AMENDMENT-9 (กรอกตอน commit Gate 1b)
- วันเวลา commit, git commit และสถานะ push: บันทึกใน addendum ของ commit Gate 2 (commit ใส่ hash ของตัวเองไม่ได้)
- ผล parity ของ grader รอบสุดท้ายพร้อม manifest และ gold ของชุดขยาย: PARITY: PASS (`parity_grader.py --final`; บรรทัด 'P3 extension golds (MI-1b, arm base)' PASS 80/80; P1 เก้าบรรทัด IDENTICAL รวมโหมด manifest; P2 3,600/3,600 IDENTICAL; P3 two-arm 944/944 PASS; ไม่มีบรรทัด SKIPPED)
- sha256 ของไฟล์ (suite ชุดขยายและข้อสำรอง, ไฟล์บันทึกการเปลี่ยน, input ของตัวสร้างด้วย label กลาง, ตัวสร้าง, manifest ที่ record แล้ว,
  คำตอบที่ตรึง, selftest_mi, prompt log ของ dry-run และสคริปต์วิเคราะห์ของชุดขยาย):

| ไฟล์ | sha256 |
|---|---|
| `harness/db/build_instances.py` | `49550be85f53ad5362ed68b39fa4aed46e75913f2287732e63ef72247bd4e692` |
| `harness/db/mi_manifest_k3n.json` | `98d0ce0e11a0ee2df5f41412a4c36d98c5a9b5ec896011c8fa9f423856ebe0c5` |
| `harness/db/expected/mi_scratch_TESTONLY.json` | `126cd0530e88988ebd40f832b9e11b89e5a6ffab2e008fbf878fefbcdd10693a` |
| `suite/k3n_ext_suite_v1.0.tsv` | `838c732afd89066835de9f3eb60799029e76364af6f73a472bfee346e7cbdf14` |
| `suite/k3n_ext_reserves_v1.0.tsv` | `c506745567bd99c1415806e6a63a0af92bb2693a1989312f5b240df0e7fce31a` |
| `suite/ITEM_CHANGES_ext_v1.0.tsv` | `f737ada2041321c3cbf1fdc57ac689915144c6d7b1290a46b6e64617a4b22982` |
| `suite/ext_inputs/ext_decisions_2026-10-14.json` | `8c333fac7dec3201e84b86dedb150f0a5c8a12cf6088931e0f36a1b0860091d2` |
| `suite/ext_inputs/ITEM_CHANGES_2026-10-14_ADD.tsv` | `a38d8103a1156f17bc74b4a2ba8f9b16161a12e87c7c2ccbf0510710e5b48920` |
| `suite/ext_inputs/ext_metadata_refresh_2026-10-14.tsv` | `26724a108a08aee3f5a73ca6cef2c9765d66e9ace0f4d609b81436e3418d988a` |
| `harness/build_ext_suite.py` | `85693132b1a9c339b525ca2a5dfb899a8e8db1924f56b30058ac7f9342d806a3` |
| `results/ext/build/ext_build_report.md` | `bfc5dc40b4ce6195127771006b230d9c0b8922b3056060fffd24f656bebfafff` |
| `results/ext/build/ext_inputs.sha256` | `e766032eeec0c540816c9be128e559bb9faf990278310d1446a6bd82c8fbe1b3` |
| `harness/answers_mi_PREREG_v2_frozen.py` | `d708cbd4a6c9c5049c76d2836347cf408a94b442886c47b310097a38da9160db` |
| `harness/selftest_mi.py` | `4112fa1be1469e685e4121b9c5177f88b0ec3a2fd5fb6b0a09f83a7d6d9d1536` |
| `results/ext/prompts_ext.jsonl` | `9bc2b142e1dc42670e7d79efe6598eb9d46240529ec9cf0119c36c2fa60cfd21` |
| `harness/analyze_ext.py` | `334980f09fc95c878f6daf36b04796f9384c4f0dbf719a5cbad5450f82d54a40` |
| `harness/make_table_ext.py` | `5467795b99322efe2f7acb178ee0fceb3e254abb4d94eca71431a8ed03178556` |
| translation_fixes_xlsx | `fd6ffe00a3d81f5d25d68e255abafde43b2f5d33bc394be76e7193489f1125dc` |
| selection_xlsx | `63a7bbe058e25647e4c612be08b1fd549563191d83fd6424814d443d0e16a667` |
| typo_fixes | `d9f8c8673daf70169fb357534dc63dac3c0fdccb4516338b54f19be1ff86c2be` |
| item_changes | `115efabdcfe1006c6e091b3bd03b9d33f5679441dea3b21e6e46db565c5087ba` |
| items_json | `ca89abb17651c59c4a1baeb7d93141a8411fe8356cc324ff9571732f0ae7ce60` |
| sql_TESTONLY (16 ไฟล์; tree hash) | `e9fa6501ff1b3d2d41bdcadfb0841aa68af2cafad2237f671d2575657ef6142a` |
| sql_TESTONLY/F7C-1__alt_whig_excluded.sql | `7ddda6c143bd8794e1f2a77f33fc69c800ed79964f5c5c6e34b510eab0267c42` |
| sql_TESTONLY/FK1__new_format_DRAFT.sql | `f13960c067198c358d3e0015890272fbce55abbf21c638bcf9fc71db8eb84ad3` |
| sql_TESTONLY/X02__weak_every_own_term_longest.sql | `19b5bffe24070365229fce782807dfee3ddab8d3dd0032a49a6d51619f5d90e9` |
| sql_TESTONLY/X04__weak_every_own_term_shortest.sql | `92ab1b09f5408dcfe3d247dbe13d6c3114ac36f45f3443da434ff4ed888180e2` |
| sql_TESTONLY/X07__weak_every_own_term_shorter.sql | `47ff392fc5099ab704337ce50496d790bc1359d49ff058150f2202089d631ed8` |
| sql_TESTONLY/X20__alt_exclude_self.sql | `e5ab15d478adbe8bb8d74b2c4f2f778864d30a062a5747e56bd263952b8f89b2` |
| sql_TESTONLY/X33__alt_runnerup_and_president.sql | `4b03855ab0024de2e8c3454b181bd0c6ae632680b1fd8ef404f8d29189de0bd4` |

### AMENDMENT-8 หัวข้อ 15 — FREEZE STAMP ของรายการข้อ (Gate 2; 19 ต.ค. 2026)
- วันเวลา commit, git commit และสถานะ push ของ Gate 2: บันทึกใน addendum ของ commit ผล Gate 3 (commit ใส่ hash ของตัวเองไม่ได้)
- ฐานของการสุ่ม: aug-k3n (`results/v13n/graded_v13n.csv`; ข้อมูลรอง) sha256 `30d29a826b57fcf3ff56e05241ad5c67656a1966b3538b16d4236bd7c54e46f8` และ `suite/k3n_suite_v1.3n.tsv` sha256 `195839ec46f902901f03e90965c00bb1b78b4ef6bc970f4cabb0ed0272997366`
- ขนาดของ pool: |E| = 8, |C| = 39
- NONVG: Q41, Q50, Q25, Q43, Q35, Q18, Q02, Q55
- sha256 ของรายการ 18 ข้อ: `262b3d240057a47039c781a57a3a5338e767658adea08b5350cf3dd8112fff05`
- sha256 ของลำดับก่อนสลับ (pre-shuffle) จาก `make_chat_cells.py`: `6f358b2d0f6a329eb9859462649cc5c07d5f9bed9fef6fdb5bcc55bb7691d3cf`
- sha256 ของ `cells.tsv`: `ec805ee0a21e972da8fbeb8b1d63f73f4f810f9896dcd9b14b937b1b4ab0ff50` / `cells_meta.json` (seed, pre-shuffle และเวลาสร้าง prompt): `ed4d3dc788cc42f7c598ff1404cec379190689bf930e32627b29f820ee332639` / tree hash ของ `prompts/`: `60e53351e3141a1d3865afb74bacd229218308242aaadc077b31340e4dfe3d29`
  / `prompts/TURN2.txt`: `c220925a94346625b3c1510d7114fd55c1e18bc9793359fe512dc5c70fddbfc7` / แม่แบบ `CHAT_LOG.xlsx`: `a73d65512e120490327120ec2be5894963b88844fe04c266f053bbf1b71b4c60`
- sha256 ของสคริปต์ (commit ใน Gate 1b): `draw_chat_items_v13.py` `12632f46b26904c909d538746135c17df333a4b6f212e92124da925306a0f9e5`, `make_chat_cells.py` `5d3e00d3747456d501266a34f423c3bfdcc108df7b744ccdfdf8ff83c379f00e`,
  `chatapp_to_results.py` `f70be7fb86e75bdc554f7b3f9847954b98bd63e47fe7cc8156e9b22f6ff6eb67`, `vg_outcome.py` `659dff5696df68a0fa4a7f673f5fce3d78b6bcebae07d13c0e7408298da7fc0d`; สคริปต์อื่นของ kit และ `harness/vg_classifier.py` อยู่ใน FREEZE STAMP ของ AMENDMENT-7
- `raw_manifest.tsv` (sha256 ของไฟล์ raw ทุกไฟล์) บันทึกใน addendum หลังแชตครบ
- **บัญชี**
  - ChatGPT free: บัญชี free ที่ผู้เขียนสมัครใหม่สำหรับ check นี้ด้วยบัญชี Google ของ Gemini ข้างล่าง ไม่มี subscription
  - Gemini: บัญชี Google ส่วนบุคคล (@gmail.com) แยกต่างหากของผู้เขียน ไม่มีแผน AI แบบเสียเงิน และไม่เคยใช้กับ LLM app (ไม่ใช้บัญชี Google ที่มีแผน AI แบบเสียเงินของผู้เขียน)
  - Claude.ai free: บัญชี free ที่ผู้เขียนสมัครใหม่สำหรับ check นี้ด้วยบัญชี Google เดียวกัน ไม่มี subscription (ไม่ใช้บัญชีแบบเสียเงินของผู้เขียน)
  - ผู้เขียนสมัคร ChatGPT และ Claude.ai ก่อนแชตแรก ล็อกอินทั้งสาม app เฉพาะใน Chrome profile ข้างล่างซึ่งไม่เคยใช้กับ LLM app และยืนยันบัญชีกับการตั้งค่าในชีต setup ของ `CHAT_LOG.xlsx` และใน addendum หลังแชตครบ
- ชื่อไฟล์ screenshot ของ settings ก่อนเริ่ม: `shots/setup_before_chatgpt.png`, `shots/setup_before_gemini.png`, `shots/setup_before_claude.png`
- browser และเวอร์ชัน: Google Chrome 155.0.8059.82 บน macOS 26.7.1 ใน profile แยกที่ล็อกอินด้วยบัญชี Google ของ Gemini ข้างบนและไม่เคยใช้กับ LLM app (Chrome อัปเดตตัวเอง เวอร์ชันจริงในวันป้อนแชตบันทึกในชีต setup) / ภาษาของ UI: อังกฤษ ทั้งสาม app
- ช่วงวันที่เก็บแขน B ของ AMENDMENT-7 ที่วางแผน: 19–25 ต.ค. 2026 / ช่วงวันที่ป้อนแชตที่วางแผน: ต่อจากการเก็บแขน B ครบทันที ภายใน 19–26 ต.ค. 2026 (วันจริงบันทึกใน addendum หลังแชตครบ)
- ผลของ chat check (`results/chat/` ทั้งโฟลเดอร์) commit แยกหลังแชตครบและหลังรายงาน พร้อม addendum ที่มี sha256 ของ `raw_manifest.tsv`
  และช่วงวันที่ป้อนแชตจริงต่อ app; ก่อน stage ผู้เขียนตรวจว่าไม่มีชื่อบัญชี อีเมล หรือชื่อบุคคลใน `CHAT_LOG.xlsx`, `raw/` และ screenshot ใน `shots/`

#### FREEZE STAMP ของ AMENDMENT-8 หัวข้อ 15 (freeze_stamp.py, 19 ต.ค. 2026 19:13:40)
| ไฟล์ | sha256 |
|---|---|
| `results/v13n/graded_v13n.csv` | `30d29a826b57fcf3ff56e05241ad5c67656a1966b3538b16d4236bd7c54e46f8` |
| `suite/k3n_suite_v1.3n.tsv` | `195839ec46f902901f03e90965c00bb1b78b4ef6bc970f4cabb0ed0272997366` |
| `results/chat/chat_items_v13.json` | `95f8742f1ad0c2e12440e16d655a7540274649b9473d99e7eb7cc31844cec6aa` |
| `results/chat/cells.tsv` | `ec805ee0a21e972da8fbeb8b1d63f73f4f810f9896dcd9b14b937b1b4ab0ff50` |
| `results/chat/cells_meta.json` | `ed4d3dc788cc42f7c598ff1404cec379190689bf930e32627b29f820ee332639` |
| `results/chat/prompts/` (29 ไฟล์; tree hash) | `60e53351e3141a1d3865afb74bacd229218308242aaadc077b31340e4dfe3d29` |
| `results/chat/prompts/TURN2.txt` | `c220925a94346625b3c1510d7114fd55c1e18bc9793359fe512dc5c70fddbfc7` |
| `results/chat/CHAT_LOG.xlsx` | `a73d65512e120490327120ec2be5894963b88844fe04c266f053bbf1b71b4c60` |
| `harness/chatapp/draw_chat_items_v13.py` | `12632f46b26904c909d538746135c17df333a4b6f212e92124da925306a0f9e5` |
| `harness/chatapp/make_chat_cells.py` | `5d3e00d3747456d501266a34f423c3bfdcc108df7b744ccdfdf8ff83c379f00e` |
| `harness/chatapp/chatapp_to_results.py` | `f70be7fb86e75bdc554f7b3f9847954b98bd63e47fe7cc8156e9b22f6ff6eb67` |
| `harness/chatapp/vg_outcome.py` | `659dff5696df68a0fa4a7f673f5fce3d78b6bcebae07d13c0e7408298da7fc0d` |

### Addendum ของ commit Gate 1b (19 ต.ค. 2026)
- git commit `f75e6337312c91ecfd5e439fd4a04781e58ad7ce` บน main เวลา commit 2026-10-19T12:45:08+07:00 (เวลานี้คือ NOT_BEFORE ของรอบ ต.ค.); push ถึง origin แล้ว (c698547..f75e633) ก่อน re-grade ทางการของ log ส.ค. และก่อน model call แรกของรอบ ต.ค.
- prereg หลังต่อท้าย Gate 1b: `prereg/preregistration_FROZEN.md` sha256 `8f891ca1c1c59de3967671f02a240c2c9adecd473a29c13e28512f8ce1c1c118` จำนวน 1914 บรรทัด
- หัวเรื่องของ AMENDMENT-6 ถึง 9 ลงวันที่ 19 ต.ค. 2026 ซึ่งเป็นวันที่ต่อท้ายและ commit; ข้อความประกอบเสร็จวันที่ 14 ต.ค. 2026 และค่าของ Gate 1a ในข้อความมาจากการรันของผู้เขียนวันที่ 14 ต.ค. 2026
- **Python ระหว่าง Gate 1a กับ Gate 1b:** Homebrew ปรับ python@3.14 จาก 3.14.7 (Gate 1a; `provenance_gate1a.json`) เป็น 3.14.8 เมื่อ 18 ต.ค. 2026 ตั้งแต่ Gate 1b ใช้ Python 3.14.8
  - User-Agent ของ urllib ที่ AMENDMENT-7 Part 0 ข้อ 9 อ้างถึงเป็น `Python-urllib/3.14` ทั้งสองเวอร์ชัน (ทดสอบ) request ของรอบ ต.ค. จึงไม่เปลี่ยน
  - ไฟล์ re-grade ทางการของ log ส.ค. (Python 3.14.8) ตรงทุก byte กับ re-grade ทดสอบของ Gate 0 (Python 3.14.7)
  - provenance ของรอบ ต.ค. บันทึกเวอร์ชันที่ใช้จริง; PostgreSQL 16.9 และ Ollama 0.32.5 ไม่เปลี่ยน
  - ตั้งแต่ 19 ต.ค. 2026 ผู้เขียน pin postgresql@16, ollama และ python@3.14 ใน Homebrew จนส่งฉบับสุดท้าย
- **Typhoon:** layer ของโมเดล typhoon2-8b ใน Ollama (ขึ้นต้น d5b2115c; 4,920,736,992 bytes) มีขนาดเท่าไฟล์ GGUF แต่ค่า hash ต่างจาก sha256 ของไฟล์ GGUF (63a0e073…) เพราะ Ollama เขียนไฟล์ใหม่ตอน import ตัวระบุโมเดลที่ใช้คือ sha256 ของไฟล์ GGUF และ digest ของ Ollama ในตารางของ AMENDMENT-7

#### FREEZE STAMP ของ addendum (ผลของ Gate 2; ข้อมูลรอง)
| ไฟล์ | sha256 |
|---|---|
| `results/v13n/` (84 ไฟล์; tree hash) | `81807e08e655a9aeab74c1575f2be087b3804034f0878209fe854ec76e9dfd4c` |
| `results/v13/` (6 ไฟล์; tree hash) | `d4a278bda08342822568e2edbd47f259b167da3a0e0e5473f2e41aab8c75c49c` |

### Addendum ของ commit Gate 2 และการเก็บข้อมูลรอบ ต.ค. (Gate 3; 20 ต.ค. 2026)
- **commit Gate 2:** git commit `f39fe84aa35266cb0fdbab1c1036ba34872278ff` บน main เวลา commit 2026-10-19T19:32:45+07:00 (เวลาเริ่มต้นที่เร็วที่สุดของแชตใน chat check ของ AMENDMENT-8); push ถึง origin แล้ว (f75e633..f39fe84)
- **prereg หลังต่อท้าย Gate 2:** `prereg/preregistration_FROZEN.md` sha256 `5176d0c51f39477f1e3b1dc2e726c1d769967deb6cd0ff18a30c0c66cc6b5408` จำนวน 1970 บรรทัด
- **ยอดเครดิตก่อนเริ่ม (19 ต.ค. 2026; auto-reload ปิดทุกค่าย):** Anthropic US$8.39, OpenAI US$4.79, Gemini API แบบ Prepay THB 679.13
- **ช่วงเวลาที่เก็บ (ts ของ runner, เวลาไทย):** core ผ่าน API 2026-10-19T19:44:40 ถึง 2026-10-20T09:40:31; core local 2026-10-19T19:47:19 ถึง 2026-10-19T23:00:49; ชุดขยายผ่าน API 2026-10-20T09:46:45 ถึง 2026-10-20T12:14:03; ชุดขยาย local 2026-10-19T23:10:11 ถึง 2026-10-20T09:55:31 (อยู่ในช่วง 19–25 ต.ค. ที่วางแผนไว้ใน AMENDMENT-8 หัวข้อ 15)
- **provenance:** ก่อนเริ่มเทียบกับ Gate 1a ต่างเฉพาะ Python 3.14.7 → 3.14.8 (เปิดเผยแล้วใน addendum ของ commit Gate 1b); หลังเก็บครบเทียบกับก่อนเริ่ม ไม่มี field ใดเปลี่ยน ได้แก่ echo ของ API ทั้งสาม, Ollama 0.32.5 และ digest ของทั้งสามโมเดล, sha256 ของไฟล์ GGUF, runner และ models.json
- **ความพร้อมกันของคู่ (check 8):** 3,600 คู่ ไม่พร้อมกัน 0 คู่ในทุกโมเดล
- **core:** 7,200 records สำเร็จทั้งหมดในครั้งแรก ไม่มี error record; check_rc1_log ผ่าน check 1–7

#### ชุดขยาย: error records และการรันซ้ำ
- error records 17 รายการ; AMENDMENT-7 A5 ข้อ 5 กำหนดว่า HTTP error และ timeout ไม่นับเป็นความพยายาม และการ resume เติมเฉพาะ cell ที่ยังไม่ครบ
- **typhoon2-8b:** TimeoutError 11 ครั้ง ทั้งหมดที่ X28 ภาษาไทย (timeout ต่อ call 120 วินาที)
  - รันซ้ำ 2 ครั้ง; กฎหยุด "รันซ้ำอีกครั้งเดียวแล้วหยุด" ตั้งหลังการรันซ้ำครั้งแรกและก่อนครั้งที่สอง
  - เติมได้ 3 cell; X28 ภาษาไทย run 1 และ run 2 timeout ทั้งสามครั้ง จึงเก็บได้ 398 จาก 400 cell
  - ตาม A5 ข้อ 6 รายงานเท่าที่มีพร้อมเหตุผล: ตัดออกจาก check 2–5 ของชุดขยายและจากการวิเคราะห์ชุดขยาย (`--exclude-models`) และรายงานผลของโมเดลนี้บนชุดขยายเชิงพรรณนา
- **gemini-flash:** TimeoutError 1 ครั้ง (X23 ภาษาไทย run 2) สำเร็จในการรันซ้ำครั้งแรก
- **claude-sonnet:** 5 ครั้งที่คำตอบมีเฉพาะ block thinking ไม่มีข้อความ: X07 ภาษาอังกฤษ run 2, X37 ภาษาไทย run 2, X17 ภาษาไทย run 4 และ X37 ภาษาไทย run 5 (2 ครั้ง)
  - runner ส่ง max_tokens 1024 และ claude-sonnet-5 ใช้ thinking แบบ adaptive ที่ effort high ตามค่าตั้งต้นของผู้ให้บริการ
  - กรณีนี้ไม่ใช่ HTTP error หรือ timeout ตามถ้อยคำของ A5 ข้อ 5 แต่ runner ที่ตรึงใน Gate 1a จัดเป็น error record และ resume ถามใหม่; สำเร็จครบหลังรันซ้ำ 2 ครั้ง
- การรันซ้ำของ timeout และของคำตอบที่มีแต่ thinking ขึ้นกับเนื้อหาของข้อ cell ที่เติมได้จากการรันซ้ำจึงอาจเป็นครั้งที่ตอบสั้นกว่า
  เล่มรายงานเป็นข้อจำกัดพร้อมจำนวน (สำเร็จหลังรันซ้ำ: claude-sonnet 4 cell, gemini-flash 1 cell, typhoon2-8b 3 cell; typhoon2-8b ขาด 2 cell); core ไม่มีกรณีนี้
- check_rc1_log ของชุดขยาย: แบบรวมทุกโมเดลไม่ผ่านเฉพาะ check 2 (ขาด typhoon2-8b ภาษาไทย X28 run 1–2); แบบตัด typhoon2-8b ผ่าน check 1–7 (check 7 ยังสแกนทุกบรรทัด)

#### manual audit ของ AMENDMENT-7 A6
- ผู้เขียน code ครบ 186 run จาก audit sheet ที่สลับลำดับแถวและซ่อนแขน โมเดล และคลาสของตัวจำแนก
- agreement 64.5% และ Cohen's κ 0.542 (5 คลาส ระดับ run); ผลตัดสิน GF ต่างกัน 8 จาก 39 cell
- GF ของ frontier แขน B บน VG_cov: ตัวจำแนก 6, ผู้เขียน 5; แขน V: 0 ทั้งสองแบบ; ตัวจำแนกเป็นผลหลักและเล่มรายงานทั้งสองค่า
- ระดับ run ผลตัดสิน GF ตรงกัน 146 จาก 186 run; ความต่างส่วนใหญ่ (30 run) คือตัวจำแนกให้ NO_PRED แต่ผู้เขียนให้ INVENTED ในคำตอบที่ไม่มี literal บนคอลัมน์เป้าหมาย แต่กรองคอลัมน์อื่นแทน (เช่น ประเทศแทนเมือง) หรือใช้ IS NULL; กฎของ B2.3 นับ INVENTED เฉพาะ literal บนคอลัมน์เป้าหมาย ผลของผู้เขียนจึงสะท้อนนิยามที่กว้างกว่า และไม่มีการ code ใหม่หลังเห็นคลาสของตัวจำแนก

#### แก้ข้อความใน AMENDMENT-8 หัวข้อ 15 (commit f39fe84)
- บรรทัดบัญชี Gemini, บรรทัดการล็อกอิน และบรรทัด browser เขียนว่าบัญชี Google และ Chrome profile ไม่เคยใช้กับ LLM app
- หลัง push หน้าแรกของ Gemini app ในบัญชีนั้นแสดงประวัติแชต 1 รายการที่มีอยู่ก่อน check นี้ ข้อความนั้นจึงไม่ถูกต้อง
- ส่วนที่ยังถูกต้อง: บัญชีเป็น @gmail.com ส่วนบุคคล แยกจากบัญชีที่มีแผน AI แบบเสียเงินของผู้เขียน และไม่มีแผน AI แบบเสียเงิน ตามข้อกำหนดของ AMENDMENT-8 หัวข้อ 3; ChatGPT และ Claude.ai เป็นบัญชี free ที่สมัครใหม่วันที่ 19 ต.ค. 2026
- ก่อนแชตแรก ผู้เขียนปิด memory, การอ้างอิงแชตเก่า และ personalization ของทุก app ตามหัวข้อ 3 และบันทึก screenshot หน้า settings
- ชื่อโมเดลที่ app แสดงเมื่อสมัคร (19 ต.ค. 2026): Claude.ai free แสดง Sonnet 5.5 และ Gemini app แสดง Gemini 4 ซึ่งต่างจาก API proxy (claude-sonnet-5, gemini-3.6-flash); ชื่อโมเดลในวันแชตบันทึกในชีต setup

#### ค่าใช้จ่ายและการทดลองเชิงสำรวจที่วางแผนไว้
- **ค่าใช้จ่ายแบบ list-price estimate** (`results/rc1/cost.csv`; ราคาตรวจกับหน้าราคาทางการวันที่ 20 ต.ค. 2026): รวม US$11.72 แยกเป็น Anthropic 5.05, Google 5.78 และ OpenAI 0.88 (รวม call ที่เป็น error record)
- **ค่าใช้จ่ายจริงจากยอดใน console (20 ต.ค. 2026 หลังเก็บครบ):** OpenAI US$4.79 → US$3.90 (ใช้ US$0.89); Gemini API THB 679.13 → THB 471.15 (ใช้ THB 207.98); Anthropic ยังแสดง US$8.39 ซึ่งยังไม่สะท้อนการใช้ของรอบนี้ ค่าใช้จ่ายจริงของ Anthropic รายงานใน addendum ถัดไป
- **การทดลองเชิงสำรวจ (exploratory):** ผู้เขียนวางแผนป้อน X07 (ภาษาอังกฤษ), X17 และ X37 (ภาษาไทย) ซึ่ง claude-sonnet ให้คำตอบที่มีแต่ thinking ลงใน Claude.ai free หลังแชตของ chat check ครบ
  - ข้อเหล่านี้เลือกหลังเห็น error จึงไม่ใช่ส่วนของ chat check และไม่รวมกับผลของ chat check
  - รายการข้อ รูปแบบ prompt และวิธีอ่านผล กำหนดใน addendum ที่ลงวันที่ก่อนป้อนแชตแรกของการทดลองนี้

### Addendum ของการแก้เล่ม ชุดที่ 1 (22 ต.ค. 2026; ก่อนผู้เขียนรันสคริปต์ตารางและตัวเลขฉบับแก้)
- **prereg ก่อนต่อท้ายชุดนี้:** `prereg/preregistration_FROZEN.md` sha256 `36aa8d469569e70dba1eec3777350eea50bc0da9b68bf58c94cb4cb2184a3680` จำนวน 2013 บรรทัด (หลังต่อท้ายของ Gate 3)
- ชุดนี้บันทึก deviation ด้านถ้อยคำและการนำเสนอที่ผู้เขียนตัดสินหลังเห็นผลของรอบ ต.ค. (D-12 ถึง D-14), สคริปต์ใหม่ที่ผลิตตารางและตัวเลขของเล่มฉบับแก้, ค่า PostgreSQL settings ที่จับย้อนหลัง, การยกเลิกการทดลองเชิงสำรวจที่วางแผนไว้ใน addendum ของ Gate 3 และการแก้ข้อความของ AMENDMENT-4
- ผลของผู้ช่วยจากสคริปต์ใหม่เป็น TEST-ONLY; ตัวเลขทางการมาจากการรันของผู้เขียนหลัง commit ชุดนี้ และบันทึกพร้อม sha256 ของไฟล์ผลใน addendum ชุดที่ 2
- addendum ชุดที่ 2 จะบันทึกด้วย: คำตอบของ claude-sonnet-5 บนชุดขยายที่ถูก cap 1,024 token ตัด (ตัวเลขจากการรันของผู้เขียน) และค่าใช้จ่ายจริงของ Anthropic ที่ addendum ของ Gate 3 ระบุว่าจะรายงานใน addendum ถัดไป (ผู้เขียนยังไม่ได้ตรวจยอดใน console)

#### D-12 ถ้อยคำของแม่แบบ A9 ภายใต้ M2 (มติผู้เขียน 21 ต.ค. 2026)
- **ชนิด:** ถ้อยคำรายงานต่างจากผลของการแทนคำตามตัวอักษร; ไม่เปลี่ยนตัวเลข band หรือการวิเคราะห์
- **แผนเดิม:** A9 บรรทัด 544 และ 548 (S1 ของ abstract ใช้ "removed all of" เมื่อ GF_V = 0), บรรทัด 554 (S1 ของ RQ2 "grounding failures fell from [GF_B] to [GF_V] across the three proxies"), บรรทัด 562 (G-a "fell to [s]"), บรรทัด 570 (M2) และบรรทัด 535 (ย่อได้ แต่ห้ามเปลี่ยนกริยาหรือ qualifier)
- **เหตุผล:** H3 ไม่ผ่านในบางโมเดล M2 จึงให้เปลี่ยน "removed" และ "fell" เป็น "coincided with fewer"; การแทนคำตามตัวอักษรได้ "coincided with fewer all of the grounding failures" และ "gap coincided with fewer to [s]" ซึ่งไม่เป็นประโยค และ M2 ไม่ระบุว่าคำ "fell" ใน clause G-a อยู่ในขอบเขตหรือไม่
- **ช่วงเวลา:** พบหลังผลของ analyze_rc1 (20 ต.ค. 2026); ตัดสิน 21 ต.ค. 2026 หลังเห็น band ของ H1–H4 จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - ใช้ M2 กับคำ "fell" ใน clause G-a ด้วย (อ่านแบบอนุรักษ์)
  - S1 ของ abstract: "listing stored values in the prompt coincided with fewer grounding failures there (6 to 0 in a concurrent re-run; the values also changed 15 answers on items needing no stored value)" (ถ้อยคำย่อตาม D-13)
  - S1 ของ RQ2: "listing the values coincided with fewer grounding failures across the three proxies, 6 to 0 by the classifier and 5 to 0 by the manual coding (the values also changed 15 answers on items that need no stored value)"
    โดยเปลี่ยนประธานจาก "grounding failures" เป็น "listing the values" และย้ายการชี้ตารางไปท้าย clause G-a เป็น "per-model gaps in Table IV, last column" (D-14)
  - G-a: "and with a pooled frontier English--Thai gap at 0.44 of its schema-only size (item-bootstrap 95% CI −0.30 to 2.00)" ไม่มีคำบอกทิศ
  - Conclusion (ไม่ใช่ตำแหน่งของแม่แบบ A9): "listing the stored values coincided with fewer grounding failures, though not with a reliably smaller gap, and also changed answers on items that need no stored value (Section V-B)" ไม่มีตัวเลข
- **ผลต่อการตีความ:** ลดน้ำหนักเชิงเหตุและเชิงทิศ ไม่เพิ่ม; band ไม่เปลี่ยน

#### D-13 การย่อบล็อก A9 ใน abstract ให้ไม่เกิน 200 คำ (มติผู้เขียน 22 ต.ค. 2026)
- **ชนิด:** ถ้อยคำ; ไม่เปลี่ยนตัวเลข band หรือการวิเคราะห์
- **แผนเดิม:** A9 บรรทัด 535 (ย่อได้ แต่ห้ามเปลี่ยนกริยาหรือ qualifier), บรรทัด 542 (clause ของทุก scenario "the [10] items whose gold compares a stored English constant"), บรรทัด 543 (นิยาม grounding failures ในวงเล็บครั้งเดียวใน abstract) และบรรทัด 544 (S1 "listing each text column's stored values in the prompt ... among them" พร้อมวงเล็บนิยาม)
- **เหตุผล:** abstract ฉบับแก้ตัดผลของชุดขยาย ผลของ chat check และประโยค artifact ออก และเพิ่มประโยค takeaway หนึ่งประโยค ได้ 199 คำ (บล็อก A9 75 คำ; นับคำแยกด้วยช่องว่าง) ถ้าคืนวงเล็บนิยาม (12–13 คำ) จะเกิน 200 คำ
- **ช่วงเวลา:** ตัดสิน 22 ต.ค. 2026 หลังเห็นผลทั้งหมดของรอบ ต.ค. จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - ตัดวงเล็บนิยามออกจาก abstract; นิยามในเล่มอยู่ในประโยคแม่แบบของ RQ2 (บรรทัด 552): "value-grounding failures that copy the Thai word or invent an English value"
  - ย่อ "the 10 items whose gold compares a stored English constant" เป็น "10 items comparing stored English constants", "each text column's stored values" เป็น "stored values", "grounding failures among them" เป็น "grounding failures there" และ "items that need no stored value" ใน clause k ของ M2 เป็น "items needing no stored value"
  - คงกริยา "fall on" และ "coincided with fewer" และ qualifier อื่นทั้งหมด: schema-only, in the prompt, in a concurrent re-run, three, clause k ของ M2, frontier และ item-bootstrap 95% CI
- **ผลต่อการตีความ:** abstract ใช้คำ "grounding failures" โดยไม่นิยาม และไม่ระบุว่ารายการค่าครอบเฉพาะคอลัมน์ข้อความ ผู้อ่านต้องไปที่ Section V-B ซึ่งมีทั้งนิยามและ "each text column's stored values"; ตัวเลขและ band ไม่เปลี่ยน

#### D-14 ผลต่อโมเดลของแขน values เป็นคอลัมน์สุดท้ายของ Table IV (มติผู้เขียน 21–22 ต.ค. 2026)
- **ชนิด:** การนำเสนอเปลี่ยนหลังเห็นผล; ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** A10 บรรทัด 581 (ตัวเลขของแขน values ในเล่มมาจาก `analyze_rc1.py` และ `make_table_rc1.py` เท่านั้น) ซึ่งผลิตตารางแยก `tab_values.tex`
- **เหตุผล:** ให้เล่มอยู่ใน 6 หน้า และให้อ่านความต่าง EN−TH ของแขน values คู่กับแขน schema-only ในตารางเดียว
- **ช่วงเวลา:** ตัดสิน 21–22 ต.ค. 2026 หลังเห็นผลของ analyze_rc1 (20 ต.ค. 2026) จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - `harness/make_tables_rev.py` (หัวข้อถัดไป) อ่าน gap_values_all ของแต่ละโมเดลจาก `rc1_gap.csv` ที่ analyze_rc1.py ผลิต แล้วเขียนเป็นจุดร้อยละ (หารด้วย n = 60) ในคอลัมน์สุดท้าย Δ_V ของ Table IV โดยไม่คำนวณใหม่ ไม่มี interval หรือการทดสอบ
  - acceptance ในสคริปต์: เมื่อตัดเซลล์ Δ_V และ † ออก ตัวเลขทุกเซลล์ของแถวโมเดลทั้งหกต้องเหมือน `tab_crosslingual.tex` เดิม
  - `tab_values.tex` คงอยู่ใน artifact
- **ผลต่อการตีความ:** ไม่มีตัวเลขเปลี่ยน; ค่าในคอลัมน์ Δ_V เป็นค่าเดียวกับใน rc1_gap.csv

#### สคริปต์ใหม่สำหรับตารางและตัวเลขของเล่มฉบับแก้
- **สคริปต์ที่ตรึงไว้ไม่เปลี่ยน:** `harness/make_tables.py` sha256 `90ff96b8a8341ddb2e8fd5b16d3b84f038b27ae771f844b48ccc3ded369e3a49` รวมถึง analyze_rc1.py, analyze_ext.py และ make_table_ext.py
- `harness/rev_numbers.py` sha256 `28a555c531df4b8246b5e8399428e669b243f25687628ea073730e621a587101`
  - อ่านอย่างเดียวจาก results/rc1/graded_rc1.csv, results/ext/graded_ext.csv, results/ext/results_ext_api.jsonl และ accuracy.csv สามชุด: results/tables/accuracy.csv (key v1.2 ของเล่มที่ส่ง), results/v13n/tables/accuracy.csv (regrade ส.ค. ภายใต้ key v1.3n) และ results/rc1/base60/tables/accuracy.csv (รอบ ต.ค.)
  - เขียนผลลงโฟลเดอร์ใหม่ results/rc1/rev_numbers พร้อม `meta.json` (sha256 ของสคริปต์และอินพุตทุกไฟล์; path สัมพัทธ์) และปฏิเสธถ้าโฟลเดอร์นั้นมีอยู่แล้ว
  - แถว typhoon2-8b ของคอลัมน์ Ext.: นับข้อด้วยกฎเสียงข้างมากเดิม (ถูกมากกว่าครึ่งของ run ที่มี) จาก graded_ext.csv พร้อม Wilson 95% (n = 40) และรายการ cell ที่มีน้อยกว่า 5 run; ทำตาม addendum ของ Gate 3 (บรรทัด 1986) ที่ให้รายงานโมเดลนี้บนชุดขยายเชิงพรรณนา แถวนี้จึงไม่ได้มาจาก analyze_ext.py ตาม AMENDMENT-9 หัวข้อ 8 (บรรทัด 1824)
  - ตัวเลขอื่นที่ใช้ในเล่มและ Response: จำนวน generation ที่ grade (core สองแขนและชุดขยาย), การแยก loud, silent-empty และ silent-non-empty ของ free-tier proxies บนชุดขยาย (ข้อ instance เดียว; run ที่ผิดของข้อหลาย instance แยกไว้), run ของ claude-sonnet-5 บนชุดขยายที่ถูก cap 1,024 token ตัด และตาราง decomposition จาก key v1.2 (n=60) ไป regrade ส.ค. (n=59) และรอบ ต.ค. (n=60)
- `harness/make_tables_rev.py` sha256 `521f8228270ca3afba0e02a9d33c8341c2d3624f570176ec7f53020a35834b32`
  - อ่าน `tab_headline.tex`, `tab_tiers.tex`, `tab_crosslingual.tex` และ `tab_stability.tex` ใน `paper/generated/` ที่ make_tables.py ผลิตไว้ และอ่าน results/rc1/base60/tables/accuracy.csv, results/ext/tables/ext_accuracy.csv, results/rc1/rev_numbers/ext_typhoon_descriptive.csv และ results/rc1/h1h4/rc1_gap.csv
  - เขียน `tab_*_rev.tex`, `diff.txt` และ `meta.json` (sha256 ของสคริปต์และอินพุตทุกไฟล์; path สัมพัทธ์) ลงโฟลเดอร์ใหม่ paper/generated_rev และปฏิเสธถ้าโฟลเดอร์นั้นมีอยู่แล้ว
  - caption ของ Table II–V ตามถ้อยคำที่ผู้เขียนอนุมัติ และ † ที่ชื่อแถวของโมเดล local พร้อมประโยค exploratory (A10 บรรทัด 585)
  - Table II: คำนวณ Wilson 95% ใหม่จาก correct/n ใน accuracy.csv แทนการปัดค่าที่ปัดไว้แล้วซ้ำ (typhoon2-8b ภาษาไทย ขอบล่าง 18.507% แสดงเป็น 18 ที่ถูกคือ 19) และเพิ่มคอลัมน์ Ext. (จำนวนข้อที่ถูก EN/TH จาก 40 ข้อของชุดขยาย AMENDMENT-9; เชิงพรรณนา) โดยใส่ ‡ ที่เซลล์ของโมเดลที่มี cell น้อยกว่า 5 run ตาม ext_typhoon_descriptive.csv
  - Table IV: คอลัมน์ Δ_V ตาม D-14
  - acceptance ในสคริปต์: ทุกเซลล์ตัวเลขในแถวโมเดลของ Table III–V ต้องเหมือนเดิม (caption เปลี่ยนโดยเจตนา) และเซลล์ของ Table II เปลี่ยนได้เฉพาะขอบ Wilson ที่ปัดซ้ำ มิฉะนั้นสคริปต์หยุดโดยไม่เขียนไฟล์; diff.txt บันทึกเซลล์ของ Table II ที่เปลี่ยน
- ผู้เขียนรัน rev_numbers.py ก่อน make_tables_rev.py เพราะ make_tables_rev.py อ่าน ext_typhoon_descriptive.csv

#### ค่า PostgreSQL settings ที่จับย้อนหลัง
- ผู้เขียนจับค่าเมื่อ 22 ต.ค. 2026 05:30 ICT: `results/rc1/base60/pg_settings_posthoc_2026-10-22.tsv` sha256 `2c69a98d4abd2281d138efd645cca89a7acea90068cc7ec7640e48aa823d2c4d`
- pg_postmaster_start_time และ pg_conf_load_time เป็น 12 ต.ค. 2026 21:49 ICT ซึ่งอยู่ก่อนไฟล์ plan ทุกชุดที่สร้างหลังวันนั้น ได้แก่ results/v13n/plan_*.csv (regrade ของ log ส.ค.; 19 ต.ค.) และ results/rc1/base60/plan_*.csv (รอบ ต.ค.; 20 ต.ค.) จึงไม่มีการ restart หรือ reload ระหว่างนั้น
- plan_quality.py ตั้งเพียง statement_timeout ค่าในไฟล์นี้จึงเป็นค่าที่ใช้ตอนวัดไฟล์ plan ทั้งสองชุด
- AMENDMENT-5 เขียนว่า config "ที่ repo ตรึงครบ" แต่ repo ไม่มีไฟล์ settings จนถึงการจับค่าครั้งนี้; plan ของเล่มที่ส่ง (results/plan_*.csv; 7 ส.ค. 2026) ยืนยันด้วยไฟล์นี้ไม่ได้

#### ยกเลิกการทดลองเชิงสำรวจบน Claude.ai free
- addendum ของ Gate 3 (บรรทัด 2011–2013) วางแผนป้อน X07, X17 และ X37 ลงใน Claude.ai free หลัง chat check
- ผู้เขียนยกเลิกการทดลองนี้เมื่อ 21 ต.ค. 2026 ก่อนป้อนแชตใด ๆ ของการทดลอง; ไม่มีข้อมูลเก็บ และไม่มีผลใดรายงาน

#### แก้ข้อความของ AMENDMENT-4 เรื่องต้นทางของ weights ของ typhoon2-8b (แก้แบบเปิดเผย; ไม่ใช่ deviation ของวิธีการ)
- addendum ของ AMENDMENT-4 (บรรทัด 101–103; 7 ส.ค. 2026) บันทึกว่า weights ต้นทางของ GGUF ที่ใช้ "คือ typhoon-ai/llama3.1-typhoon2-8b-instruct อย่างเป็นทางการ"
  - GGUF นั้นคือ repo mradermacher/llama3.1-typhoon2-8b-instruct-GGUF commit 076ad750510f23fef0cb7b8ba69f6ef072a1d3f4 และไฟล์ Q4_K_M ที่มี sha256 63a0e0730cc131abbd2d2ab7ddde27bf9aac530143e4b1f824d03399c4567770 (sha256 ตรงกับ provenance ของรอบ ต.ค. และค่า GGUF ที่เติมใน AMENDMENT-7; commit ตามบันทึกการทำงานของผู้เขียนเมื่อดาวน์โหลด)
- ข้อนี้ยืนยันไม่ได้: README ของ repo GGUF และ metadata general.source.url ในไฟล์ระบุต้นทางเป็น FILM6912/llama3.1-typhoon2-8b-instruct ซึ่งเป็น repo ของบุคคลที่สามที่ตั้งชื่อเป็น Typhoon 2 และเมื่อ 22 ต.ค. 2026 เข้าถึงไม่ได้ (HTTP 401) จึงเทียบ hash กับ release ทางการไม่ได้
- ข้อความที่ถูกต้อง: community quantization (mradermacher, Q4_K_M) ของ repo ของบุคคลที่สามที่ตั้งชื่อเป็น Typhoon 2 และเข้าถึงไม่ได้แล้ว ซึ่งยืนยันไม่ได้ว่าตรงกับ release ทางการ
- AMENDMENT-4 บรรทัด 94–95 ("ต่างเฉพาะ Thai adaptation") ไม่ครบ: คู่นี้ต่างกันใน post-training (Typhoon 2 ทำ instruction tuning ของตัวเองบน base ที่ continual-pretrain จาก Llama-3.1-8B), chat template และผู้ทำ quantization ด้วย ซึ่งตรงกับ A10 ที่ให้ผลของโมเดล local เป็น exploratory
- ไม่มีการเปลี่ยนโมเดล ข้อมูล หรือผล; ผลของ typhoon2-8b เป็นผลของไฟล์ GGUF นี้ (sha256 ข้างบน) และเล่มฉบับแก้ใช้ถ้อยคำที่ถูกต้องใน Limitations

### Addendum ของการแก้เล่ม ชุดที่ 2 (22 ต.ค. 2026; ผลของการรันหลัง commit ชุดที่ 1)
- **prereg ก่อนต่อท้ายชุดนี้:** `prereg/preregistration_FROZEN.md` sha256 `6c9a2012f6054432ab014ca48ac0034d5ebc3bc1f98e8705163a75de0db4999b` จำนวน 2089 บรรทัด (หลังต่อท้ายชุดที่ 1)
- **commit ของชุดที่ 1:** git commit `329000fcf33a7a0ed5fac3d114fea29d10984a38` บน main เวลา commit 2026-10-22T13:44:38+07:00; push ถึง origin แล้ว (1809106..329000f)
- ผู้เขียนรันทุกคำสั่งในชุดนี้เมื่อ 22 ต.ค. 2026 หลัง commit ชุดที่ 1; ผลทุกไฟล์ตรงกับการทดสอบของผู้ช่วยก่อนหน้าทุก byte (ไม่นับ meta.json)
- ชุดนี้รายงานค่าใช้จ่ายจริงของ Anthropic ที่ addendum ของ Gate 3 ระบุว่าจะรายงานใน addendum ถัดไป (หัวข้อสุดท้าย)

#### FREEZE STAMP ของผลการรัน

| ไฟล์ | sha256 |
|---|---|
| `results/rc1/h1h4_vg9/rc1_summary.txt` | `d7e3d81cb7d29c78ae021e00d3fda5ead7e8a3be3c414410a88f925902813f36` |
| `results/rc1/h1h4_vg9/rc1_decisions.json` | `8383a36c482037a42a564b19c0f51657be36a6b2d65c283d9b38f3916ec46a31` |
| `results/rc1/h1h4_positional/rc1_summary.txt` | `2c084d5e56d34c4c938556fd806c96e701faec4f530b93871a578c63263887f3` |
| `results/rc1/h1h4_positional/rc1_decisions.json` | `c66b40d5b953a12bc94fc0c7c1592bd47aac8e921ffe066e5a54b5cff109be22` |
| `results/rc1/h1h4_nocolroles/rc1_summary.txt` | `bb5681218cc12c5152bd81684a132930576849823d9104988976eb239ac32431` |
| `results/rc1/h1h4_nocolroles/rc1_decisions.json` | `ae73b49c1ee4724b7a89a1eeb88aa14f95d96a5b05ddf8b886d9285e955742d6` |
| `suite/vg_set_v13n_noQ14.txt` | `dc692a01f9289a3372c801edbedc518aef6d045ddaf2dcf6ae87394ddf1018a0` |
| `results/rc1/base60/tables_noQ14/value_translated.csv` | `0a24f80c65f210d95f06ed8510a11252d2ae42893b3951ed5fd45ec8c8c6f6c8` |
| `results/rc1/rev_numbers/summary.txt` | `369e7e022b76b70f35bf9645f98ec1cc6fe720168a3691c82ed5aecd5b49309a` |
| `results/rc1/rev_numbers/generations.csv` | `d96e74ca6b5c681ccbbdb2b898ea8827c93989cb10a0c598318ea041facc82c5` |
| `results/rc1/rev_numbers/ext_frontier_silent.csv` | `2e60f3e26868a87f046daa2dde87da681ea6dfb0bb960f09b35fa1e54aedb332` |
| `results/rc1/rev_numbers/ext_typhoon_descriptive.csv` | `a803250f1c211132e1e5894de9d418a0e5fd09a1f95a3ea588a34d429f00eaca` |
| `results/rc1/rev_numbers/ext_claude_truncation.csv` | `89bca28c4761f592814c90caf5f0a94acccfc2e497d1d1be39113a4ede7ad5fd` |
| `results/rc1/rev_numbers/decomposition.csv` | `5b4185623f112309e53686129831d9aadcc2b6fa9b12a220dccfe41f3296b04b` |
| `paper/generated_rev/tab_headline_rev.tex` | `95389bc7f63cb96b1468c125196bf2c8b758911e0fadc3d89cf3084a57eb09fc` |
| `paper/generated_rev/tab_tiers_rev.tex` | `7c303e4bb034247caf16826559e4e7a40061b9e2acbd144bf0fea9074d071fda` |
| `paper/generated_rev/tab_crosslingual_rev.tex` | `aff165bdb848feed455032531d0fb76fea51d24ca8977278b9b2bfcc00e67015` |
| `paper/generated_rev/tab_stability_rev.tex` | `681259e45fd703356b098fa203179a0fef0fca24e5023411db87479d24e88929` |
| `paper/generated_rev/diff.txt` | `f86a722bd138435accbf2dc2598f2ed81cff68c04a2ce85116f7ab3e834b8ae7` |

#### sensitivity ที่ลงทะเบียนไว้ (A8 และ C4) ด้วยสคริปต์ที่ตรึงไว้
- **VG9** (`analyze_rc1.py --vg-set suite/vg_set_v13n_VG9.txt`; VG10 ไม่รวม Q48): free-tier proxies แขน schema-only a = 7 จาก 17, g = 6 จาก 17; แขน values a = 0 จาก 10; band H1 S1 (GF 6 → 0), H2 G-a (share 0.44, item-bootstrap 95% CI −0.30 ถึง 2.00), H3 ไม่ผ่าน (M2 ใช้), H4 ไม่มี M1 — เหมือนผลหลักทุก band
- **เทียบคอลัมน์ตามตำแหน่ง** (`--graded results/rc1/graded_rc1_positional.csv`) และ **ไม่ใช้บทบาทคอลัมน์** (`--graded results/rc1/graded_rc1_nocolroles.csv`): แขน schema-only a = 8 จาก 17 (gpt-mini 5 แทน 4), g = 6 จาก 17; แขน values a = 0 จาก 10; band เหมือนผลหลักทุก band ในทั้งสองแบบ
- **VG ไม่มี Q14** (`analyze.py --arm base --vg-set suite/vg_set_v13n_noQ14.txt`; 9 ข้อ): ความถูกภาษาไทยบนข้อ VG ต่อข้อที่เหลือ 51 ข้อ: claude-sonnet 0.889 ต่อ 0.922, gemini-flash 1.000 ต่อ 0.941, gpt-mini 0.444 ต่อ 0.922, qwen25-coder-7b 0.333 ต่อ 0.431, llama31-8b 0.333 ต่อ 0.392, typhoon2-8b 0.556 ต่อ 0.235; accuracy.csv และ cross_lingual.csv เหมือนตารางหลักทุก byte

#### ตัวเลขจาก rev_numbers.py และตารางจาก make_tables_rev.py
- จำนวน generation ที่ grade: core 3,600 (schema-only) + 3,600 (values) + ชุดขยาย 2,398 = 9,598
- ชุดขยาย, free-tier proxies, ข้อ instance เดียว: run ที่ผิด 191 = loud 24 (ถูก cap ตัด 14) + silent-empty 11 + silent-non-empty 156 → execute ได้โดยไม่มี error 167 จาก 191 (87.4%); run ที่ผิดของข้อหลาย instance 4 run (gpt-mini ภาษาอังกฤษ) แยกไว้
- typhoon2-8b บนชุดขยาย (เชิงพรรณนา): ภาษาอังกฤษถูก 1 จาก 40 ข้อ (200 run), ภาษาไทยถูก 1 จาก 40 ข้อ (198 run; X28 มี 3 run); Wilson 95% 0.4–12.9%
- make_tables_rev.py: ตัวเลขที่เปลี่ยนมีเพียง CI ของ typhoon2-8b ภาษาไทยใน Table II ([18,41] → [19,41]); คอลัมน์ Ext. 36/31, 31/29, 38/37, 7/4, 4/3, 1/1 (‡ ที่ typhoon2-8b); Δ_V +6.7, +0.0, +0.0, +15.0, +18.3, +13.3

#### cap 1,024 token ของ claude-sonnet-5 บนชุดขยาย (เปิดเผย; ไม่ใช่ deviation)
- max_tokens 1024 ลงทะเบียนไว้ในตาราง roster (บรรทัด 335) และนับรวม token ของ thinking
- คำตอบที่ grade แล้วของ claude-sonnet-5 บนชุดขยาย 14 คำตอบมี record สุดท้ายที่ tok_out = 1,024 (ภาษาไทย 12, ภาษาอังกฤษ 2) ใน 6 cell: ภาษาอังกฤษ X07 run 3 และ X08 run 3; ภาษาไทย X05 run 1 และ 3, X07 run 1, 3 และ 4, X17 run 2–5, X37 run 1, 3 และ 5
- ทั้ง 14 คำตอบนับเป็นคำตอบที่ผิดแบบ loud ตาม protocol
- majority ภาษาไทยของ X07, X17 และ X37 ขึ้นกับ run ที่ถูกตัด (run ที่ไม่ถูกตัดของสามข้อนี้ grade ถูกเป็นเสียงข้างมาก); run ที่ถูกตัดของ X05 ภาษาไทยและของภาษาอังกฤษไม่เปลี่ยน majority
- **แก้ข้อความใน addendum ของ Gate 3 (บรรทัด 1990):** "สำเร็จครบหลังรันซ้ำ 2 ครั้ง" หมายถึงได้ record ที่ไม่ใช่ error ครบทุก cell; ใน 4 cell ที่ถามใหม่เพราะคำตอบมีแต่ thinking มี 2 cell (X17 ภาษาไทย run 4 และ X37 ภาษาไทย run 5) ที่ record สุดท้ายยังถูก cap ตัด
- core ไม่กระทบ: ไม่มี record ของโมเดล API ใดที่ tok_out = 1,024 (claude-sonnet สูงสุด 567 จาก 1,200 record; gemini-flash 181; gpt-mini 168; ผู้เขียนตรวจด้วยคำสั่งอ่านอย่างเดียวบน `results/rc1/results_rc1_api.jsonl` เมื่อ 22 ต.ค. 2026)
- การวิเคราะห์ใดที่พัก 14 คำตอบนี้ไว้ต้องติดป้ายว่าไม่ได้ลงทะเบียนล่วงหน้า (non-preregistered sensitivity) และบันทึกใน addendum ก่อนรัน; เล่มรายงานจำนวนนี้ใน caption ของ Table II และใน Limitations

#### token usage และค่าใช้จ่ายจริง (A6 ข้อ 9)
- token usage ต่อ log, โมเดล และแขน พร้อม list-price estimate: `results/rc1/cost.csv` sha256 `75dfeef05ce03fcd0d382de236bd1385bb87567cddf60ba3041c640dd7d2188d` (commit ใน Gate 3; รวม US$11.72 แยกเป็น Anthropic 5.05, Google 5.78 และ OpenAI 0.88)
- **Anthropic:** ยอดเครดิตคงเหลือ US$8.39 (19 ต.ค. 2026 ก่อนเริ่ม) → US$3.28 (22 ต.ค. 2026) = ใช้ US$5.11
  - หน้า cost ของ console (ข้อมูล ณ 22 ต.ค. 2026 06:03 UTC) แสดงค่าใช้จ่าย 30 วันย้อนหลัง US$5.11 เป็นค่า token ของ Claude Sonnet 5 ทั้งหมด (ค่าค้นหาเว็บ ค่ารันโค้ด และค่าเวลาของเซสชันเป็น 0) และยอดใช้จ่ายของเดือน ต.ค. (UTC) US$5.11
  - ยอดของเดือนจึงเท่ากับยอดที่ลดลงตั้งแต่ 19 ต.ค.; การเรียก API อื่นในเดือนนี้ก่อนเริ่มเก็บข้อมูลไม่เปลี่ยนตัวเลขในหลักเซ็นต์ ค่าใช้จ่ายจริงของรอบ ต.ค. ฝั่ง Anthropic จึงเป็น US$5.11 (list-price estimate 5.05)
- **OpenAI และ Gemini API:** ค่าใช้จ่ายจริง US$0.89 และ THB 207.98 ตาม addendum ของ Gate 3; ยอดคงเหลือเมื่อ 22 ต.ค. 2026 ยังเป็น US$3.90 และ THB 471.15 เท่ากับเมื่อ 20 ต.ค. จึงไม่มีการใช้หลังเก็บข้อมูลครบ

### Addendum ของการแก้เล่ม ชุดที่ 3 (22 ต.ค. 2026; บีบเล่มให้อยู่ใน 6 หน้า)
- **prereg ก่อนต่อท้ายชุดนี้:** `prereg/preregistration_FROZEN.md` sha256 `60725fe14e4374df6f429d016a2b52954ef46898bee6a25322362ee5228cf708` จำนวน 2146 บรรทัด (หลังต่อท้ายชุดที่ 2)
- **commit ของชุดที่ 2:** git commit `d567fb60b414cd5ececb029f2b5f7daa0244283c` บน main เวลา commit 2026-10-22T14:23:13+07:00; push ถึง origin แล้ว (329000f..d567fb6)
- ชุดนี้ไม่มีการรันใหม่ และไม่เปลี่ยนตัวเลข band หรือการวิเคราะห์ใด; บันทึก deviation ด้านตำแหน่งการรายงาน (D-15 ถึง D-18) ที่ผู้เขียนตัดสินเมื่อ 22 ต.ค. 2026 เพื่อให้เล่มอยู่ใน 6 หน้ารวม reference ตามหน้า Paper Submission และ Camera-Ready ของ KST 2027 ("maximum of 6 pages")
- ทุกข้อในชุดนี้ตัดสินหลังเห็นผลทั้งหมดของรอบ ต.ค. จึงไม่เป็นไปตาม A10 บรรทัด 586
- เนื้อหาที่ย้ายออกจากเล่มอยู่ใน `SUPPLEMENT.md` sha256 `dfe6db5ba237e846b197ef7c0ed5990550940a18b0f0980e86fd847abf1e8313` (ไฟล์ใหม่ที่ root ของ repo: ข้อจำกัดฉบับเต็ม, errata ของ suite รุ่นถัดไปซึ่งเล่มกล่าวถึงสั้นๆ ใน Section III-C, และตาราง/รูปที่เล่มไม่พิมพ์) และในไฟล์ผลที่ตรึงไว้แล้ว ไม่มีไฟล์ผลใดถูกแก้
- เล่มฉบับบีบ: `paper/main_rev.tex` sha256 `dca5001ab883c6b0d9ac9ac74372c3da1920b747c57f9bd98c6fa9a6f31eb08a` (6 หน้ารวม reference เมื่อ compile ด้วย xelatex; เว้นที่ท้ายหน้า 6 ไว้ให้ย่อหน้าผลของ chat check ตาม AMENDMENT-8 หัวข้อ 11)
- ส่วนที่ prereg กำหนดให้อยู่ในเล่มและยังอยู่ครบ: ประโยคแม่แบบ A9 ทุกตำแหน่ง (ตัวชี้ตารางเปลี่ยนตาม D-15), H3 แบบรวมและแบบตัดโมเดลที่เกิน placebo, footnote ของ Q14 (C4), การ re-code ด้วยมือพร้อม agreement และ κ, ข้อความของ D-1, ลำดับเวลาการเพิ่ม typhoon2-8b (D-3), ผลรอบ ส.ค. ตาม C5, นิยาม loud และ silent ทั้งสองแบบ (B1), ป้าย exploratory ของผลโมเดล local ทุกจุด (A10) และคำที่ AMENDMENT-8 ตรึงไว้สำหรับ chat check
- การเปิดเผยการใช้ AI ตามบรรทัด 219 อยู่ใน Acknowledgment ของเล่มฉบับแก้ และระบุว่าผู้ช่วย AI ร่าง preregistration
- sensitivity ที่ prereg ไม่ได้กำหนดตำแหน่งในเล่ม (VG9 ของ A8, การเทียบคอลัมน์ตามตำแหน่ง และแบบไม่ใช้บทบาทคอลัมน์) ไม่อยู่ในเล่ม ผลอยู่ในไฟล์ที่ตรึงในชุดที่ 2 และ SUPPLEMENT.md หัวข้อ 3

#### D-15 ตารางและรูปของเล่ม (มติผู้เขียน 22 ต.ค. 2026)
- **ชนิด:** การนำเสนอ (ตำแหน่งของตารางและรูป); ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** A10 บรรทัด 582 (ตัวเลขหลักใน Table II–V), D-14 (Δ_V เป็นคอลัมน์สุดท้ายของ Table IV) และประโยคแม่แบบ A9 ของ RQ2 ที่ D-12 ให้ชี้ "per-model gaps in Table IV, last column"
- **เหตุผล:** ให้เล่มอยู่ใน 6 หน้า; ผู้เขียนให้ตัดรูปก่อน แล้วจึงตัดตารางที่เนื้อหาในเล่มรายงานตัวเลขที่ใช้สรุปผลไว้แล้ว
- **ช่วงเวลา:** ตัดสิน 22 ต.ค. 2026 หลังเห็นผลทั้งหมด จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - เล่มพิมพ์เฉพาะตารางผลหลัก (Table II เดิม) ซึ่งเลขเปลี่ยนเป็น Table I; caption และตัวเลขเหมือนไฟล์ที่ตรึงไว้ทุกตัว
  - Table III เดิม (ผลรายชั้น), Table IV เดิม (EN–TH พร้อม Δ_V), Table V เดิม (unanimity และ parse rate), Fig. 1 เดิม (ผลรายชั้น) และ Table I เดิม (ตารางสรุปการแปล) ไม่พิมพ์ในเล่ม; ไฟล์ตามตารางข้างล่างไม่ถูกแก้ และตารางสรุปการแปลอยู่ใน SUPPLEMENT.md หัวข้อ 3
  - RQ2: ประโยคแม่แบบ A9 ชี้ "per-model gaps in the artifact" แทน "per-model gaps in Table IV, last column"; ตัวเลข pooled share และ CI คงเดิม
  - การอ้าง Table II–V ใน prereg และ addendum ก่อนหน้า: Table II คือ Table I ของเล่มฉบับแก้; Table III–V คือไฟล์ข้างล่าง
- **ผลต่อการตีความ:** ผู้อ่านเล่มเห็นช่วงความเชื่อมั่นและการทดสอบ EN–TH รายโมเดล, Δ_V รายโมเดล และ unanimity รายเซลล์ได้จาก artifact เท่านั้น; ข้อความของ RQ1, RQ2 และ RQ4 ยังรายงานตัวเลขที่ใช้สรุปผล

| ไฟล์ | sha256 |
|---|---|
| `paper/generated_rev/tab_headline_rev.tex` | `95389bc7f63cb96b1468c125196bf2c8b758911e0fadc3d89cf3084a57eb09fc` |
| `paper/generated_rev/tab_tiers_rev.tex` | `7c303e4bb034247caf16826559e4e7a40061b9e2acbd144bf0fea9074d071fda` |
| `paper/generated_rev/tab_crosslingual_rev.tex` | `aff165bdb848feed455032531d0fb76fea51d24ca8977278b9b2bfcc00e67015` |
| `paper/generated_rev/tab_stability_rev.tex` | `681259e45fd703356b098fa203179a0fef0fca24e5023411db87479d24e88929` |
| `paper/generated/fig_tiers.pdf` | `2b7dae83449cde32f1ec0b371d1046c25ed1a7f54615028e8c029d9e6ffb31b2` |
| `results/rc1/h1h4/rc1_decisions.json` | `ae73b49c1ee4724b7a89a1eeb88aa14f95d96a5b05ddf8b886d9285e955742d6` |
| `results/rc1/h1h4_vg9/rc1_summary.txt` | `d7e3d81cb7d29c78ae021e00d3fda5ead7e8a3be3c414410a88f925902813f36` |

#### D-16 ความสอดคล้องระหว่างรอบ ส.ค. และรอบ ต.ค. (มติผู้เขียน 22 ต.ค. 2026)
- **ชนิด:** ตำแหน่งการรายงาน; ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** AMENDMENT-7 Part 0 ข้อ 3 (บรรทัด 178–181): จำนวนข้อที่ถูกโดย majority ของรอบ ส.ค. และรอบ ต.ค. ต่อโมเดล × ภาษา และจำนวนข้อที่คำตัดสินต่างกันแยกทิศ บน 59 ข้อที่ถามเหมือนกัน อยู่ในเล่ม
- **เหตุผล:** ให้เล่มอยู่ใน 6 หน้า; การเทียบเป็นเชิงพรรณนาและไม่เปลี่ยนข้อสรุปใด
- **ช่วงเวลา:** ร่างเล่มก่อนบีบหน้า (22 ต.ค. 2026) ย่อเหลือจำนวนข้อที่เปลี่ยนของ free-tier proxies และช่วง 0–3 ของโมเดล local โดยไม่ได้ลง deviation; ฉบับบีบหน้าย้ายทั้งหมดไป artifact; ตัดสินหลังเห็นผล จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ:** ตารางครบทุกโมเดล × ภาษาพร้อมทิศอยู่ใน SUPPLEMENT.md หัวข้อ 1 ข้อ 3 จาก `results/rc1/consistency/consistency.csv` sha256 `57ed5f03c2b7731c9fb264fbfd8b29595c672215c862a71e1c1de568883a0ea9`; เล่มไม่มีผลข้อนี้
- **ผลต่อการตีความ:** ผู้อ่านเล่มไม่เห็นขนาดของการเปลี่ยนระหว่างสองรอบ (0–3 ข้อต่อโมเดล × ภาษา) ถ้าไม่เปิด artifact

#### D-17 ข้อจำกัดที่ addendum ก่อนหน้าระบุให้อยู่ใน Limitations (มติผู้เขียน 22 ต.ค. 2026)
- **ชนิด:** ตำแหน่งการรายงาน; ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** addendum ของ Gate 3 บรรทัด 1992 (เล่มรายงานการถามซ้ำเป็นข้อจำกัดพร้อมจำนวน), addendum ชุดที่ 1 บรรทัด 2087 และ 2089 (ถ้อยคำที่ถูกต้องเรื่อง weights ของ typhoon2-8b ซึ่งเล่มฉบับแก้ใช้ใน Limitations) และ addendum ชุดที่ 2 บรรทัด 2139 (จำนวนคำตอบที่ถูก cap ตัด ใน caption ของ Table II และใน Limitations)
- **เหตุผล:** ผู้เขียนให้ Limitations ของเล่มเหลือแกนสองเรื่อง (การศึกษาในชั้นเรียนที่ต้องรอภาคที่สอนเป็นภาษาไทย และการขยาย schema) กับประโยคสำคัญ 1–2 ประโยค เพื่อให้อยู่ใน 6 หน้า
- **ช่วงเวลา:** ตัดสิน 22 ต.ค. 2026 หลังเห็นผลทั้งหมด จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - จำนวนการถามซ้ำ จำนวนคำตอบที่ถูก cap ตัด และถ้อยคำเรื่อง weights อยู่ใน SUPPLEMENT.md หัวข้อ 1 ข้อ 8–9 (ไฟล์ผลของ cap: `results/rc1/rev_numbers/ext_claude_truncation.csv` sha256 `89bca28c4761f592814c90caf5f0a94acccfc2e497d1d1be39113a4ede7ad5fd`)
  - caption ของ Table I (Table II เดิม) ยังรายงานคำตอบ 14 คำตอบที่ถูก cap ตัด
  - §IV ของเล่มยังระบุ cap 1,024 token, ว่าไม่มีคำตอบของ core ที่ใกล้ cap (สูงสุด 567 output tokens) และว่า weights ของ typhoon2-8b เป็น community quantization การเทียบจึงเป็น exploratory
  - Limitations ของเล่มคงประโยคเรื่อง execution grading ตาม C4 และประโยคว่า free-tier proxies ไม่ใช่ตัวแอป
- **ผลต่อการตีความ:** เล่มไม่ระบุว่ายืนยันไม่ได้ว่า weights ตรงกับฉบับทางการ และไม่ระบุจำนวน cell ที่ได้จากการถามซ้ำ; ข้อมูลทั้งสองอยู่ใน artifact

#### D-18 ตารางจับคู่ free tier กับ API model (มติผู้เขียน 22 ต.ค. 2026)
- **ชนิด:** การนำเสนอ; ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** preregistration ฉบับแรก บรรทัด 22–23 (ตารางจับคู่ free-tier↔API-model ณ วัน freeze ใส่ในเปเปอร์ พร้อม limitation เรื่อง scaffolding ของ web free tier)
- **เหตุผล:** ฉบับส่ง (ส.ค. 2026) เขียนการจับคู่เป็นข้อความใน Section IV แทนตาราง โดยไม่ได้ลง deviation; ฉบับแก้คงเป็นข้อความเพื่อให้อยู่ใน 6 หน้า
- **ช่วงเวลา:** เกิดตั้งแต่ฉบับส่ง (ส.ค. 2026); พบระหว่างตรวจเล่มฉบับแก้ 22 ต.ค. 2026
- **สิ่งที่ทำ:** §IV ของเล่มระบุ identifier ของแต่ละ proxy, แอปฟรีที่ proxy แทน และว่าเป็น proxy ระดับ tier-class; identifier และค่าตั้งของทุกโมเดลอยู่ใน `harness/models.json` sha256 `019ec1785ae857d4fd798048145c7453911dc43a9255f6f13fb70c060ce7b099`; ข้อจำกัดเรื่อง scaffolding อยู่ใน Limitations ของเล่ม (proxies ไม่ใช่ตัวแอป) และ SUPPLEMENT.md หัวข้อ 1 ข้อ 4
- **ผลต่อการตีความ:** ไม่มี; ข้อมูลเดียวกันอยู่ในรูปข้อความ

### Addendum ของ chat check (AMENDMENT-8 หัวข้อ 15; 25 ต.ค. 2026; หลังแชตครบ การ code และรายงาน)
- **prereg ก่อนต่อท้ายชุดนี้:** `prereg/preregistration_FROZEN.md` sha256 `3fde32e50b85e52f603448e8c1b962211c6d586865d99277a6cf0d85bcbd3169` จำนวน 2207 บรรทัด (หลังต่อท้าย addendum การแก้เล่ม ชุดที่ 3)
- **commit ของ Gate 3:** git commit `1809106bd6978ea6c15610ffb470553711d4249b` บน main เวลา commit 2026-10-20T16:06:39+07:00; push ถึง origin แล้ว (f39fe84..1809106)
  - prereg หลังต่อท้าย Gate 3 มีค่า sha256 36aa8d469569e70dba1eec3777350eea50bc0da9b68bf58c94cb4cb2184a3680 จำนวน 2013 บรรทัด (ค่าเดียวกับหัวของ addendum การแก้เล่ม ชุดที่ 1)
- **commit ของชุดที่ 3:** git commit `3e5f117083ff721a89ace1ab8bb0b5b879b0d828` บน main เวลา commit 2026-10-22T21:22:06+07:00; push ถึง origin แล้ว (d567fb6..3e5f117)
- ชุดนี้คือ addendum หลังแชตครบตามหัวข้อ 15 ของ AMENDMENT-8 และ commit พร้อมผลของ chat check (`results/chat/` ทั้งโฟลเดอร์)
  - ไม่เปลี่ยนกฎ รายการข้อ cells หรือ prompt ของ AMENDMENT-8
  - ทุกตัวเลขมาจากการรันของผู้เขียนด้วย kit ที่ตรึงใน Gate 1b และ Gate 2
- ย่อหน้าผลของ chat check ในเล่ม (ท้าย Section V-B) และข้อความเรื่อง chat check ใน `SUPPLEMENT.md` บันทึกพร้อมค่า sha256 ของทั้งสองไฟล์ใน addendum ถัดไป

#### วันที่และเวลาที่ป้อนแชต
- ทั้งสาม app ป้อนวันที่ 21 ต.ค. 2026 วันเดียว ตามลำดับ cell-major ของหัวข้อ 5 (ts_sent แรกถึง ts_done สุดท้ายของแถว done; เวลาไทย)
  - ChatGPT 10:43:23–13:20:33
  - Gemini 11:00:09–13:21:15
  - Claude.ai 11:10:52–13:21:48
- **เงื่อนไขเวลาของหัวข้อ 6:** ผ่านทุกข้อ
  - ช่วง 3 วันปฏิทิน: ใช้ 1 วัน
  - ±7 วันจากแขน B: แขน B ภาษาไทยของ gpt-mini และ gemini-flash เก็บวันที่ 19 ต.ค. 2026 และของ claude-sonnet เก็บวันที่ 20 ต.ค. 2026 ตัวเปรียบเทียบจึงเป็นแขน B ที่เก็บพร้อมกัน และไม่ใช้ทางสำรองของหัวข้อ 9
  - cell ที่เริ่มก่อน cell ก่อนหน้าเสร็จครบทั้งสาม app: 0
  - วันแชตอยู่ในช่วง 19–26 ต.ค. 2026 ที่หัวข้อ 15 วางแผนไว้ และการตรวจซ้ำของ `chat_log_export.py` ผ่าน โดยใช้เวลา commit ของ Gate 2 (2026-10-19T19:32:45+07:00) เป็นขอบล่างของ ts_sent
- **log:** 85 แถว คือ done 84 แถว (28 แถวต่อ app; คู่ app × prompt ละหนึ่งแถว) และ void 1 แถว
  - ทุกคำตอบของ turn 1 มี SQL จึงไม่มีการส่ง turn 2
  - limit_banner ว่างทุกแถว และ tools_visible เป็น none ทุกแถว done
  - ป้ายโมเดลที่ UI แสดง (ui_model_label) เหมือนกันทุกแถว done ของแต่ละ app: ChatGPT "not shown", Gemini "Gemini auto" และ Claude.ai "Sonnet 5.5 medium"

#### บัญชี การตั้งค่า browser และหลักฐาน (ยืนยันตามหัวข้อ 15)
- **ชีต setup ของ `CHAT_LOG.xlsx`:** ตอบ Y ครบทั้ง 7 ข้อ
  - บัญชี free ของ ChatGPT และของ Claude.ai ที่ไม่มี subscription
  - บัญชี Google ส่วนบุคคลของ Gemini ที่ไม่มีแผน AI แบบเสียเงินและไม่ใช่บัญชีขององค์กร
  - ปิด memory การอ้างอิงแชตเก่า personalization และ custom instructions ครบทั้งสาม app
  - ปิดการใช้ข้อมูลเพื่อฝึกโมเดลเท่าที่แต่ละ app เปิดให้ปิด
  - ใช้ค่า default ของ free plan และไม่ใช้ VPN
- บัญชีตรงกับบรรทัดบัญชีของหัวข้อ 15 ตามข้อแก้ใน addendum ของ Gate 3
- **browser:** Google Chrome 155.0.8059.82 (Official Build) (arm64) บน macOS 26.7.1 ตลอด 84 แชต ตรงกับหัวข้อ 15
  - Chrome มี update ที่ดาวน์โหลดแล้วแต่ยังไม่ติดตั้ง ผู้เขียนไม่ relaunch Chrome จนแชตครบ
  - ภาษาของ UI เป็นอังกฤษทั้งสาม app
- **การตั้งค่าหลังแชตสุดท้าย:** เหมือนก่อนเริ่มทุกค่าที่ถ่ายไว้ของทั้งสาม app
  - ChatGPT: memory การอ้างอิงประวัติแชต และ library search ปิด; การใช้ข้อมูลเพื่อพัฒนาโมเดลปิด
  - Gemini: Gemini Apps Activity ปิด; memory ของ Personal Intelligence ปิด; instructions ปิดและว่าง
  - Claude.ai: การสร้าง memory ปิด; การใช้ข้อมูลเพื่อพัฒนา Claude ปิด; location metadata ปิด; instructions ว่าง
- **screenshot ของ settings:** `shots/setup_before_*.png` และ `shots/setup_after_*.png` ใน `results/chat/` crop จากต้นฉบับ 26 ภาพ (ก่อนแชตแรก 17 ภาพ และหลังแชตสุดท้าย 9 ภาพ)
  - สคริปต์ที่ crop คือ `kst_rev/gate0/work/make_setup_shots.py` sha256 `c9819ff59b748808b6398ffb9d3df32a0fdbb8fef8cd0403a869ef7932117d82`: ตัดแถบ URL และแถบข้างที่มีชื่อ และปิดทับชื่อ รูปโปรไฟล์ และ Organization ID
  - ต้นฉบับไม่ crop มีชื่อบัญชีซึ่งใช้ยืนยันว่าเป็นบัญชีที่ระบุ ผู้เขียนเก็บไว้นอก repo
  - 16 หลักแรกของค่า sha256 ของต้นฉบับตามที่สคริปต์พิมพ์ (ชื่อไฟล์ต้นฉบับ ตามด้วยค่า)
    - ก่อนแชตแรก ChatGPT: 111 05b6d21c2a5d0625, 112 4a95c07735eebd1c, 115 d457bd0805b9e5ba, 114 4727ad7882ff7564
    - ก่อนแชตแรก Gemini: 100 4c2bb01028cf5512, 103 8a298e2fa273b30f, 104 fd7286be824522bb, 106 b3355f87d8953416
    - ก่อนแชตแรก Claude.ai: 122 e110c7c9900e5f23, 119 babae6f1dc9c24b0, 126 851a9ce04310f34b, 120 07d66ebce30ae176, 123 be7cb3c787fe6845, 127 ea0155552e52a4e5, 129 fb787c6087ca3d8f, 130 a738909e71cd6323, 131 326c33efb25fcabb
    - หลังแชตสุดท้าย: chatgpt_1 b940d839a5b6c564, chatgpt_2 93ad84a5100e8ea7, chatgpt_3 7019b8ed2ac1a4ca, gemini_1 91264903ebc4b703, gemini_3 50554d6237fd19ab, gemini_4 dd93a9f89bede568, claude_2 ee1e09cdbd2c1ae6, claude_3 b2c890b9a7fb3dde, claude_4 b9b428099d5154da

#### เหตุการณ์ระหว่างป้อนแชต (ไม่เปลี่ยนกฎ cells หรือ prompt)
- **วิธีป้อน:** ผู้เขียนวาง prompt และกดส่งด้วยมือทุก cell ตามหัวข้อ 6
  - helper ของ shell ที่ผู้ช่วยเขียนใช้ pbcopy โหลด prompt เข้า clipboard และใช้ pbpaste บันทึกคำตอบที่ผู้เขียนคัดลอกด้วยปุ่ม copy ของ app ลง `raw/`
  - helper เรียกเครื่องมือ screenshot แบบเลือกพื้นที่ของ macOS และบันทึกเวลา โดยไม่ควบคุม browser
- **ts_sent และ ts_done:** คือเวลาที่ผู้เขียนพิมพ์คำสั่งบันทึกของ helper หลังกดส่งและหลังคัดลอกคำตอบ ไม่ใช่เวลาที่ app แสดง
  - time log ของ helper (`results/chat/chat_session_log.tsv`; 340 เหตุการณ์ คือ go, sent, save และ shot ของ 85 แถว) commit พร้อมชุดนี้ และเวลาของทั้ง 85 แถวใน `log_index.tsv` ตรงกับ time log
  - ChatGPT order 1: ts_done ช้ากว่าเวลาที่คำตอบครบราว 5 นาที เพราะผู้เขียนสับสนระหว่างปุ่ม copy ของ code block กับปุ่ม copy ของทั้งคำตอบ
  - ChatGPT order 2 attempt 2: ts_sent บันทึกหลังคำตอบปรากฏแล้ว
  - ทั้งสองแถวมี note
- **ส่งในแชตเดิม:** ChatGPT order 2 (002_A_th_Q21) attempt 1 ถูกส่งในแชตของ order 1 เพราะผู้เขียนไม่ได้เปิดแชตใหม่
  - ผู้เขียนตั้ง status เป็น void พร้อมเหตุผล และทำ cell นั้นใหม่ในแชตใหม่ (attempt 2; `raw/chatgpt_002_A_th_Q21_a2.md`) ตามหัวข้อ 6
  - แถว ไฟล์ raw และ screenshot ของ attempt 1 คงอยู่ใน log และ screenshot นั้นแสดงแชตเดิมด้านบนเป็นหลักฐาน
- **Gemini ไม่เก็บแชต:** เมื่อเปิดแชตใหม่ Gemini แจ้งว่าแชตเดิมจะถูกลบ เพราะ Gemini Apps Activity ปิดอยู่ตามหัวข้อ 3
  - หลักฐานของ Gemini จึงมีเฉพาะ `raw/` และ `shots/` ซึ่ง helper บันทึกก่อนเปิดแชตใหม่ทุกครั้ง
  - ผู้เขียนไม่ได้เปิด Activity ระหว่าง check
- **ข้อความของ Claude.ai ที่ไม่ใช่ banner ของหัวข้อ 6:** order 3 มี popup ชวนอัปเกรด ("Use Opus 5.5 with Claude Pro") ซึ่งไม่มีข้อความเรื่อง limit หรือการสลับโมเดล
  - ผู้เขียนกด "Not now" และบันทึกใน note โดยไม่บันทึกเป็น limit_banner
  - ใต้คำตอบมีการ์ดโฆษณา Claude Code ซึ่งไม่อยู่ใน raw
- **คำตอบที่ให้ SQL หลายแบบ:** การให้คะแนนใช้ query แรกตามหัวข้อ 8 แม้คำตอบจะแนะนำแบบอื่น เช่น ChatGPT order 1 ให้สองแบบและแนะนำแบบที่สองในส่วนสรุป

#### audit ปิดตาของตัวจำแนก B2.3 (cell ที่ผิดของ VG_chat)
- ผู้เขียน code ครบ 14 แถวของ `vg_audit_chat.xlsx` เมื่อ 21 ต.ค. 2026 โดยไม่เปิดกุญแจ; ผู้ code เป็นผู้ป้อนแชตเอง
- agreement 8 จาก 14 (57.1%) และ Cohen's κ 0.24 (`vg_audit_agreement.tsv`)
  - ผลตัดสิน GF ต่างกัน 5 cell: ตัวจำแนกนับ GF 8 cell และผู้เขียนนับ 11 cell
  - ตัวจำแนกเป็นผลหลักตามหัวข้อ 8 และไม่มีการ code ใหม่หลังเห็นคลาสของตัวจำแนก
- **สาเหตุของผลตัดสิน GF ที่ต่างกัน**
  - 3 cell ของ Claude.ai (Form A Q14 และ Q42, Form B Q14): literal อยู่ใน `LOWER(TRIM(ReturnStatus)) IN (...)` ตัวจำแนกให้ NO_PRED เพราะไม่อ่านคอลัมน์เป้าหมายที่ถูกห่อด้วยฟังก์ชัน แต่ผู้เขียนให้ INVENTED
  - 1 cell ของ ChatGPT (Form A Q48): ใช้ `RunnerUp IS NOT NULL` โดยไม่มี literal ตัวจำแนกให้ NO_PRED แต่ผู้เขียนให้ INVENTED ซึ่งเป็นนิยามที่กว้างกว่า แบบเดียวกับ manual audit ของ Gate 3
  - 1 cell ของ ChatGPT (Form A Q42): SQL มี literal ที่ไม่อยู่ในค่าที่เก็บ ตัวจำแนกให้ INVENTED แต่ผู้เขียนให้ NO_PRED; ตามลำดับกฎใน README ของ sheet ควรเป็น INVENTED
- ตามการ code ของผู้เขียน (ข้อมูลประกอบ ไม่ใช่ผลหลัก) GF ของ Claude.ai เป็น 4 จาก 10 ใน Form A และ 1 จาก 10 ใน Form B และข้อที่เป็น GF รวม Q14 และ Q42 ซึ่งเป็นข้อ GF ของ claude-sonnet; จำนวน GF ของ ChatGPT และ Gemini เท่าเดิม
- **ข้อมูลที่ผู้เขียนเห็นระหว่าง code**
  - ผู้ช่วยให้ตารางค่าที่เก็บจริงของคอลัมน์เป้าหมายทั้ง 5 คอลัมน์ (จาก `suite/value_hints_v1.json` และ query แบบอ่านอย่างเดียวบนฐาน k3n) โดยไม่เปิดกุญแจและไม่บอกคลาสของตัวจำแนก
  - ผู้ช่วยยกตัวอย่างอธิบายกฎว่า Category = 'Apparel' ตัวอย่างนี้ตรงกับ SQL ของแถว V01 ที่ผู้ช่วยเห็นขณะตรวจ layout ของ sheet ในการทดสอบ แต่ผู้ช่วยบอกผู้เขียนว่ายกขึ้นเองโดยไม่ได้มาจากคำตอบของ app ใด ซึ่งไม่ถูกต้อง; ผู้ช่วยแก้ข้อความนี้กับผู้เขียนในวันเดียวกัน
  - ตัวอย่างไม่เปิดเผย app หรือคลาสของตัวจำแนก แต่อาจมีอิทธิพลต่อการตัดสินแถว V01; ผู้เขียนยืนยัน (21 ต.ค. 2026) ว่าตัวอย่างไม่มีผลต่อการตัดสิน และแถว V01 ได้คลาส INVENTED ทั้งจากผู้เขียนและจากตัวจำแนก

#### silence code (Form B; 54 คำตอบ)
- **รอบแรก:** ผู้เขียน code ครบ 54 แถวเมื่อ 21 ต.ค. 2026 (บันทึกล่าสุด 14:46:18)
  - หลัง scrub metadata (หัวข้อถัดไป) ไฟล์มีเวลาแก้ไข 14:48:04 ซึ่ง `chat_silence_sheet.py` ใช้เป็นจุดเริ่มนับ 72 ชั่วโมง
- **รอบสอง:** sheet สร้างวันที่ 24 ต.ค. 2026 หลังรอบแรกเกิน 72 ชั่วโมง ลำดับแถวต่างจากรอบแรก และไม่แสดง code ของรอบแรก; ผู้เขียน code ครบ 54 แถว (บันทึกล่าสุด 23:23:43)
- agreement 49 จาก 54 (90.7%) และ Cohen's κ 0.78
  - ตาราง 3×3 (รอบแรก → รอบสอง): FLAGGED→FLAGGED 13, FLAGGED→SILENT 5, SILENT→SILENT 36 และช่องอื่น 0; ไม่มี ASKED ทั้งสองรอบ
- **แก้ความต่าง:** ผู้เขียนอ่านซ้ำ 5 แถวที่ไม่ตรงกัน และบันทึก code สุดท้ายพร้อมเหตุผลใน `silence_reconcile.xlsx` (SILENT 4 แถว และ FLAGGED 1 แถว)
  - code สุดท้ายของ 54 แถวใน `silence_final.tsv`: FLAGGED 14, SILENT 40 และ ASKED 0
- **การปิดตา:** sheet ไม่แสดง app สถานะ VG หรือป้ายถูกผิด แต่การปิดตาเป็นแบบขั้นตอนตามหัวข้อ 8
  - รูปแบบของคำตอบอาจบอก app ได้
  - ผู้เขียน code ทั้งสองรอบหลังเห็นผลการให้คะแนนระดับ run ต่อ app × form และค่า agreement ของ audit B2.3
  - ระหว่างสองรอบ ผู้ช่วยไม่บอกสัดส่วนหรือผลของ code รอบแรก

#### scrub metadata ของ xlsx
- xlsx ที่บันทึกด้วย Excel มี path ของไฟล์และชื่อผู้แก้ไขล่าสุดใน metadata ผู้เขียนลบสองส่วนนี้ (`xl/workbook.xml` และ `docProps/core.xml`) ก่อน commit โดยเนื้อหาของทุกชีตไม่เปลี่ยน
  - ไฟล์ที่ scrub: `CHAT_LOG.xlsx`, `vg_audit_chat.xlsx`, `silence_round1.xlsx`, `silence_round2.xlsx` และ `silence_reconcile.xlsx`
  - ค่าใน FREEZE STAMP ข้างล่างเป็นค่าหลัง scrub; ฉบับก่อน scrub ผู้เขียนเก็บไว้นอก repo
  - scrub ของ `silence_round1.xlsx` ทำก่อนสร้าง sheet รอบสอง เพราะ `chat_silence_sheet.py` บันทึกค่า sha256 ของไฟล์รอบแรกตอนสร้างรอบสอง

#### ผลของ `chat_report.py` (ฐาน k3n; ตัวเปรียบเทียบคือแขน B ภาษาไทยของ proxy คู่กัน, majority of 5)
- k = 10 ต่อ app ต่อ form บน VG (นับ Q48); single shot ต่อ cell; switch ของรายงานใช้ค่า default; ไม่มี override และไม่มี deviation ตามหัวข้อ 5–6
- **ChatGPT (gpt-mini):** reproduced; GF ใน Form A 2 จาก 10 และใน Form B 1 จาก 10; clean ใน Form A 7 จาก 10; ข้อ GF ของ proxy: Q07, Q15, Q30; silence ของ Form B: "most wrong replies gave no warning (1 of 1)"
- **Gemini (gemini-flash):** reproduced; GF ใน Form A 2 จาก 10 และใน Form B 1 จาก 10; clean ใน Form A 8 จาก 10; ข้อ GF ของ proxy: Q14; silence ของ Form B: "most wrong replies gave no warning (2 of 3)"
- **Claude.ai (claude-sonnet):** reproduced; GF ใน Form A 2 จาก 10 และใน Form B 0 จาก 10; clean ใน Form A 6 จาก 10; ข้อ GF ของ proxy: Q14, Q42; silence ของ Form B: "flagged or asked in 2 of 3 wrong replies"
- ตามตัวจำแนก ข้อที่เป็น GF ใน app ตรงกับข้อ GF ของ proxy คู่กันครั้งเดียว (Gemini, Q14)
- sensitivity ของ tag ใน Form A (หัวข้อ 8): เปลี่ยน 0 cell; cell VG ที่ parse ไม่ผ่านแต่จะเป็น GF จากข้อความที่สกัดได้: ไม่มี
- **sensitivity บนฐาน k3 ด้วย suite v1.3 (artifact เท่านั้น):** vocabulary ของ k3 เพิ่มค่า 'None' ที่เก็บในสามคอลัมน์; GF ต่อ app × form, clean และ silence เท่ากับผลบน k3n ทุกค่า ข้อสรุปจึงไม่ต่างระหว่างสองฐาน

#### การตรวจข้อมูลบัญชีก่อน stage (หัวข้อ 15)
- ผู้เขียนตรวจชีต setup และช่อง note ของชีต log ใน `CHAT_LOG.xlsx` ไม่พบชื่อบัญชี อีเมล หรือชื่อบุคคล
- `raw/`: ผู้ช่วยตรวจด้วยสคริปต์ระหว่างป้อนแชต (21 ต.ค. 2026) และก่อน stage ไม่พบชื่อบัญชี
- `shots/`: ระหว่างป้อนแชต ผู้ช่วยเปิดดู contact sheet ของ screenshot ทุกภาพ ไม่พบแถบข้าง ชื่อ หรือรูปบัญชี และผู้เขียนตรวจภาพ settings ทั้ง 6 ภาพ (21 ต.ค. 2026); metadata ของ screenshot มีเพียงขนาดภาพและคำว่า Screenshot
- `anon_sweep.py` บน `results/chat/` (pattern ของ CLAUDE.md, ชื่อย่อที่ผู้เขียนพิมพ์, ชื่อผู้ใช้และชื่อเครื่อง, path ของ home และอีเมล): ไฟล์ข้อความและ xlsx ไม่มี hit
  - ใน PNG มี 8 จุดใน 8 ไฟล์ ทุกจุดอยู่ใน chunk IDAT ซึ่งเป็นข้อมูลพิกเซลที่บีบอัด จึงเป็นไบต์ที่ตรงกับ pattern โดยบังเอิญ ไม่ใช่ข้อความ
  - ตรวจตำแหน่งด้วย `kst_rev/gate0/work/png_hit_chunks.py` sha256 `4e67498560f19e49225c2538ba8cb44a6191fbfb76221b6ce869202b18d988fc`

#### FREEZE STAMP ของผล chat check (25 ต.ค. 2026)
| ไฟล์ | sha256 | หมายเหตุ |
|---|---|---|
| `results/chat/raw_manifest.tsv` | `d7a6068bdd48962bb3c06b25911c61f87a70025671c9b9be30779db530faed8b` | sha256 ของไฟล์ raw 85 ไฟล์ |
| `results/chat/raw/` (85 ไฟล์; tree hash) | `98568cbf741d39be3bbce2399b029ff4bf46a829ccbd1efd928bf29c597b312d` | คำตอบ verbatim |
| `results/chat/shots/` (91 ไฟล์; tree hash) | `d71f0d3d6005adc5b4d934434d3aab4ff270c9b6e903e95286c49bee9b281155` | screenshot 85 ภาพและ settings 6 ภาพ |
| `results/chat/log_index.tsv` | `7d3fd2b745094f7b517be7dd018a36612693f835f1dc267a774180b2511d201a` | 85 แถว |
| `results/chat/chat_session_log.tsv` | `63bd759da8ce2975552d040dd90e5647cbc0c61d917679ba6773438e8c48c800` | time log ของ helper |
| `results/chat/CHAT_LOG.xlsx` | `0a51350201a259252d024760c3a095f86d4d16c766654e092d86946eb9e08a70` | หลัง scrub |
| `results/chat/results_chat.jsonl` | `8d74283af714cd757f64bb9c0c87dffa5bf22afdc9bc31d9cb06c5286b9725af` | turn 1, 84 cell |
| `results/chat/graded_chat_k3n.csv` | `89ae8444752a2edc41b91800b26e22b417039d8a813989c8732901a8ed198f92` | ผลการให้คะแนน |
| `results/chat/vg_codes_chat.tsv` | `71958ceb40035a3296e5994060ef1552edff35341cabc1f3c390f44276961a77` | คลาสของตัวจำแนก |
| `results/chat/vg_audit_chat.xlsx` | `38fcb9a4083e8841865dd5c1a23a46492dd5ab8a5d8dcba599764f4340d16f3e` | หลัง scrub |
| `results/chat/vg_audit_agreement.tsv` | `35985dc961506ecae6e8154234ff5f18f6d17b5a9ca943564e141fd8a46a6c6c` | audit B2.3 |
| `results/chat/silence_round1.xlsx` | `28fce48c7d4e64624c104b7faa0eaaf0703b37821236d5f6dc5867231b30a4f8` | หลัง scrub |
| `results/chat/silence_round2.xlsx` | `403a4c0fd8f5412f2c0372abd25160ea35addd5de929269cce9c731c3bf4504e` | หลัง scrub |
| `results/chat/silence_reconcile.xlsx` | `c17ce8028033e1e4b0f18c28dbc89c6415610c6f90072a94aafdc735f0ca4840` | หลัง scrub |
| `results/chat/silence_final.tsv` | `79224e2209e6a2646a4bdc28a0b331626307c7114f2b2ee6b51caf540dd9c6e8` | code สุดท้าย |
| `results/chat/report/chat_report.txt` | `ec1fe91a5300211c03bfc3cc86a4acd8a6ad440f4133d871229525d6b9556ae8` | รายงานบน k3n |
| `results/chat/report/chat_cells.tsv` | `7d172b02603a7fd1e64bb2df64469986217af1e7dcad441fc696f9a8874d16dc` | ตารางราย cell |
| `results/chat/report_k3/chat_report.txt` | `e8428778c935d612ae651cdc81ab68cc99603ac121e20e2c0ebe2a1bb2c0866e` | sensitivity บน k3 |

### Addendum ของการแก้เล่ม ชุดที่ 4 (26 ต.ค. 2026; claim audit, การบีบเล่มฉบับ camera-ready ให้อยู่ใน 6 หน้า และไฟล์ฉบับสุดท้าย)
- **prereg ก่อนต่อท้ายชุดนี้:** `prereg/preregistration_FROZEN.md` sha256 `258226e16e58a72fc0ac464064e460b24deb4a7914985c97005f2562d7720933` จำนวน 2349 บรรทัด (หลังต่อท้าย addendum ของ chat check)
- **commit ของ chat check:** git commit `c323df34a8173abd650f5feefa7daf969894d718` บน main เวลา commit 2026-10-25T15:01:31+07:00; push ถึง origin แล้ว (3e5f117..c323df3)
- ชุดนี้ไม่มีการรันใหม่ และไม่เปลี่ยนตัวเลข band หรือการวิเคราะห์ใด บันทึกเรื่องต่อไปนี้
  - deviation D-19 และ D-20 และหมายเหตุต่อ D-12, D-17 และ D-18
  - ฉบับ camera-ready: title, abstract, เกณฑ์หน้าและขอบกระดาษ และการบีบเล่มหลังชุดที่ 3
  - ย่อหน้าผลของ chat check ในเล่มและข้อความเรื่อง chat check ใน `SUPPLEMENT.md` ตามที่ addendum ของ chat check ระบุ (บรรทัด 2217)
  - claim audit หลังบีบหน้า (22–23 ต.ค. 2026) และ claim audit สุดท้าย (26 ต.ค. 2026)
  - sha256 ของเล่มและ `SUPPLEMENT.md` ฉบับสุดท้าย
- ทุกข้อในชุดนี้ตัดสินหลังเห็นผลทั้งหมดของรอบ ต.ค. จึงไม่เป็นไปตาม A10 บรรทัด 586
- Response ถึง reviewer (ไม่อยู่ใน repo) อ้าง D-19 และ D-20 จึงต้องต่อท้ายและ push ชุดนี้ก่อนส่ง Response
- ไฟล์การตัดสินที่ชุดนี้อ้างใต้ `kst_rev/drafts/` (cut list v4–v5, ไฟล์ claim audit ทั้งสองรอบ และข้อความ EDAS) เป็นไฟล์ทำงานที่ไม่อยู่ใน git และไม่อยู่ในรายการไฟล์ของแผน snapshot; หลักฐานที่ผู้อ่านตรวจได้คือข้อความที่ยกไว้ในชุดนี้และไฟล์ใน FREEZE STAMP

#### ฉบับ camera-ready
- อีเมลแจ้งผลการพิจารณาของ KST 2027 กำหนดให้ camera-ready คือฉบับแก้ที่ตอบความเห็นของ reviewer ทุกข้อ ("Upload the revised manuscript addressing all reviewer comments") เล่มฉบับแก้จึงเป็นฉบับ camera-ready (`\anonfalse`)
- **ส่วนที่เปลี่ยนเมื่อเปิดชื่อ (นำเข้าเล่ม 23 ต.ค. 2026):** ส่วนผู้แต่ง, คำขอบคุณผู้ประเมินคำแปลคนที่สองใน Acknowledgment และ URL ของ artifact ใน Section VIII
  - ผู้ประเมินคนที่สองยินยอมให้ระบุชื่อเป็นลายลักษณ์อักษรเมื่อ 21 ต.ค. 2026; หลักฐานเก็บนอก repo
- **URL ของ artifact:** ชี้ไปที่ repo ใหม่ชื่อ `thaitext2sql-reproducibility` บน GitHub ตามมติผู้เขียน 23 ต.ค. 2026
  - repo ใหม่จะเป็น snapshot ของ repository นี้ที่ตัดหรือปิดข้อมูลระบุตัวบุคคลและ API key ที่ยกเลิกแล้ว (ยังไม่สร้าง ณ 26 ต.ค. 2026) ส่วน repository นี้คงเป็น private
  - ตามแผน snapshot ที่ผู้เขียนตัดสิน (23 ต.ค. 2026) README ของ snapshot ระบุ commit ต้นทางและ sha256 ก่อนและหลังของไฟล์ที่เปลี่ยน; snapshot สร้างหลัง commit ของชุดนี้
  - Section III-A และ contribution (iv) ของเล่มระบุว่า artifact มีตาราง 10^6 แถวที่สร้างแล้วและฐานข้อมูลของวิชา ณ 26 ต.ค. 2026 ทั้งสองอย่างไม่มีไฟล์ในส่วนของ repository นี้ที่อยู่ใน git (ตาราง 10^6 แถวสร้างลง /tmp ตาม `RUNBOOK.md` และไฟล์ CSV ของวิชาอยู่นอก repository โดยมีเพียงค่า sha256 ใน `harness/db/k3n_inputs.sha256`) และรายการไฟล์ของแผน snapshot (ฉบับ 23 ต.ค. 2026) ยังไม่รวม; ต้องเพิ่มทั้งสองอย่างก่อนเปิด artifact หรือแก้ข้อความในเล่มก่อน upload (ข้อ X1-1 ของ claim audit สุดท้าย)
- **Acknowledgment "Use of AI":** ยังเปิดเผยว่าผู้ช่วย AI ร่าง preregistration ตามบรรทัด 219; claim audit สุดท้าย (ข้อ P7-2) แก้ขอบเขตเป็น "the English core-item wording" และ "proposed wording fixes"

#### title และ abstract
- **title:** "Silently Wrong: Auditing Free-Tier LLM SQL for Thai Database Classrooms with ThaiText2SQL" (ฉบับส่ง) เปลี่ยนเป็น "Silently Wrong: Auditing Free-Tier LLM Proxies for Thai Database Classrooms with ThaiText2SQL"
  - มติผู้เขียน 23 ต.ค. 2026 เพื่อตอบ Reviewer I ข้อ W2 และ RC2 (ให้ title หรือ abstract บอกว่าผลมาจาก API model ที่แทน free chat app)
  - คำว่า "free-tier proxies" ตรงกับคำที่ AMENDMENT-8 หัวข้อ 1 ตรึงไว้
  - ผู้เขียนแก้ช่อง title ใน EDAS เมื่อ 23 ต.ค. 2026 (อีเมลยืนยันของ EDAS 15:59)
- **abstract:** ผลของ chat check ถูกตัดออกจาก abstract ตั้งแต่ร่างวันที่ 22 ต.ค. 2026 และผู้เขียนยืนยันเมื่อ 23 ต.ค. 2026 ก่อนรันรายงานผลของ chat check (24 ต.ค. 2026) ว่า abstract ไม่ใส่ผลนี้ แต่การยืนยันนี้เกิดหลังผู้เขียนป้อนแชตครบและ code audit B2.3 (21 ต.ค. 2026) และหลังเห็นผลการให้คะแนนระดับ run ต่อ app × form (addendum ของ chat check บรรทัด 2303); ผู้เขียนแก้ช่อง abstract ใน EDAS เป็นฉบับแก้เมื่อ 23 ต.ค. 2026
  - หลังชุดที่ 3 abstract เปลี่ยนสองจุด: คำว่า "stored" ตาม D-19 (23 ต.ค. 2026) และประโยคท้ายตามข้อ P1-1 ของ claim audit สุดท้าย (26 ต.ค. 2026; ผู้เขียนตัดสินแบบแก้เอง โดยให้ใช้ถ้อยคำและตัวเลข headline ที่ไม่ overclaim หรือตัดประโยคออกถ้าทำไม่ได้; ถ้อยคำที่ใช้ตรงกับข้อเสนอของผู้ตรวจ)
  - ประโยคท้าย: "Of the proxies' failed runs, 95\% execute without error and 75\% return a non-empty wrong table" เปลี่ยนเป็น "Of failed schema-only proxy runs, 95\% execute without error and 75\% return a non-empty wrong table"
  - เหตุผลของประโยคท้าย: ร้อยละทั้งสองมาจากแขน schema-only บน core (131 และ 103 จาก 138 failed run ตาม Discussion) ส่วนแขน values และชุดขยายมีค่าอื่น แต่ประโยคเดิมไม่ระบุแขน; ตัวเลขไม่เปลี่ยน และประโยคยังระบุร้อยละตามกฎถ้อยคำของ B1
  - ชุดขยายก็ใช้ prompt แบบ schema-only เช่นกัน (167 และ 156 จาก 191 failed run) แต่ abstract บรรยายเฉพาะ suite 60 ข้อและไม่กล่าวถึงชุดขยาย ประโยคท้ายจึงอ่านเป็นผลของ core; Discussion และ Conclusion ระบุ "on the core"
  - ผู้เขียนแก้ช่อง abstract ใน EDAS ตามประโยคท้ายใหม่เมื่อ 26 ต.ค. 2026 (อีเมลยืนยันของ EDAS 19:14)
  - ข้อความ plain text ใน `kst_rev/drafts/EDAS_METADATA_camera_ready_2026-10-23.md` ตรงกับ abstract ของเล่มฉบับสุดท้ายทุกคำ (198 คำ; ผู้ช่วยเทียบ 26 ต.ค. 2026)

#### D-19 คำว่า "stored" ใน clause แม่แบบ A9 ของ abstract (มติผู้เขียน 23 ต.ค. 2026)
- **ชนิด:** ถ้อยคำ; ไม่เปลี่ยนตัวเลข band หรือการวิเคราะห์
- **แผนเดิม**
  - A9 บรรทัด 542: clause ของทุก scenario ใช้ "the [10] items whose gold compares a stored English constant absent from the Thai wording"
  - D-13 (บรรทัด 2042) ย่อเป็น "10 items comparing stored English constants"
  - A9 บรรทัด 535: ย่อได้ แต่ห้ามเปลี่ยนกริยาหรือ qualifier
  - B2.1 บรรทัด 648: ถ้อยคำในเล่มบรรยายว่า gold เทียบค่าภาษาอังกฤษที่เก็บจริงซึ่งไม่ปรากฏในโจทย์ภาษาไทย (อ้าง A9)
- **เหตุผล:** ใน 10 ข้อของ VG10 ค่าคงที่ 'None' ของ Q48 ไม่ได้เก็บอยู่ในฐาน k3n เพราะค่าว่างเก็บเป็น NULL (หมายเหตุ Q48 ของ B2.1) คำว่า "stored" จึงไม่จริงสำหรับ 1 ใน 10 ข้อ และขัดกับ Section III-B ของเล่มที่ระบุว่าค่าคงที่เป็นค่าที่เก็บอยู่ใน 9 ข้อ
- **ช่วงเวลา:** claim audit หลังบีบหน้าพบประเด็นนี้เมื่อ 22 ต.ค. 2026 (ข้อ A15 และ A05 ของ claim audit นั้น); ผู้เขียนอนุมัติ 23 ต.ค. 2026 หลังเห็นผลทั้งหมด จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - abstract ใช้ "8 of the three API proxies' 17 Thai errors fall on 10 items comparing English constants absent from the Thai wording"
  - ตัวเลข 8 จาก 17 และ clause อื่นของบล็อก A9 คงเดิม
  - Section III-B ของเล่มระบุว่าค่าคงที่ของ 9 ข้อเป็นค่าที่เก็บอยู่ และ Q48 เทียบ 'None' ซึ่งฐานไม่เก็บแล้ว แต่ยังอยู่ในชุดตามกฎเชิงไวยากรณ์ที่ลงทะเบียนไว้
  - ช่อง abstract ใน EDAS ใช้ถ้อยคำนี้ตั้งแต่ 23 ต.ค. 2026
- **ผลต่อการตีความ:** abstract อ้างน้อยลง คือไม่อ้างว่าค่าคงที่ทุกตัวเก็บอยู่ในฐาน; ถ้านับเฉพาะ 9 ข้อที่ค่าคงที่เก็บอยู่จริง (VG9) ได้ 7 จาก 17 (บรรทัด 2122) ซึ่งอยู่ใน artifact เท่านั้น

#### D-20 ตาราง sampling config ของ AMENDMENT-3 (มติผู้เขียน 23–26 ต.ค. 2026)
- **ชนิด:** การนำเสนอ; ไม่เปลี่ยนตัวเลข
- **แผนเดิม:** AMENDMENT-3 (7 ส.ค. 2026) บรรทัด 90: "ตารางท้ายว่าแต่ละโมเดลรันด้วย config ใด จะรายงานใน paper (sampling-config table)"
- **เหตุผล**
  - ฉบับส่ง (ส.ค. 2026) เขียน config เป็นข้อความใน Section IV แทนตาราง โดยไม่ได้ลง deviation; ตารางของฉบับส่งคือ Table I–V (ตารางสรุปการแปล, ผลหลัก, ผลรายชั้น, EN–TH และ unanimity) ไม่มีตาราง config
  - ฉบับแก้คงเป็นข้อความ เพราะผู้เขียนกำหนดเมื่อ 22 ต.ค. 2026 ให้เล่มอยู่ใน 6 หน้า และให้ค่าตั้งของแต่ละโมเดลอยู่ในเล่ม
- **ช่วงเวลา**
  - เกิดตั้งแต่ฉบับส่ง (ส.ค. 2026); พบเมื่อ 23 ต.ค. 2026 ระหว่างตรวจ cut list v5 กับ prereg (ชีต deviations ของ `kst_rev/drafts/SQUEEZE_CUTLIST_v5_2026-10-23.xlsx`)
  - บันทึกการตัดสินไม่มีมติแยกของข้อนี้: ผู้เขียนอ่าน Response ส่วนที่ 3 ซึ่งอ้าง D-20 แล้วไม่แก้เมื่อ 23 ต.ค. 2026 และอนุมัติให้ต่อท้าย D-20 พร้อมวันที่ในชุดนี้ก่อนส่ง Response เมื่อ 26 ต.ค. 2026 (ข้อ R2-1 ของ claim audit สุดท้าย) วันที่ของมติจึงระบุเป็นช่วง 23–26 ต.ค. 2026
  - ตัดสินหลังเห็นผลทั้งหมด จึงไม่เป็นไปตามบรรทัด 586
- **สิ่งที่ทำ**
  - Section IV (Protocol) ของเล่มระบุ config ของทุกโมเดลเป็นข้อความ: โมเดล local ใช้ temperature 0 กับ seed คงที่; OpenAI และ Google ใช้ temperature 0; `claude-sonnet-5` ใช้ค่า default ของผู้ให้บริการเพราะ endpoint ปฏิเสธ temperature; ไม่มี request ใดตั้ง reasoning option; มีเพียง request ของ Anthropic ที่มี output cap (1,024 token รวม reasoning)
  - ตารางค่าตั้งรายโมเดล รวมค่า seed 42 ของโมเดล local อยู่ใน AMENDMENT-7 A3 (บรรทัด 331–338) ซึ่งไปกับ artifact และค่าที่ส่งจริงตั้งใน `harness/runner.py`
  - ค่าตั้งเหล่านี้ไม่อยู่ใน `harness/models.json` ตามที่ D-18 ระบุ (หมายเหตุต่อ D-18 ในชุดนี้)
- **ผลต่อการตีความ:** ไม่มีต่อตัวเลข; เล่มให้ข้อมูลเดียวกันในรูปข้อความ ยกเว้นค่า seed (42) ซึ่งเล่มระบุเพียง "fixed seed" และอยู่ใน AMENDMENT-7 A3 และ `harness/runner.py`

#### หมายเหตุต่อ D-12 (26 ต.ค. 2026)
- **ข้อความใน D-12 ที่ไม่เป็นจริงแล้ว:** bullet สุดท้ายของ "สิ่งที่ทำ" ของ D-12 (บรรทัด 2032) ระบุประโยคใน Conclusion "listing the stored values coincided with fewer grounding failures, though not with a reliably smaller gap, and also changed answers on items that need no stored value (Section V-B)"
- **เหตุ:** การบีบเล่มของชุดที่ 3 ตัดประโยคนี้พร้อมประโยคสรุปผลอื่นของ Conclusion (รายการ B13-concl-summary ของ `kst_rev/drafts/SQUEEZE_CUTLIST_v4_2026-10-22.xlsx` ซึ่งบันทึกว่าตัดได้และไม่ขัด prereg; ผู้เขียนอนุมัติ 22 ต.ค. 2026)
  - เล่มฉบับบีบที่ชุดที่ 3 บันทึก (ค่า sha256 ขึ้นต้น dca5001a) และเล่มฉบับสุดท้ายไม่มีประโยคนี้ใน Conclusion
  - addendum ชุดที่ 3 ไม่ได้บันทึกการตัดนี้; ข้อ X2-8 ของ claim audit สุดท้ายพบประเด็นนี้
- **ไม่เป็น deviation ใหม่:** D-12 ระบุเองว่า Conclusion ไม่ใช่ตำแหน่งของแม่แบบ A9
- **ส่วนที่ยังอยู่ในเล่ม**
  - ตำแหน่งแม่แบบ A9 อื่นของ D-12 ยังตรงกับเล่ม: abstract และประโยค S1 ของ RQ2 (ตัวชี้ตารางเปลี่ยนตาม D-15)
  - Discussion ย่อหน้า "Mind the values" ไม่มีตัวเลข: "With the stored values listed, the free-tier proxies made no grounding failures, but the values also changed answers on items that need no stored value and did not coincide with a reliably smaller English--Thai gap (Section~V-B)."
  - ประโยคใน Discussion บรรยายจำนวนในแขน values (0 grounding failure) ด้วย "made no grounding failures" ไม่ใช่ "coincided with fewer" และไม่มีคำเชิงเหตุ

#### หมายเหตุต่อ D-17 (26 ต.ค. 2026)
- **ข้อความใน D-17 ที่ไม่เป็นจริงแล้ว:** "ผลต่อการตีความ" ของ D-17 (บรรทัด 2199) ว่าเล่มไม่ระบุว่ายืนยันไม่ได้ว่า weights ตรงกับฉบับทางการ
- **เหตุ:** หลัง claim audit หลังบีบหน้า (ข้อ A26; ผู้เขียนอนุมัติ 23 ต.ค. 2026) Section IV ของเล่มเขียนว่า weights ของ typhoon2-8b เป็น "community quantization of unverified origin (artifact)" ซึ่งตรงกับถ้อยคำที่ถูกต้องของ addendum ชุดที่ 1 (บรรทัด 2087)
- **ส่วนที่ยังจริง**
  - จำนวนการถามซ้ำอยู่ใน `SUPPLEMENT.md` หัวข้อ 1 ข้อ 9 เท่านั้น
  - caption ของ Table I (ไฟล์ตรึงที่ไม่เปลี่ยน; FREEZE STAMP ท้ายชุดนี้) ยังรายงานคำตอบ 14 คำตอบที่ถูก cap ตัด และ RQ2 ยังระบุ 14 คำตอบ
  - Section IV ยังระบุ cap 1,024 token และ "at most 567 output tokens" ของ core
- **ถ้อยคำที่เปลี่ยน:** ประโยค execution grading ตาม C4 ใน Limitations เปลี่ยน "on our one database" เป็น "on our data" (ข้อ P7-1 ของ claim audit สุดท้าย) เพราะข้อ key-constraint สามข้อของชุดขยาย grade บนฐานหลาย instance; ความหมายตาม C4 คงอยู่ คือโค้ดที่ผิดแต่ได้ผลตรงกับ key บนข้อมูลของวิชาผ่านการให้คะแนน

#### หมายเหตุต่อ D-18 (26 ต.ค. 2026)
- **ข้อความใน D-18 ที่ไม่ครบ:** "สิ่งที่ทำ" ของ D-18 (บรรทัด 2206) ระบุว่า identifier และค่าตั้งของทุกโมเดลอยู่ใน `harness/models.json`
- **เหตุ:** `harness/models.json` sha256 `019ec1785ae857d4fd798048145c7453911dc43a9255f6f13fb70c060ce7b099` (ค่าเดียวกับที่ D-18 บันทึก) เก็บเฉพาะ identifier, ผู้ให้บริการ และช่วงพักระหว่าง call ของแต่ละโมเดล ไม่มีค่า temperature, seed หรือ max_tokens
  - ค่าที่ส่งจริงตั้งใน `harness/runner.py` (temperature 0 ของ OpenAI, Google และโมเดล local, seed 42 ของโมเดล local และ max_tokens 1024 ของ Anthropic) และอยู่ในตาราง A3 ของ AMENDMENT-7 (บรรทัด 331–338)
  - พบระหว่างตรวจร่างชุดนี้ (26 ต.ค. 2026)
- **ส่วนที่ยังจริง:** identifier ของทุกโมเดลอยู่ใน `harness/models.json`; ข้อความอื่นของ D-18 ไม่เปลี่ยน
- **ผลต่อการตีความ:** ไม่มี; ค่าตั้งทุกค่าอยู่ใน prereg และโค้ด

#### เกณฑ์หน้าและขอบกระดาษ
- **จำนวนหน้า:** 6 หน้ารวม reference ตามหน้า Paper Submission ของ KST 2027 ("The length of the paper should be between 4-6 pages") และหน้า Camera-Ready ("Maximum number of pages: 6")
  - ช่อง Final manuscript ของ EDAS รับถึง 7 หน้า แต่ผู้เขียนยึด 6 หน้าและไม่ถาม chair (มติ 22 และ 25 ต.ค. 2026)
- **ขอบกระดาษ:** มติผู้เขียน 25 ต.ค. 2026 ให้ใช้เกณฑ์ขอบข้างอย่างน้อย 1.5 cm ของการตรวจรูปแบบใน EDAS ที่ JCSSE ใช้ เพราะขอบข้างเดิมของเล่ม (IEEEtran แบบ a4paper) วัดได้ 14.05–14.39 mm
  - `\CLASSINPUTinnersidemargin` และ `\CLASSINPUToutersidemargin` เป็น 15.55mm ก่อน `\documentclass`
  - `\addtolength{\topmargin}{0.03in}` ให้ขอบบนไม่ต่ำกว่า 1.8 cm โดยความสูงของข้อความไม่เปลี่ยน
  - ผู้ช่วยทดสอบ build ของเล่มฉบับสุดท้ายที่ 150 dpi: ขอบข้างแคบสุด 91 px (15.41 mm) และขอบบนแคบสุด 18.97 mm
  - ขอบใหม่ทำให้เล่มยาวเป็น 7 หน้า (reference ล้นราว 25 บรรทัด) จึงต้องบีบต่อตามหัวข้อถัดไป

#### การบีบเล่มหลังชุดที่ 3
- **cut list v5 (23 ต.ค. 2026):** หลังนำการแก้ของ claim audit หลังบีบหน้าและการเปลี่ยนเป็น camera-ready เข้า เล่มยาวเกิน 6 หน้า; ผู้เขียนตัดสินรายข้อใน `kst_rev/drafts/SQUEEZE_CUTLIST_v5_2026-10-23.xlsx`
  - ชุดแนะนำ 27 รายการ ตัดทั้งหมด: ตัดวลี 18, ย้ายไป `SUPPLEMENT.md` 3, ใช้ถ้อยคำสำรองที่ claim audit กำหนด 2, ตัด citation ของ Wilson, McNemar และ Holm 3 (claim list ข้อ C44 อนุญาต) และตัดทั้งประโยค 1 รายการ (A10: สองประโยคท้ายของ Conclusion คือ "Auditing instruments make that clause checkable." และคำเชิญให้วิชาอื่นใช้เครื่องมือ ซึ่ง claim list ข้อ C87 ระบุว่าตัดได้)
  - สำรอง 22 รายการ อนุมัติไว้ใช้เมื่อที่ไม่พอ; ผู้เขียนกำหนดไม่ให้ใช้ A08, C26 และ C16 คู่กับรายการในชุดแนะนำเพราะข้อความซ้อนกัน (เช่น A08 ซ้อนกับ A09) และถอน C01, C08, B10 และ B28 ออกจากกลุ่มสำรอง (23 ต.ค. 2026) ด้วยหลักว่าไม่ตัดตัวเลข headline นิยาม หรือรายละเอียดที่รองรับ rigor
  - ชีต deviations ของไฟล์นี้ตรวจทุกข้อที่ prereg กำหนดให้อยู่ในเล่ม ไม่มีรายการใดในชุดแนะนำย้ายหรือเปลี่ยนเนื้อหานั้น จึงไม่มี deviation ใหม่จากการตัดชุดนี้
- **25 ต.ค. 2026:** เมื่อใส่ย่อหน้าผลของ chat check (14:16) เล่มยังได้ 6 หน้า; เมื่อเปลี่ยนประโยคท้ายของย่อหน้าเป็นประโยคเรื่องตัวจำแนกและ audit ของผู้เขียน (15:13; ยาวขึ้นสองบรรทัด) เล่มยาวเป็น 7 หน้า; ใช้สำรอง 3 รายการแล้วได้ 6 หน้า
  - C20: ตัดวลี "with no server restart or configuration reload in between" ใน RQ3 และเพิ่มแถว PostgreSQL settings ใน `SUPPLEMENT.md` หัวข้อ 3 (หลักฐานอยู่ใน addendum ชุดที่ 1 หัวข้อ PostgreSQL settings)
  - C22: ตัด "run at temperature 0 with a fixed seed" ใน RQ4 (ค่าตั้งอยู่ใน Section IV)
  - A29: ตัด "and the one the title records" ใน Conclusion
  - จากนั้นเปลี่ยนขอบกระดาษ (หัวข้อก่อน) แล้วเล่มยาวเป็น 7 หน้าอีกครั้ง
- **26 ต.ค. 2026**
  - สำรอง A06 (Section I ตัดวลีช่องทางของนโยบาย AI), B05 (Section III-A ตัด "(universal-quantification)"), B08 (Section III-B ตัดเหตุผลของกฎข้อ 2 ของการแปล) และ B29 (Section IV ตัดประโยค "We report percentage points, not standardized effect sizes.") ยังได้ 7 หน้า; ข้อความของ B08 และ B29 ย้ายไป `SUPPLEMENT.md` หัวข้อ 4
  - ใส่ `\looseness=-1` ท้ายย่อหน้า 15 ย่อหน้าโดยไม่เปลี่ยนคำ (ผู้ช่วยเทียบไฟล์ก่อนและหลัง: ต่างกันเฉพาะคำสั่งนี้) ยังได้ 7 หน้า
  - cut list v6 ใช้รายการสำรองของ cut list v5 สี่รายการ (ผู้เขียนให้ทำตามคำแนะนำ 26 ต.ค. 2026) ได้ 6 หน้า: A08 (ใช้เฉพาะส่วนที่ A09 ไม่ได้ตัด จึงไม่ซ้อนกับ A09 ซึ่งเป็นเหตุของข้อกำหนดวันที่ 23 ต.ค. 2026; ประโยคปล่อย artifact ใน Conclusion เหลือ "The artifact is released at"; รายการของใน artifact อยู่ใน contribution (iv) ของ Section I), C12 (ตัดตัวเลขของการ code ด้วยมือที่ซ้ำใน RQ2 เหลือ "(Section~IV)"; 186 run, 64.5% และ κ 0.54 อยู่ใน Section IV), A15 (ตัด clause ที่อ้าง UNESCO ใน Section II และย้าย bibitem unesco2023 ไปท้ายรายการให้ลำดับ reference ตามการอ้างครั้งแรก; Conclusion ยังอ้าง) และ C18 (ตัด "The tails teach." ใน RQ3)
  - การแก้ถ้อยคำของ claim audit สุดท้ายไม่เปลี่ยนจำนวนหน้า
- **เนื้อหาที่ย้ายไป `SUPPLEMENT.md` หลังชุดที่ 3** (รหัสในวงเล็บเป็นรายการของ cut list v5)
  - จำนวนแถวของฐาน President (หัวข้อ 4; B01)
  - ตัวเลข 53 จาก 60 ที่อธิบาย κ ของการประเมินคำแปล (หัวข้อ 1 ข้อ 6; B12)
  - การแยกชนิดของ failed run ของชุดขยายพร้อมจำนวนที่ถูก cap ตัด (หัวข้อ 3; C06) และ Wilson interval ของผลรวม 100 ข้อ (หัวข้อ 3; C10)
  - ประโยคการ re-derive ตัวเลข (ย่อหน้าแรก; A09) และคำเชิญให้วิชาอื่นใช้เครื่องมือ (หัวข้อ 5; A10)
  - ค่า PostgreSQL settings (หัวข้อ 3 แถวสุดท้าย; C20), เหตุผลของกฎข้อ 2 ของการแปล (B08) และการรายงานเป็นจุดร้อยละ (B29) (หัวข้อ 4)
- **ผลของ AMENDMENT-9 หัวข้อ 8 ที่เล่มไม่พิมพ์** (หัวข้อนี้ไม่กำหนดให้ผลใดต้องอยู่ในเล่ม; คลาส VG ของชุดขยายอยู่ใน artifact และในเล่มไม่เกินหนึ่งประโยคตามบรรทัด 1831 ซึ่งเล่มไม่มีประโยคนี้; ตาราง hardness และ sensitivity บน k3 อยู่ใน artifact ตามบรรทัด 1833–1834)
  - เล่มคง 167 และ 156 จาก 191 failed run ของชุดขยาย และผลของ pooled 100 ข้อพร้อม exact McNemar
  - การแยก loud พร้อมจำนวนที่ถูก cap ตัด, Wilson interval ของ pooled 100 ข้อ และตารางราย instance ของข้อ MI อยู่ใน `SUPPLEMENT.md` หัวข้อ 3
  - จำนวนข้อต่อ family, EN−TH exact McNemar ต่อโมเดล, positional sensitivity และคลาส VG ของชุดขยายอยู่ใน `results/ext/tables/` (ext_family.csv, ext_mcnemar.csv, ext_positional.csv และ ext_vg_classes.csv)
  - sensitivity บน k3 ของ 37 ข้อที่ใช้ instance เดียว (บรรทัด 1834) อยู่ใน `results/ext/graded_ext_k3_single_instance.csv`
  - ตาราง hardness แบบ Spider ของ 100 ข้อ (บรรทัด 1833) ยังไม่มีในไฟล์ผลของ repository นี้ ณ 26 ต.ค. 2026; RUNBOOK_v2 ขั้น 4.2 และแผน snapshot กำหนดให้ผู้ช่วยเตรียมตารางนี้ก่อนเปิด artifact และถ้าเปิด artifact โดยไม่มีตารางนี้ต้องบันทึกเป็น deviation ใน addendum ถัดไป

#### ส่วนที่ prereg กำหนดให้อยู่ในเล่ม (ตรวจกับเล่มฉบับสุดท้าย)
- ไม่มีส่วนใดถูกตัดออก ทั้งรายการของชุดที่ 3 (บรรทัด 2155) และส่วนที่ชีต deviations ของ cut list v5 ตรวจเพิ่ม; ถ้อยคำที่เปลี่ยนหลังชุดที่ 3 ระบุไว้ในแต่ละข้อ
- รหัส A, B และ C ในหัวข้อนี้เป็นข้อของ AMENDMENT-7 ยกเว้นที่ระบุว่าเป็นรายการของ cut list
- **ประโยคแม่แบบ A9:** abstract (clause ของทุก scenario ตาม D-13 และ D-19, S1 กับ M2 และ G-a) และประโยคของ RQ2 ทั้งสองประโยค; ประโยคของ RQ2 เหมือนเล่มของชุดที่ 3 ทุกตัวอักษร
- **H3 แบบรวมและแบบตัดโมเดลที่เกิน placebo:** คงอยู่ในวงเล็บของ RQ2; "too few for the decision rule" เปลี่ยนเป็น "too few for the preregistered decision rule (at least four)"
- **footnote ของ Q14 (C4):** คงเดิม
- **การ re-code ด้วยมือพร้อม agreement และ κ:** 186 run, 64.5% และ κ 0.54 อยู่ใน Section IV; RQ2 รายงานทั้งค่าของตัวจำแนกและของการ code ด้วยมือ (6 ต่อ 0 และ 5 ต่อ 0; 3, 1 และ 1) ตาม addendum ของ Gate 3 และชี้กลับ Section IV แทนตัวเลขที่ซ้ำ (รายการ C12 ของ cut list v5 ที่ใช้ใน v6)
- **ข้อความของ D-1:** clause ของ Newcombe interval ที่ระบุว่าต่างจาก paired interval ที่ลงทะเบียนไว้ คงเดิม พร้อม citation ของ Newcombe ทั้งสองรายการ
- **ลำดับเวลาการเพิ่ม typhoon2-8b (D-3):** คงเดิมใน Section IV (Roster)
- **ผลรอบ ส.ค. ตาม C5:** คงอยู่ใน RQ2 และเติม "(the latter on the 59 items asked in both collections)"
- **นิยาม loud และ silent (B1):** นิยามสามคลาสอยู่ใน Section IV; ตัวอย่างหม้ายระบุว่าเป็น silent-empty; ป้าย "As an illustration, not a measurement" อยู่ที่ตัวอย่าง silent-non-empty (NULL guard ของข้อ age-gap) ตาม B1 หลังการแก้ของ claim audit หลังบีบหน้า; abstract และ Discussion ระบุร้อยละ
- **ป้าย exploratory ของผลโมเดล local (A10):** มีทุกจุดที่รายงานผลโมเดล local รวม parse rate ใน RQ4 และ † ใน Table I
- **คำที่ AMENDMENT-8 ตรึงไว้:** "chat-app consistency check", "instructor-written student-style prompt", "free-tier proxies", วันที่ป้อนแชตและ "single shot" ทุกครั้งที่รายงานผล (หัวข้อถัดไป)
- **การเปิดเผยการใช้ AI (บรรทัด 219):** คงอยู่ใน Acknowledgment
- **ส่วนที่ชีต deviations ของ cut list v5 ตรวจเพิ่ม**
  - B4: "grade-stable" พร้อม 359 จาก 360 และ 340 จาก 360 (92.5–97.5%); วงเล็บ "(temperature 0 or provider default)" ถูกตัดใน cut list v5 (รายการ C23) เพราะค่าตั้งอยู่ใน Section IV; แม่แบบของ B4 (บรรทัด 759–760) ใช้แทนประโยค "one-in-ten to one-in-twenty" ซึ่งไม่มีในเล่มแล้ว เล่มรายงานส่วนเติมเต็มคือ graded alike 92.5–97.5% ต่อโมเดล ซึ่งเท่ากับคำตอบที่ให้คะแนนต่างกันใน 2.5–7.5% ของ cell ตามแม่แบบ
  - B5: clause ของข้อ top-1-per-group ใน RQ3 คงเดิม
  - A5 บรรทัด 404–405: "(the October calls were billed)" คงเดิม
  - A10 บรรทัด 582: Table I เป็นไฟล์ที่ตรึงและไม่เปลี่ยน
  - addendum ชุดที่ 2 และ D-17: จำนวนคำตอบที่ถูก cap ตัดใน caption ของ Table I และ cap 1,024 token กับ "at most 567" ใน Section IV คงเดิม
  - C4 ประโยค execution grading ใน Limitations: เปลี่ยนถ้อยคำตามหมายเหตุต่อ D-17

#### ย่อหน้าผลของ chat check ในเล่มและข้อความเรื่อง chat check ใน SUPPLEMENT.md
- ย่อหน้าท้าย Section V-B ของ `paper/main_rev.tex` (บรรทัด 489; LaTeX source ตามตัวอักษร)

```tex
In the chat-app consistency check (single shot, entered 21~October 2026), the failure also appeared in the free ChatGPT, Gemini app, and Claude.ai: 2 of 10 Form~A cells in each copied a Thai word into, or invented an English value for, a filter. With the instructor-written student-style prompt (Form~B), 1, 1, and 0 of 10 cells failed this way. Across both forms, failing items matched the same-vendor proxy's only once (Gemini, Q14). Among wrong Form~B replies, most gave no warning in ChatGPT (1 of 1) and Gemini (2 of 3); Claude.ai flagged or asked in 2 of 3 (two blinded coding rounds agreed on 49 of 54 replies, $\kappa = 0.78$). Counts are descriptive; failures use the preregistered classifier; the author's blinded audit adds three Claude.ai failures, on its proxy's Q14 and Q42 (artifact).\looseness=-1
```

- **ตามกฎของ AMENDMENT-8**
  - ระบุวันที่ป้อนแชตและ "single shot"; จำนวน GF cell เป็น a of k (2 of 10 ใน Form A ทุก app; 1, 1 และ 0 of 10 ใน Form B) โดยไม่มีร้อยละหรือ CI (หัวข้อ 10 และ 11)
  - ทั้งสาม app เป็น "reproduced" จึงใช้ "the failure also appeared in the free ..." (หัวข้อ 10)
  - กฎเรื่องความเงียบ: ChatGPT และ Gemini app เข้าเกณฑ์ "most wrong replies gave no warning (s of n)" (1 of 1 และ 2 of 3) และ Claude.ai เข้าเกณฑ์ "flagged or asked in m of n wrong replies" (2 of 3); ในเล่มคำว่า "wrong Form~B replies" อยู่ต้นประโยค ("Among wrong Form~B replies, most gave no warning in ChatGPT (1 of 1) ...")
  - ตัวจำแนกเป็นผลหลัก และเล่มบอกจำนวนที่ audit ของผู้เขียนนับเพิ่มพร้อมข้อที่ตรงกับ proxy
- ย่อหน้า "Chat-app consistency check" ของ Section IV (บรรทัด 364–379) บรรยายวิธีของ check; claim audit สุดท้าย (ข้อ P3-1) แก้ "wrong Form~B replies were coded" เป็น "all Form~B replies were coded" เพราะผู้เขียน code ครบ 54 คำตอบทั้งสองรอบ
- `SUPPLEMENT.md` หัวข้อ 1 ข้อ 5 (บรรทัด 24; ตามตัวอักษร)

```text
5. **Chat-app consistency check.** The check is single shot and single turn on one date (21 October 2026). Form A places the API system prompt inside a user message, so it does not reproduce the API condition exactly. Form B is an instructor-written student-style prompt, not one written by students, and its coding records whether a wrong reply flags stored values, asks back, or gives no warning, but not how a dialogue continues. All 84 chats were entered between 10:43 and 13:21 ICT, cell by cell across the three apps. Silence codes come from two blinded coding rounds at least three days apart (agreement 49 of 54 replies, Cohen's κ 0.78; the five disagreements were reconciled with written reasons, `results/chat/silence_final.tsv`); the style of a reply may reveal its app, so the blind is procedural. The apps' model labels differed from the proxies' identifiers: Claude.ai showed 'Sonnet 5.5 medium' and the Gemini app 'Gemini auto' on every chat, and ChatGPT showed none (`results/chat/log_index.tsv`). These labels are not pinned versions: as the preregistration declares (AMENDMENT-8 §12), the apps can change model or routing without notice, and a free plan may switch to a smaller model under quota; no chat showed a rate-limit or model-switch banner, which does not rule out a silent switch. In a blinded audit of the 14 wrong value-grounding replies (app, form and classifier class hidden), coded on 21 October 2026 by the author, who had also entered the chats that day, the grounding classifier agreed with the author's codes in 8 (57%, Cohen's κ 0.24); the classifier, which the preregistration makes primary, counts 8 grounding failures and the author 11, mainly because it skips literals inside function-wrapped columns. By the author's codes, Claude.ai has grounding failures in 4 of 10 Form A and 1 of 10 Form B cells, among them Q14 and Q42, which its proxy answered wrongly in 4 of 5 Thai runs each; Q42 is a proxy grounding failure only by the classifier, so with the author's codes on both sides Claude.ai and its proxy share only Q14 (`results/chat/vg_audit_agreement.tsv`, `results/rc1/audit/agreement_cells.csv`). On the eight other Form B items (paper Section IV), ChatGPT, the Gemini app and Claude.ai answered 8, 7 and 7 correctly. The two wrong replies (Gemini app Q41, Claude.ai Q50) returned wrong non-empty results and were coded silent; they are among the wrong Form B replies in the paper's silence counts. Correctness matched the same-vendor proxy's October schema-only Thai majority on 6, 6 and 8 of the 8 items: ChatGPT was correct on both items its proxy failed (Q25, Q50); the Gemini app was correct on Q50, which its proxy failed, but wrong on Q41, which its proxy passed; Claude.ai failed Q50, as its proxy did (`results/chat/report/chat_summary.tsv`, NONVG rows; per cell, `results/chat/report/chat_cells.tsv`).
```

- **ข้อความนี้ทำตาม AMENDMENT-8**
  - หัวข้อ 8 (บรรทัด 1646–1649): agreement และ Cohen's κ ของการ code ความเงียบ (49 จาก 54, κ 0.78; ร้อยละ 90.7 และตาราง 3×3 ไม่อยู่ใน `SUPPLEMENT.md` แต่อยู่ใน addendum ของ chat check บรรทัด 2297–2298 และ `results/chat/silence_final_agreement.tsv`), agreement และ Cohen's κ ของ audit ตัวจำแนก B2.3 (8 จาก 14, 57%, κ 0.24), การปิดตาแบบขั้นตอน และการเปิดเผยว่าผู้ code เป็นผู้ป้อนแชตเอง
  - หัวข้อ 10: ผลเชิงพรรณนาของ 8 ข้อที่ไม่ใช่ VG ใน Form B (จำนวนข้อที่ถูก, concordance กับ proxy, การแยก empty กับ non-empty และ silence code)
  - หัวข้อ 12: ข้อจำกัดเรื่องโมเดลในแอปพร้อมป้ายโมเดลที่ UI แสดง
- sha256 ของทั้งสองไฟล์อยู่ใน FREEZE STAMP ท้ายชุดนี้

#### claim audit หลังบีบหน้า (22–23 ต.ค. 2026)
- เล่มฉบับบีบของชุดที่ 3 ตรวจด้วย workflow wf_a946aa40-863 (จบ 22 ต.ค. 2026 23:02): ยืนยัน 43 ข้อ (major 14, minor 29, ไม่มี critical) และถูกหักล้าง 36 ข้อ; 28 จาก 43 ข้อเกี่ยวกับการบีบหน้า
- ผู้เขียนตัดสินรายข้อใน `kst_rev/drafts/CLAIM_AUDIT_POSTSQUEEZE_2026-10-22.xlsx` (23 ต.ค. 2026): แก้ตามข้อเสนอ 40 ข้อ และไม่แก้ 3 ข้อ (A11, A13 และ A17 เรื่องคำว่า released และ public เพราะการ upload ครั้งนี้เป็น camera-ready และ artifact จะเปิดเป็น public)
- ผลต่อ prereg: D-19 (ข้อ A15 และ A05), หมายเหตุต่อ D-17 (ข้อ A26) และป้ายโมเดลที่แอปแสดง (ข้อ A25) ซึ่งอยู่ใน `SUPPLEMENT.md` หัวข้อ 1 ข้อ 5 ตั้งแต่ 25 ต.ค. 2026
- ตัวอย่างการแก้ในเล่ม: errata ใน Section III-C ระบุ "Thai typos" เพราะมีมากกว่าหนึ่งข้อ (`SUPPLEMENT.md` หัวข้อ 2 ข้อ 3 ขยายเป็นรายการตาม `suite/CHANGELOG_v1.2_to_v1.3.md`); ป้าย illustration ย้ายไปอยู่ที่ตัวอย่าง silent-non-empty ตาม B1; parse rate ของโมเดล local มีป้าย exploratory; การสุ่มข้อของ chat check ระบุ "from the August run regraded under the revised key"

#### claim audit สุดท้าย (26 ต.ค. 2026)
- **ขอบเขต:** เล่มหลัง cut list v6 (ค่า sha256 ขึ้นต้น ceb05f76), `SUPPLEMENT.md` (ขึ้นต้น e30a8cd7) และร่าง Response ส่วนที่ 1–3 (ฉบับ 25 ต.ค. 2026); ผู้ตรวจและผู้หักล้างอ่านอย่างเดียว
- **workflow wf_2dcdf42b-344:** ออกแบบผู้ตรวจ 12 ส่วน (P1–P7 เล่ม, S1 `SUPPLEMENT.md`, R1–R2 Response, X1 ความสอดคล้องข้ามเอกสาร และ X2 ความสอดคล้องกับ prereg และคำที่ล้าสมัย)
  - หยุดเมื่อ usage 5 ชั่วโมงถึง 72% (26 ต.ค. 2026) หลังผู้ตรวจ 10 ส่วนเสร็จ แล้วรันต่อ (resume) ให้ผู้หักล้างตรวจข้อที่ค้าง; ผู้ตรวจ X1 และ X2 ไม่ได้รันใน workflow นี้
  - ทุกข้อค้นพบผ่านผู้หักล้าง (adversarial verification): ระดับ high สองมุม (หลักฐาน และกติกากับข้อเสนอแก้) ระดับอื่นหนึ่งมุม
  - รอบหลัก (10 ส่วนที่ไม่ใช่ X1 และ X2): ยืนยัน 65 ข้อ ตกไป 14 ข้อ
- **workflow wf_bc4b2652-de9:** X1 และ X2 บนสำเนาที่แก้ตามคำตัดสินของรอบหลักแล้ว; X1 ตรวจ 236 ข้อความพบ 5 ข้อ, X2 ตรวจ 152 ข้อความพบ 8 ข้อ; ยืนยัน 11 ตกไป 2
- **คำตัดสินของผู้เขียน**
  - รอบหลัก 65 ข้อ (26 ต.ค. 2026; `kst_rev/drafts/CLAIM_AUDIT_FINAL_2026-10-26.xlsx`): ใช้ข้อเสนอของผู้หักล้าง 62 ข้อ, ใช้ข้อเสนอเดิม 2 ข้อ และตัดสินแบบแก้เอง 1 ข้อ (P1-1 ประโยคท้ายของ abstract: ผู้เขียนให้แนวทาง และถ้อยคำที่ใช้ตรงกับข้อเสนอของผู้ตรวจ)
  - X1 และ X2: ผู้เขียนอนุมัติ 6 ข้อที่แก้เอกสาร (26 ต.ค. 2026); อีก 5 ข้อคือหมายเหตุภายในของร่าง Response 2 ข้อ, หมายเหตุต่อ D-12 ในชุดนี้ (X2-8), แผน snapshot (X1-1) และช่อง abstract ใน EDAS ที่ผู้เขียนแก้แล้ว (X1-5)
  - การแก้ทำบนสำเนาด้วย workflow wf_33897c46-ce0 (รอบหลัก), wf_bc4b2652-de9 (จัดข้อความให้ตรงกันข้ามไฟล์ก่อนตรวจ X1 และ X2: `SUPPLEMENT.md` 4 จุดและ Response 6 จุด) และ wf_709105b6-3ac (6 ข้อของ X1 และ X2) แล้วผู้ช่วยตรวจ diff และ build 6 หน้าก่อนนำเข้าไฟล์จริง (26 ต.ค. 2026)
- **รอบหลักแยกตามเอกสารและชนิด**
  - เล่ม 15 ข้อ: `paper/main_rev.tex` 14 ข้อ (overclaim 5, inconsistent 4, prereg 2, emphasis 1, unsupported 1, typo 1) และ caption ของ Table I 1 ข้อ (emphasis; caption เป็นไฟล์ที่ตรึงจึงไม่แก้ และเติมข้อมูลใน `SUPPLEMENT.md` หัวข้อ 1 ข้อ 9 แทน)
  - `SUPPLEMENT.md` 11 ข้อ (inconsistent 4, unsupported 2, prereg 2, overclaim 1, emphasis 1, false 1)
  - Response 39 ข้อ (ส่วนที่ 1: 12, ส่วนที่ 2: 7, ส่วนที่ 3: 20)
- **การแก้ในเล่ม:** ถ้อยคำและขอบเขตเท่านั้น 13 บรรทัดเมื่อเทียบกับฉบับที่ตรวจ ไม่มีตัวเลขใดเปลี่ยน (ย่อหน้า chat check เพิ่มเฉพาะเลขข้อ Q14 และ Q42)
  - abstract: "Of failed schema-only proxy runs" (หัวข้อ title และ abstract)
  - Section III-A: "the nine items that select rows by rank" แทน "the nine items whose answer would otherwise depend on ties" (Q02 มีปีเกิดที่เสมอกันแต่ไม่มี clause tiebreak; errata อยู่ใน `SUPPLEMENT.md` หัวข้อ 2 ข้อ 3) และ "five universal-quantification items" แทน "five relational-division items"
  - Section III-C: "Dated amendments record later changes" แทน "record each later change"
  - Section IV: "October local inference, grading, and analysis" (สภาพแวดล้อมที่ระบุเป็นของรอบ ต.ค.) และ "all Form~B replies were coded"
  - RQ2: "(Amendment~7, item~A8)" แทน "(Amendment~7, A8)" (X1-3)
  - ย่อหน้า chat check: "failing items matched the same-vendor proxy's only once", "Counts are descriptive; failures use the preregistered classifier" และ "the author's blinded audit adds three Claude.ai failures, on its proxy's Q14 and Q42"
  - Limitations: "on our data" แทน "on our one database"
  - Conclusion: ";" แทน ":" ตัวที่สองของประโยค
  - Acknowledgment: "the English core-item wording" และ "proposed wording fixes"
- **การแก้ใน `SUPPLEMENT.md` ที่ทำตามสัญญาเดิม**
  - หัวข้อ 3 แถว column-order sensitivities (เทียบคอลัมน์ตามตำแหน่ง และไม่ใช้บทบาทคอลัมน์; C5 ข้อ 3): addendum ชุดที่ 3 (บรรทัด 2157) ระบุว่าผลอยู่ใน `SUPPLEMENT.md` หัวข้อ 3 แต่ฉบับของชุดที่ 3 มีเพียงแถว VG9 (X2-1)
  - หัวข้อ 1 ข้อ 5: ผลของ 8 ข้อที่ไม่ใช่ VG ใน Form B ตาม AMENDMENT-8 หัวข้อ 10 (X2-6) และข้อจำกัดเรื่องโมเดลในแอปตามหัวข้อ 12 (X2-5)
  - หัวข้อ 1 ข้อ 5: agreement ของ audit ตัวจำแนกของ chat check (8 จาก 14, 57%, κ 0.24) ซึ่งเพิ่มเมื่อ 25 ต.ค. 2026 (ผู้เขียนอนุมัติถ้อยคำ) และเติมการเปิดเผยตาม AMENDMENT-8 หัวข้อ 8 (S1-5)
- **การแก้อื่นใน `SUPPLEMENT.md`**
  - ย่อหน้าแรก: ไฟล์นี้ถือเพียงบางส่วนของสิ่งที่เล่มชี้ว่า "in the artifact" และชี้ไฟล์อื่นใน repository; ตัวเลขมาจากไฟล์ที่ระบุหรือจาก prereg ยกเว้นค่าความสอดคล้องของการประเมินคำแปลในข้อ 6 ซึ่งคำนวณจาก rating sheet สองไฟล์ (ค่าที่ไม่รวม Q27 ไม่มีไฟล์ผล)
  - ข้อ 1: ระบุการทดสอบ exact McNemar ทั้งสามชุด (EN–TH แบบ Holm ข้ามหกโมเดล, แขน values แบบ Holm ข้ามสาม proxy และคู่ typhoon2-8b กับ llama3.1:8b แบบไม่ปรับ) และ item-bootstrap 95% ของ gap share
  - ข้อ 3: ทั้งสองรอบให้คะแนนด้วย key v1.3n (แขน base), ตัวชี้ `results/rc1/rev_numbers/decomposition.csv` และระบุว่าการเทียบนี้ไม่ใช่การรันซ้ำตรงตัว (D-8)
  - ข้อ 6: ความต่าง +2.4 ต่อ +12.3 รวมทั้งหกโมเดลและโมเดล local เป็น exploratory (A10)
  - ข้อ 9: run ที่ถูก cap ตัดตัดสิน majority ภาษาไทยของ X07, X17 และ X37 และ gap ของ Claude อาจสูงเกินจริงได้ถึงสามข้อ
  - ข้อ 10: "on our data" แทน "on our one database" (P7-1)
  - หัวข้อ 3: ย่อหน้านำระบุข้อยกเว้นของไฟล์ PostgreSQL settings ที่ผู้เขียนเก็บหลังการรัน, แถว Wilson ของชุดขยายต่อโมเดล และแถวรายละเอียดของ RQ3 plan quality
  - หัวข้อ 4: ข้อ Translation rule (2) (รายการ B08 ของ cut list v5) ระบุว่ามาจากประสบการณ์การสอนของผู้เขียน
- Response แก้ตามคำตัดสินและจัดให้ตรงกับเล่ม (ไม่อยู่ใน repo)

#### FREEZE STAMP ของไฟล์ฉบับสุดท้าย (26 ต.ค. 2026)
| ไฟล์ | sha256 | หมายเหตุ |
|---|---|---|
| `paper/main_rev.tex` | `0ef12c4c35c1c0c03f33027b11a6d8a6f6fb8506db296ec0c643c5ab2896c2c4` | 624 บรรทัด; 6 หน้ารวม reference เมื่อ compile ด้วย xelatex (A4; ไม่มีฟอนต์ Type 3) |
| `SUPPLEMENT.md` | `9a38fe74c7674fb3249ea6c60a9630c32b5aeeac9c49243aa887b250a6934ea0` | 83 บรรทัด |
| `paper/generated_rev/tab_headline_rev.tex` | `95389bc7f63cb96b1468c125196bf2c8b758911e0fadc3d89cf3084a57eb09fc` | Table I ที่เล่มใช้; ไม่เปลี่ยนตั้งแต่ชุดที่ 2 |
| `results/chat/report/chat_summary.tsv` | `9105dba65e22c8bfa36270c4a1d12bee1c4fabed0e05572b6e4b372f2b86bd93` | แถว NONVG ที่ `SUPPLEMENT.md` หัวข้อ 1 ข้อ 5 อ้าง |
| `results/chat/silence_final_agreement.tsv` | `eaf529c2d0adc5cef3023f8de10ba3c704293677d29ea7fd918356cadefbf03e` | ร้อยละ agreement และตาราง 3×3 ของ silence code |

- เล่มและ `SUPPLEMENT.md` ตามตารางนี้ commit พร้อมชุดนี้; ไฟล์อื่นในตารางไม่เปลี่ยนในชุดนี้
