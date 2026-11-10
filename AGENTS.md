# AI Coding Conventions — BJT DC Bias Web App

## ขอบเขต

Lab 02 ทำเฉพาะ DC Bias ของ NPN Common-Emitter Voltage-Divider Bias เท่านั้น
**ห้ามเพิ่ม** Bode plot, transient, signal generator, SPICE solver, bias type อื่น,
interactive schematic หรือ FET — สิ่งเหล่านี้อยู่นอกขอบเขต Week 2

## การแยกความรับผิดชอบ

- `dc_bias.py` — สมการและ validation เท่านั้น **ห้าม import Flask หรือสร้าง HTML**
- `app.py` — HTTP routing, แปลงผลเป็นข้อความ, render template
- `templates/index.html` — แสดงผลเท่านั้น **ห้ามคำนวณหรือ hardcode ผล DC Bias**
- `static/style.css` — หน้าตา ไม่มี JavaScript หรือ CDN ภายนอก

## หน่วย

- อินพุตตัวต้านทานเป็น kΩ, คูณ `KOHM_TO_OHM` (= 1000) เป็น Ω ก่อนเข้าสมการ
- ภายใน `dc_bias.py` ใช้ SI ทั้งหมด: โวลต์และโอห์ม
- แสดง `VB, VE, VC, VCE` เป็น V (3 ตำแหน่ง), `IC, IE` เป็น mA (3 ตำแหน่ง),
  `IB` เป็น µA (2 ตำแหน่ง)

## Validation และ Warning

- Input ผิด → คืน error ภาษาไทยที่ระบุชื่อฟิลด์ และตอบ **HTTP 200** พร้อมคงค่า
  ที่ผู้ใช้กรอก (ห้ามปล่อย 500)
- Warning มีเพียง 2 กรณี: `VTH ≤ VBE` (cutoff) และ `VCE ≤ 0.3 V` (saturation)
- ห้ามรายงานผลนอก active region ว่าเป็นค่าที่เชื่อถือได้

## ก่อน commit

1. รัน `python -m unittest discover -s tests -v` ต้องเขียวทั้งหมด
2. ตรวจว่าไม่มี `.venv/`, `__pycache__/`, `.env` ถูก track
3. เปิดเว็บทดสอบด้วยค่าตัวอย่างของใบงานหนึ่งครั้ง
4. Commit ผ่าน **GitHub Desktop** (ไม่ใช้ `git commit` ใน terminal)
