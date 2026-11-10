# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flask web app หลายไฟล์ที่รับ `VCC, R1, R2, RC, RE, β, VBE` แล้วคำนวณ DC operating point ของ NPN Common-Emitter Voltage-Divider Bias ด้วย Python พร้อม validation, region warning และ tests

**Architecture:** `dc_bias.py` เก็บคณิตศาสตร์ล้วน (parse หน่วย kΩ→Ω, validation, คำนวณ, ตัดสิน region) ไม่ import Flask หรือ HTML ส่วน `app.py` ทำ HTTP routing, แปลงผลเป็นข้อความ และ render `templates/index.html` ผ่าน Jinja + `static/style.css`

**Tech Stack:** Python 3.14.2, Flask 3.x, `unittest` (ไม่ใช้ pytest — handout ใช้ `python -m unittest discover -s tests -v`), ไม่มี JavaScript

**Spec:** `docs/design-note.md`

## Global Constraints

- ฟิลด์ตัวต้านทานรับหน่วย **kΩ** และคูณ `1000` เป็น Ω ก่อนเข้าสมการ (`KOHM_TO_OHM = 1000.0`)
- `VCC`, `VBE` หน่วย V; `β` ไม่มีหน่วย
- แสดง `VB, VE, VC, VCE` เป็น V (ทศนิยม 3 ตำแหน่ง), `IC, IE` เป็น mA (3 ตำแหน่ง), `IB` เป็น µA (2 ตำแหน่ง)
- Warning มีเพียง 2 กรณี: `VTH ≤ VBE` (cutoff) และ `VCE ≤ 0.3` (saturation) — `VCE_SAT_THRESHOLD = 0.3`
- Validation error → HTTP **200** พร้อมคงค่าที่ผู้ใช้กรอก ไม่ใช่ 400/500
- ห้าม hardcode ผล DC Bias ใน HTML; ห้ามใช้ JS หรือ CDN ภายนอก
- ไฟล์ต้องตรงตาม handout §04: `app.py`, `dc_bias.py`, `templates/index.html`, `static/style.css`, `tests/test_dc_bias.py`, `tests/test_web.py`, `requirements.txt`, `README.md`, `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
- **Commit ทำผ่าน GitHub Desktop เท่านั้น** ไม่ใช้ `git commit` ใน terminal
- ค่าตัวอย่างอ้างอิง: VCC=12, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70
  → VB=1.942 V, VE=1.242 V, VC=9.294 V, VCE=8.052 V, IC=1.230 mA, IB=12.30 µA, IE=1.242 mA

## Review Focus

กรณีที่ spec ไม่ได้เขียนไว้แต่ผู้ใช้มีโอกาสเจอ — แต่ละข้อมี test ใน task ที่รับผิดชอบ:

1. ผู้ใช้เว้นวรรคหัวท้ายช่องกรอก (`" 12 "`) → ต้อง parse ได้ ไม่ error (Task 1)
2. ผู้ใช้พิมพ์ทศนิยมด้วย comma (`"0,7"`) → ต้องได้ error ที่อ่านรู้เรื่อง ไม่ crash (Task 1)
3. `VBE` เท่ากับ `VCC` พอดี → ต้อง error ไม่ใช่ warning (Task 1)
4. ช่องที่ไม่มี key ส่งมาเลย (ฟอร์มถูกแก้/ยิง request เอง) → ต้องได้ error ไม่ใช่ `KeyError` (Task 1)
5. `β = 1` (ค่านอกโลกจริงแต่ผู้ใช้อาจลอง) → ต้องไม่หารศูนย์หรือให้ `inf` (Task 2)

---

### Task 1: `dc_bias.py` — โครงข้อมูล, การแปลงหน่วย และ validation

**Files:**
- Create: `requirements.txt`
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `KOHM_TO_OHM: float = 1000.0`
  - `REQUIRED_FIELDS: tuple[str, ...] = ("vcc","r1","r2","rc","re","beta","vbe")`
  - `@dataclass(frozen=True) class Params` — `vcc: float` (V), `r1, r2, rc, re: float` (Ω), `beta: float`, `vbe: float` (V)
  - `parse_inputs(raw: Mapping[str, str]) -> tuple[Params | None, list[str]]` — คืน `(params, [])` เมื่อถูกต้อง หรือ `(None, errors)` เมื่อผิด

- [ ] **Step 1: เขียน failing test**

```python
# tests/test_dc_bias.py
import unittest

from dc_bias import KOHM_TO_OHM, Params, parse_inputs


