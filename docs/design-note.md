# Design Note — Lab 02 BJT DC Bias Web App

วันที่: 2026-11-10 · ENG29 2121 · Noppadon007
ขอบเขต: **ยึดตาม Lab 02 handout เท่านั้น** (Week 2 = DC Bias)

---

## 1. เป้าหมาย

Flask web application หลายไฟล์สำหรับ NPN Common-Emitter Voltage-Divider Bias
รับ `VCC, R1, R2, RC, RE, β, VBE` จากฟอร์ม แล้วให้ Python backend คำนวณ
DC operating point (Forward-Active approximation) และแสดงผลในเบราว์เซอร์
ผ่าน `http://127.0.0.1:5000/` พร้อม tests และ commit ขึ้น GitHub

## 2. ขอบเขต

**ทำ (ตาม handout):**
- ฟอร์ม input 7 ค่า + ปุ่ม Calculate DC Bias
- คำนวณ `IB, IC, IE, VB, VE, VC, VCE` ด้วย Python (ไม่ hardcode ใน HTML)
- แสดงผลพร้อมหน่วย + IB/IE (handout: "ควรแสดง IB/IE ได้ด้วย")
- Validation: ค่าผิด/ไม่ครบ/ไม่ใช่ตัวเลข → error ที่อ่านรู้เรื่อง หน้าไม่ล้ม
- Warning: `VTH ≤ VBE` (cutoff) และ `VCE` ต่ำใกล้ saturation
- Tests: ≥3 engineering tests + ≥1 Flask test client
- README วิธีติดตั้ง/รัน/ทดสอบ

**ไม่ทำ (handout ระบุชัดว่าไม่ต้องใน Week 2):**
Bode plot, transient, signal generator, overlay animation, SPICE/ngspice solver,
bias type อื่น (Fixed/Emitter), interactive schematic, FET, ฐานข้อมูล, auth, JS framework

**Anti-goals:**
- ตัวเลข DC Bias hardcode ใน HTML/JS
- ต้องเปิด `index.html` ด้วย `file://` จึงเห็นผล
- commit `.venv/`, `__pycache__/`, `.env`
- แสดงผลนอก active region โดยไม่มี warning

## 3. โครงสร้างไฟล์ (ตรงตาม handout §04)

```
app.py                  Flask application & HTTP routes
dc_bias.py              engineering calculations (ไม่รู้จัก HTML/HTTP)
templates/index.html    input form + DC results (Jinja)
static/style.css        responsive layout
tests/test_dc_bias.py   unit tests for engineering logic
tests/test_web.py       Flask HTTP route tests
requirements.txt        Flask
README.md               install/run instructions
AGENTS.md               AI coding conventions
docs/design-note.md     เอกสารนี้
docs/validation.md      ตารางเทียบผลกับการคำนวณอิสระ
docs/reflection.md      สิ่งที่ได้เรียนรู้
```

**Data flow:** Browser form → `POST /calculate` → `app.py` parse/validate →
`dc_bias.calculate_voltage_divider()` → ผล + warnings → Jinja render
`index.html` → HTML กลับไปเบราว์เซอร์

## 4. แบบจำลอง

```
VTH = VCC · R2 / (R1 + R2)      RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β · IB        IE = (β+1) · IB
VE  = IE · RE       VB = VE + VBE
VC  = VCC − IC · RC     VCE = VC − VE
```

**หน่วย:** ฟิลด์ตัวต้านทานกรอกเป็น **kΩ** (ตามค่าตัวอย่างใน handout: 100 kΩ, 22 kΩ,
2.2 kΩ, 1 kΩ) แล้วแปลงเป็น Ω ด้วย `× 1000` ที่ขอบของ `dc_bias.py` ก่อนคำนวณ
`VCC, VBE` เป็น V, `β` ไม่มีหน่วย
ผลลัพธ์: แรงดันเป็น V, `IC/IE` เป็น mA, `IB` เป็น µA

**Region (ตาม handout §06):**

