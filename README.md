# BJT DC Bias Web App — Lab 02 (ENG29 2121)

Flask web application สำหรับคำนวณ DC operating point ของวงจร
**NPN Common-Emitter Voltage-Divider Bias** ด้วย forward-active approximation

รับค่า `VCC, R1, R2, RC, RE, β, VBE` จากฟอร์ม แล้วให้ Python backend คำนวณ
`VB, VE, VC, VCE, IC, IB, IE` พร้อมหน่วย, validation และ warning เมื่ออยู่นอก
ช่วงที่แบบจำลองใช้ได้

## โครงสร้าง

```
app.py                  Flask routes (GET /, POST /calculate)
dc_bias.py              สมการ + validation (ไม่รู้จัก HTML/HTTP)
templates/index.html    ฟอร์มและตารางผล (Jinja)
static/style.css        หน้าตาเว็บ
tests/test_dc_bias.py   unit tests ของสมการ
tests/test_web.py       HTTP tests ด้วย Flask test client
docs/                   design-note, validation, reflection
```

## ติดตั้ง

```bash
python -m venv .venv
```

Activate virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

ติดตั้ง dependencies:

```bash
python -m pip install -r requirements.txt
```

## รันเว็บ

```bash
python -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

> ต้องรันผ่าน Flask server เท่านั้น การ double-click เปิด `templates/index.html`
> ด้วย `file://` จะไม่มีการคำนวณ เพราะไม่มี Python backend

## ทดสอบ

```bash
python -m unittest discover -s tests -v
```

## ตัวอย่าง

ค่าเริ่มต้นในฟอร์มคือค่าตัวอย่างของใบงาน: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ,
RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

ผลที่ได้:

| ปริมาณ | ค่า |
|---|---|
| VB | 1.942 V |
| VE | 1.242 V |
| VC | 9.294 V |
| VCE | 8.052 V |
| IC | 1.230 mA |
| IB | 12.30 µA |
| IE | 1.242 mA |
| Region | active |

## หน่วย

- ตัวต้านทาน `R1, R2, RC, RE` กรอกเป็น **kΩ** (โค้ดคูณ 1000 เป็น Ω ก่อนคำนวณ)
- `VCC, VBE` เป็นโวลต์, `β` ไม่มีหน่วย
- ผลลัพธ์: แรงดันเป็น V, `IC/IE` เป็น mA, `IB` เป็น µA

## สมการที่ใช้

```
VTH = VCC · R2 / (R1 + R2)        RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β · IB          IE = (β+1) · IB
VE  = IE · RE         VB = VE + VBE
VC  = VCC − IC · RC   VCE = VC − VE
```

## ข้อจำกัด

แบบจำลองนี้ไม่ใช่ ngspice และไม่ครอบคลุม AC, transient, Bode plot หรือ bias
topology อื่น ถ้า `VTH ≤ VBE` (cutoff) หรือ `VCE ≤ 0.3 V` (ใกล้ saturation)
เว็บจะแสดง warning ว่าค่าที่ได้ไม่ควรใช้โดยไม่ตรวจสอบ