class ParseInputsTest(unittest.TestCase):
    def valid_raw(self, **overrides):
        raw = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
               "re": "1", "beta": "100", "vbe": "0.70"}
        raw.update(overrides)
        return raw

    def test_converts_kohm_to_ohm(self):
        params, errors = parse_inputs(self.valid_raw())
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.r1, 100 * KOHM_TO_OHM)
        self.assertAlmostEqual(params.rc, 2.2 * KOHM_TO_OHM)
        self.assertAlmostEqual(params.vcc, 12.0)

    def test_tolerates_surrounding_whitespace(self):
        params, errors = parse_inputs(self.valid_raw(vcc=" 12 ", beta=" 100 "))
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.vcc, 12.0)

    def test_rejects_zero_resistance(self):
        params, errors = parse_inputs(self.valid_raw(r1="0"))
        self.assertIsNone(params)
        self.assertTrue(any("R1" in e for e in errors))

    def test_rejects_non_numeric(self):
        params, errors = parse_inputs(self.valid_raw(rc="abc"))
        self.assertIsNone(params)
        self.assertTrue(any("RC" in e for e in errors))

    def test_rejects_comma_decimal_separator(self):
        params, errors = parse_inputs(self.valid_raw(vbe="0,7"))
        self.assertIsNone(params)
        self.assertEqual(len(errors), 1)

    def test_rejects_non_positive_beta(self):
        params, errors = parse_inputs(self.valid_raw(beta="0"))
        self.assertIsNone(params)
        self.assertTrue(any("β" in e for e in errors))

    def test_rejects_vbe_equal_to_vcc(self):
        params, errors = parse_inputs(self.valid_raw(vbe="12"))
        self.assertIsNone(params)
        self.assertTrue(any("VBE" in e for e in errors))

    def test_reports_missing_field_instead_of_crashing(self):
        raw = self.valid_raw()
        del raw["beta"]
        params, errors = parse_inputs(raw)
        self.assertIsNone(params)
        self.assertTrue(any("β" in e for e in errors))
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: สร้าง `requirements.txt` และ implement `parse_inputs`**

`requirements.txt` มีบรรทัดเดียว: `Flask>=3.0`

ใน `dc_bias.py`: แปลงข้อความเป็น `float` ด้วย `float(value.strip())` ภายใน `try/except ValueError`, คูณ `KOHM_TO_OHM` ให้ `r1, r2, rc, re`, ตรวจตามลำดับ: ฟิลด์หาย (`raw.get(...)` → `None`), non-numeric, `R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, `VBE < 0 หรือ VBE ≥ VCC` เก็บ error เป็นข้อความภาษาไทยที่ระบุชื่อฟิลด์ (`"R1 ต้องมากกว่า 0 kΩ"`, `"β ต้องมากกว่า 0"` ฯลฯ) และคืน `(None, errors)` ถ้ามี error อย่างน้อยหนึ่งข้อ

- [ ] **Step 4: รันเทสให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: PASS 8 tests

---

### Task 2: `calculate_voltage_divider` — สมการ DC Bias

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `Params` จาก Task 1
- Produces:
  - `@dataclass(frozen=True) class BiasResult` — `vth, rth, ib, ic, ie, ve, vb, vc, vce: float` (กระแสเป็น A, แรงดันเป็น V), `region: str`, `warnings: tuple[str, ...]`
  - `calculate_voltage_divider(p: Params) -> BiasResult`

- [ ] **Step 1: เขียน failing test**

```python
def reference_params() -> Params:
    return Params(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                  re=1_000.0, beta=100.0, vbe=0.70)


class CalculateTest(unittest.TestCase):
    def test_matches_handout_reference_values(self):
        r = calculate_voltage_divider(reference_params())
        self.assertAlmostEqual(r.vth, 2.164, delta=1e-3)
        self.assertAlmostEqual(r.rth, 18_033.0, delta=1.0)
        self.assertAlmostEqual(r.ib, 12.30e-6, delta=1e-7)
        self.assertAlmostEqual(r.ic, 1.230e-3, delta=1e-6)
        self.assertAlmostEqual(r.ie, 1.242e-3, delta=1e-6)
        self.assertAlmostEqual(r.ve, 1.242, delta=1e-3)
        self.assertAlmostEqual(r.vb, 1.942, delta=1e-3)
        self.assertAlmostEqual(r.vc, 9.294, delta=1e-3)
        self.assertAlmostEqual(r.vce, 8.052, delta=1e-3)

    def test_beta_changes_ic(self):
        low = calculate_voltage_divider(replace(reference_params(), beta=50.0))
        high = calculate_voltage_divider(replace(reference_params(), beta=200.0))
        self.assertGreater(high.ic, low.ic)

    def test_beta_of_one_stays_finite(self):
        r = calculate_voltage_divider(replace(reference_params(), beta=1.0))
        self.assertTrue(math.isfinite(r.ic))
        self.assertTrue(math.isfinite(r.vce))