| เงื่อนไข | การแสดงผล |
|---|---|
| `VTH ≤ VBE` | warning: วงจรอยู่ใกล้/อยู่ใน cutoff, approximation ใช้ไม่ได้ |
| `VCE ≤ 0.3 V` | warning: ใกล้ saturation, ค่าที่ได้ไม่น่าเชื่อถือ |
| อื่น ๆ | Active — แสดงผลปกติ |

`VTH`, `RTH` ใช้ภายในโมดูลเท่านั้น ไม่แสดงบนหน้าจอ

## 5. Validation

| กรณี | ข้อความ |
|---|---|
| ว่าง / ไม่ใช่ตัวเลข | "R1 ต้องเป็นตัวเลข" |
| `R ≤ 0` | "R1 ต้องมากกว่า 0 kΩ" |
| `β ≤ 0` | "β ต้องมากกว่า 0" |
| `VCC ≤ 0` | "VCC ต้องมากกว่า 0 V" |
| `VBE < 0` หรือ `VBE ≥ VCC` | "VBE ต้องอยู่ระหว่าง 0 ถึง VCC" |

ถ้ามี error: render ฟอร์มเดิมพร้อมค่าที่กรอก + error box, **HTTP 200**, ไม่คำนวณต่อ

## 6. UI

2 คอลัมน์บนเดสก์ท็อป / คอลัมน์เดียวบนมือถือ, ไม่ใช้ JS หรือ CDN

```
┌──────────────────────────────────────────────────────┐
│ BJT DC Bias — Voltage Divider (NPN)                  │
├──────────────────────────┬───────────────────────────┤
│ Inputs                   │ DC Operating Point        │
│  VCC [12  ] V            │  [ ACTIVE REGION ]        │
│  R1  [100 ] kΩ           │  VB  1.942 V              │
│  R2  [22  ] kΩ           │  VE  1.242 V              │
│  RC  [2.2 ] kΩ           │  VC  9.294 V              │
│  RE  [1   ] kΩ           │  VCE 8.052 V              │
│  β   [100 ]              │  IC  1.230 mA             │
│  VBE [0.70] V            │  IB  12.30 µA             │
│  [ Calculate DC Bias ]   │  IE  1.242 mA             │
│                          │  ⚠ warning (ถ้ามี)        │
└──────────────────────────┴───────────────────────────┘
```

ค่าเริ่มต้นในฟอร์ม = ตัวอย่างใน handout

## 7. แผนทดสอบ

`tests/test_dc_bias.py`
1. ค่าอ้างอิง handout (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.7)
   → VB≈1.942 V, VE≈1.242 V, VC≈9.294 V, VCE≈8.052 V, IC≈1.230 mA (tol 1e-3)
2. แปลง kΩ → Ω ถูกต้อง (R1=100 kΩ ให้ผลเท่ากับ 100000 Ω ในสมการ)
3. `R ≤ 0` / `β ≤ 0` → คืน error ไม่ raise exception
4. non-numeric → error
5. `VTH ≤ VBE` → warning cutoff
6. `VCE ≤ 0.3 V` → warning saturation

`tests/test_web.py`
7. `GET /` → 200 + ฟิลด์ครบ 7 ตัว
8. `POST /calculate` ค่าตัวอย่าง → 200 + แสดง 1.230 (หรือ 1.23)
9. `POST /calculate` `R1=0` → 200 + ข้อความ error
10. `POST /calculate` ค่า cutoff → 200 + warning

## 8. ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|---|---|
| Python 3.14.2 อาจมีปัญหา wheel | Flask เป็น pure Python → ความเสี่ยงต่ำ |
| ชื่อโฟลเดอร์ขึ้นต้นด้วยเว้นวรรค | ควรเปลี่ยนเป็น `BJT-DC-Bias-Web-App` ก่อน push แรก |

## 9. สิ่งที่ builder ตัดสินเอง

class names, spacing, ถ้อยคำ warning นอกเหนือจากตาราง §5, จำนวน test ที่เกินขั้นต่ำ
