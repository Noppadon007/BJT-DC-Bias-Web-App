"""Engineering calculations for the BJT common-emitter voltage-divider bias.

This module never imports Flask or touches HTML: the web layer converts user
input into :class:`Params` and renders the resulting :class:`BiasResult`.

Input units are kOhm for the four resistors and volt for VCC/VBE. Everything
inside this module is SI: ohm and volt.
"""

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

KOHM_TO_OHM = 1000.0

REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "beta": "",
    "vbe": "V",
}


@dataclass(frozen=True)
class Params:
    """Validated circuit parameters in SI units (V, ohm)."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


REGION_ACTIVE = "active"
REGION_CUTOFF = "cutoff"
REGION_SATURATION = "saturation"

VCE_SAT_THRESHOLD = 0.3


@dataclass(frozen=True)
class BiasResult:
    """DC operating point. Currents in ampere, voltages in volt."""

    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    ve: float
    vb: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]


def _parse_float(raw: Mapping[str, str], field: str, errors: list[str]) -> float | None:
    text = raw.get(field)
    if text is None or str(text).strip() == "":
        errors.append(f"{_LABELS[field]} ต้องเป็นตัวเลข")
        return None
    try:
        value = float(str(text).strip())
    except ValueError:
        errors.append(f"{_LABELS[field]} ต้องเป็นตัวเลข")
        return None
    if not isfinite(value):
        errors.append(f"{_LABELS[field]} ต้องเป็นตัวเลขที่จำกัด (ไม่รองรับ NaN หรือ Infinity)")
        return None
    return value


def parse_inputs(raw: Mapping[str, str]) -> tuple[Params | None, list[str]]:
    """Validate raw form strings and convert resistor values from kOhm to ohm.

    Returns ``(params, [])`` when every value is usable, otherwise
    ``(None, errors)`` with one readable Thai message per problem.
    """
    errors: list[str] = []
    values: dict[str, float] = {}

    for field in REQUIRED_FIELDS:
        value = _parse_float(raw, field, errors)
        if value is not None:
            values[field] = value

    if errors:
        return None, errors

    for field in ("r1", "r2", "rc", "re"):
        if values[field] <= 0:
            errors.append(f"{_LABELS[field]} ต้องมากกว่า 0 {_UNITS[field]}")

    if values["beta"] <= 0:
        errors.append("β ต้องมากกว่า 0")

    if values["vcc"] <= 0:
        errors.append("VCC ต้องมากกว่า 0 V")

    if values["vcc"] > 0 and (values["vbe"] < 0 or values["vbe"] >= values["vcc"]):
        errors.append("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    if errors:
        return None, errors

    return (
        Params(
            vcc=values["vcc"],
            r1=values["r1"] * KOHM_TO_OHM,
            r2=values["r2"] * KOHM_TO_OHM,
            rc=values["rc"] * KOHM_TO_OHM,
            re=values["re"] * KOHM_TO_OHM,
            beta=values["beta"],
            vbe=values["vbe"],
        ),
        [],
    )


def calculate_voltage_divider(p: Params) -> BiasResult:
    """Solve the DC operating point with the forward-active approximation."""
    vth = p.vcc * p.r2 / (p.r1 + p.r2)
    rth = p.r1 * p.r2 / (p.r1 + p.r2)

    ib = (vth - p.vbe) / (rth + (p.beta + 1) * p.re)
    ic = p.beta * ib
    ie = (p.beta + 1) * ib

    ve = ie * p.re
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    vce = vc - ve

    if vth <= p.vbe:
        region = REGION_CUTOFF
        warnings = (
            "VTH ≤ VBE: วงจรอยู่ในช่วง cutoff แบบจำลอง forward-active "
            "approximation ใช้ไม่ได้",
        )
    elif vce <= VCE_SAT_THRESHOLD:
        region = REGION_SATURATION
        warnings = (
            "VCE ใกล้หรือต่ำกว่า saturation (≤ 0.3 V): ค่า IC จากสมการ "
            "ไม่น่าเชื่อถือ",
        )
    else:
        region = REGION_ACTIVE
        warnings = ()

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        ve=ve,
        vb=vb,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