```

(`replace` และ `math` เพิ่มใน import ต้นไฟล์)

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ImportError: cannot import name 'calculate_voltage_divider'`

- [ ] **Step 3: implement `BiasResult` และ `calculate_voltage_divider` ตามสมการใน `docs/design-note.md` §4**

คำนวณ `vth`, `rth`, `ib = (vth - vbe) / (rth + (beta + 1) * re)`, `ic = beta * ib`, `ie = (beta + 1) * ib`, `ve`, `vb`, `vc`, `vce` ตามลำดับ ในขั้นนี้ให้ `region=REGION_ACTIVE` และ `warnings=()`

- [ ] **Step 4: รันเทสให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: PASS 11 tests

---

### Task 3: Region และ warning

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `REGION_ACTIVE = "active"`, `REGION_CUTOFF = "cutoff"`, `REGION_SATURATION = "saturation"`
  - `VCE_SAT_THRESHOLD = 0.3`
  - `BiasResult.region` เปลี่ยนค่าตามเงื่อนไข และ `BiasResult.warnings` มีข้อความภาษาไทย 1 ข้อในกรณี cutoff/saturation

- [ ] **Step 1: เขียน failing test**

```python
class RegionTest(unittest.TestCase):
    def test_reference_case_is_active_without_warning(self):
        r = calculate_voltage_divider(reference_params())
        self.assertEqual(r.region, REGION_ACTIVE)
        self.assertEqual(r.warnings, ())

    def test_low_vth_is_cutoff(self):
        r = calculate_voltage_divider(replace(reference_params(), vbe=2.5))
        self.assertEqual(r.region, REGION_CUTOFF)
        self.assertTrue(any("cutoff" in w.lower() for w in r.warnings))

    def test_small_vce_is_saturation(self):
        r = calculate_voltage_divider(replace(reference_params(), rc=15_000.0))
        self.assertEqual(r.region, REGION_SATURATION)
        self.assertTrue(any("saturation" in w.lower() for w in r.warnings))
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ImportError: cannot import name 'REGION_ACTIVE'`

- [ ] **Step 3: เพิ่มการตัดสิน region ใน `calculate_voltage_divider`**

ตรวจ `vth <= vbe` ก่อน (cutoff) แล้วจึง `vce <= VCE_SAT_THRESHOLD` (saturation) มิฉะนั้น active; warning ต้องมีคำว่า `cutoff` / `saturation` เพื่อให้บทเรียนเรื่อง approximation ตรงกับ handout §06

- [ ] **Step 4: รันเทสทั้งไฟล์ให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: PASS 14 tests

- [ ] **Step 5: Checkpoint — commit ผ่าน GitHub Desktop**

เปิด GitHub Desktop → ตรวจว่าไม่มี `.venv/`, `__pycache__/` → Summary: `Add DC bias engineering module with unit tests` → Commit to main

---

### Task 4: Flask app + ฟอร์ม (GET /)

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `parse_inputs`, `calculate_voltage_divider`, `BiasResult` จาก Tasks 1–3
- Produces:
  - `DEFAULT_FORM: dict[str, str] = {"vcc":"12","r1":"100","r2":"22","rc":"2.2","re":"1","beta":"100","vbe":"0.70"}`
  - `create_app() -> Flask` และ module-level `app = create_app()`
  - Template context keys: `form` (dict ของ raw string), `errors` (list[str]), `result` (`BiasResult | None`), `display` (dict ของข้อความที่จัดรูปแบบแล้ว, ว่างเมื่อไม่มีผล)

- [ ] **Step 1: เขียน failing test**

```python
# tests/test_web.py
import unittest

from app import create_app


class WebFormTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_index_returns_200_and_all_input_fields(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{name}"', html)

    def test_index_shows_handout_defaults(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="100"', html)
        self.assertIn('value="0.70"', html)
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: implement `create_app` + `templates/index.html` ฟอร์มพื้นฐาน**

`GET /` render `index.html` ด้วย `form=DEFAULT_FORM`, `errors=[]`, `result=None`, `display={}`; ฟอร์มเป็น `method="post" action="/calculate"` และทุก input มี `name` ตรงกับ `REQUIRED_FIELDS` พร้อม `value="{{ form.vcc }}"` ฯลฯ (Jinja รองรับ `form.vcc` บน dict)

- [ ] **Step 4: รันเทสให้ผ่าน**

Run: `python -m unittest tests.test_web -v`
Expected: PASS 2 tests

---

### Task 5: POST /calculate — เส้นทางสำเร็จ

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Produces: `format_result(r: BiasResult) -> dict[str, str]` ใน `app.py` คืน key `vb`, `ve`, `vc`, `vce`, `ic`, `ib`, `ie`, `region` เป็นข้อความพร้อมหน่วย (`"1.942 V"`, `"1.230 mA"`, `"12.30 µA"`)

- [ ] **Step 1: เขียน failing test**

```python
class CalculateRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def post(self, **overrides):
        data = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}
        data.update(overrides)
        return self.client.post("/calculate", data=data)

    def test_valid_post_renders_dc_bias_values(self):
        res = self.post()
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("1.942", html)
        self.assertIn("9.294", html)
        self.assertIn("1.230", html)
        self.assertIn("8.052", html)

    def test_values_are_computed_not_hardcoded(self):
        html = self.post(r1="47").get_data(as_text=True)
        self.assertNotIn("1.942", html)

    def test_region_badge_is_shown(self):
        html = self.post().get_data(as_text=True)
        self.assertIn("ACTIVE", html.upper())
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — 404 (route ยังไม่มี) หรือ `AssertionError` หาค่าไม่พบ

- [ ] **Step 3: เพิ่ม route `POST /calculate` และผลลัพธ์ใน template**

เรียก `parse_inputs(request.form)` → ถ้าผ่านเรียก `calculate_voltage_divider` → `display = format_result(result)` แล้ว render หน้าเดิมพร้อม `result`/`display`; template แสดงตารางผล VB/VE/VC/VCE/IC/IB/IE และ badge region ด้วย `result.region`

- [ ] **Step 4: รันเทสให้ผ่าน**

Run: `python -m unittest tests.test_web -v`
Expected: PASS 5 tests

---

### Task 6: แสดง error และ warning

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `errors: list[str]` จาก `parse_inputs`, `result.warnings: tuple[str, ...]`
- Produces: error box และ warning box ใน `index.html`; ค่าที่ผู้ใช้กรอกถูกคงไว้ใน `form`

- [ ] **Step 1: เขียน failing test**

```python
class ErrorAndWarningTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def post(self, **overrides):
        data = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}
        data.update(overrides)
        return self.client.post("/calculate", data=data)

    def test_invalid_input_shows_error_and_keeps_values(self):
        res = self.post(r1="0")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("R1 ต้องมากกว่า 0 kΩ", html)
        self.assertIn('name="r2"', html)
        self.assertIn('value="22"', html)

    def test_non_numeric_input_shows_error(self):
        res = self.post(rc="abc")
        self.assertEqual(res.status_code, 200)
        self.assertIn("RC ต้องเป็นตัวเลข", res.get_data(as_text=True))

    def test_cutoff_case_shows_warning(self):
        html = self.post(vbe="2.5").get_data(as_text=True)
        self.assertIn("CUTOFF", html.upper())
        self.assertIn("approximation", html.lower())

    def test_saturation_case_shows_warning(self):
        html = self.post(rc="15").get_data(as_text=True)
        self.assertIn("SATURATION", html.upper())
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — ไม่พบข้อความ error/warning ใน HTML

- [ ] **Step 3: เพิ่ม error box, warning box และคงค่า form**

ถ้า `errors` ไม่ว่าง: render ฟอร์มด้วย `form=request.form` (คงค่าที่กรอก) และแสดง error box ที่วน `errors`; ถ้า `result.warnings` ไม่ว่าง: แสดง warning box ที่วน `warnings` ได้

- [ ] **Step 4: รันเทสทั้งชุดให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 23 tests (14 engineering + 9 web)

- [ ] **Step 5: Checkpoint — commit ผ่าน GitHub Desktop**

Summary: `Add Flask routes, template, validation and region warnings`

---

### Task 7: `static/style.css` และการเชื่อมโยง

**Files:**
- Create: `static/style.css`
- Modify: `templates/index.html` (เพิ่ม `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`)
- Test: `tests/test_web.py`

**Interfaces:**
- Produces: layout 2 คอลัมน์ที่ยุบเป็นคอลัมน์เดียวใต้ 720px; ไม่มี `@import` หรือ `url(http...)`

- [ ] **Step 1: เขียน failing test**

```python
class StaticAssetsTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_stylesheet_is_served(self):
        res = self.client.get("/static/style.css")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/css", res.headers["Content-Type"])

    def test_page_links_stylesheet_and_has_no_external_cdn(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="/static/style.css"', html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — 404 สำหรับ `/static/style.css`

- [ ] **Step 3: สร้าง `static/style.css` และเพิ่ม `<link>`**

ใช้ CSS variables โทน navy/teal, `.layout` เป็น grid 2 คอลัมน์ (`grid-template-columns: minmax(0,1fr) minmax(0,1fr)`) → `@media (max-width: 720px) { .layout { grid-template-columns: 1fr; } }`, ตัวเลขผลลัพธ์ใช้ `font-family: Consolas, monospace`, `.error` และ `.warning` มีพื้นหลังสีต่างกัน

- [ ] **Step 4: รันเทสทั้งชุดให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 25 tests

- [ ] **Step 5: ตรวจด้วยตาเปล่า**

Run: `python -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
Expected: เห็นฟอร์มซ้าย/ผลขวา, กด Calculate ด้วยค่าตัวอย่างได้ VB=1.942 V, IC=1.230 mA, badge ACTIVE

---

### Task 8: เอกสารประกอบ (README, AGENTS, validation, reflection)

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`

**Interfaces:** ไม่มีโค้ด — เอกสารอ้างคำสั่งและตัวเลขจาก Tasks 1–7

- [ ] **Step 1: เขียน `README.md`** ให้มีลำดับคำสั่งที่รันตามได้จริง: `python -m venv .venv`, activate ตาม OS (Windows PowerShell `.venv\Scripts\Activate.ps1`, Linux/macOS `source .venv/bin/activate`), `python -m pip install -r requirements.txt`, `python -m flask --app app run --debug`, `python -m unittest discover -s tests -v`, URL `http://127.0.0.1:5000/`, และตัวอย่างอินพุต/เอาต์พุตของ handout

- [ ] **Step 2: เขียน `AGENTS.md`** ระบุกติกา: `dc_bias.py` ห้าม import Flask, ห้าม hardcode ผลลัพธ์ใน HTML, รัน `python -m unittest discover -s tests -v` ก่อนทุก commit, หน่วยเป็น kΩ ที่อินพุตและ Ω ภายใน, commit ผ่าน GitHub Desktop

- [ ] **Step 3: เขียน `docs/validation.md`** เป็นตารางเทียบ 3 เคสกับการคำนวณอิสระ: (ก) ค่าตัวอย่าง handout, (ข) `R1=47 kΩ`, (ค) `rc=15 kΩ` (saturation) โดยแต่ละแถวมี `VTH, RTH, IB, IC, IE, VE, VB, VC, VCE` และผลการรันเว็บจริง

- [ ] **Step 4: เขียน `docs/reflection.md`** ตอบคำถาม §10 ของ handout 4 ข้อ (ทำไม `file://` ไม่เท่ากับ Flask, ฟอร์มส่งข้อมูลไป Python อย่างไร, แก้สมการใน `dc_bias.py` ต้องแก้ HTML ไหม, ทำไม region ที่แบบจำลองใช้ไม่ได้ต้องมี warning)

- [ ] **Step 5: รันเทสทั้งชุดยืนยันว่าเอกสารไม่ทำให้อะไรพัง**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 25 tests

- [ ] **Step 6: Checkpoint — commit ผ่าน GitHub Desktop**

Summary: `Add styling and lab documentation` · ตรวจChanges ว่าไม่มี `.venv/` หรือ `__pycache__/` · กด Push origin

---

## Self-Review

**1. Spec coverage:** A1 (Task 4) · A2 (Task 5) · A3 (Tasks 2, 8) · A4 (Tasks 1, 6) · A5 (Tasks 3, 6) · A6 (Tasks 1–7 รวม 25 tests) · A7 (Task 8) — ครบทุกข้อ รวมถึงไฟล์ใน handout §04 ทั้ง 12 ไฟล์

**2. Step scan:** ทุก step มีผลลัพธ์ตรวจได้ (test fail → implement → test pass → checkpoint) ไม่มี step ที่เป็น "handle edge cases" ลอย ๆ

**3. Type consistency:** `Params` (Ω) ใช้ทั้ง Tasks 1–3; `BiasResult` มี `region`/`warnings` ตั้งแต่ Task 2 และถูกใช้ใน `format_result` (Task 5) และ template (Task 6) ตรงกัน; `DEFAULT_FORM` ใช้ทั้ง `GET /` และ template

**4. Review Focus:** ทั้ง 5 กรณีมี test อยู่ใน Task 1 (4 กรณี) และ Task 2 (1 กรณี)

**5. Proportion:** แผนยาวกว่า `docs/design-note.md` เล็กน้อย แต่ไม่มี code block ที่เป็น body ของ implementation — มีแต่ signature, test และค่าที่ตรึงไว้
