import math
import unittest
from dataclasses import replace

from dc_bias import (KOHM_TO_OHM, Params, REGION_ACTIVE, REGION_CUTOFF,
                     REGION_SATURATION, calculate_voltage_divider, parse_inputs)


def reference_params() -> Params:
    return Params(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                  re=1_000.0, beta=100.0, vbe=0.70)


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

    def test_rejects_nan(self):
        params, errors = parse_inputs(self.valid_raw(r1="nan"))
        self.assertIsNone(params)
        self.assertTrue(any("R1" in e for e in errors))

    def test_rejects_infinity(self):
        params, errors = parse_inputs(self.valid_raw(beta="inf"))
        self.assertIsNone(params)
        self.assertTrue(any("β" in e for e in errors))

    def test_rejects_overflow_to_infinity(self):
        params, errors = parse_inputs(self.valid_raw(vcc="1e400"))
        self.assertIsNone(params)
        self.assertTrue(any("VCC" in e for e in errors))

    def test_vcc_zero_reports_only_vcc(self):
        params, errors = parse_inputs(self.valid_raw(vcc="0"))
        self.assertIsNone(params)
        self.assertEqual(len(errors), 1)
        self.assertIn("VCC", errors[0])

    def test_rejects_zero_resistance_on_every_resistor(self):
        for field, label in (("r1", "R1"), ("r2", "R2"), ("rc", "RC"), ("re", "RE")):
            params, errors = parse_inputs(self.valid_raw(**{field: "0"}))
            self.assertIsNone(params)
            self.assertTrue(any(label in e for e in errors), f"{label} not reported")


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


if __name__ == "__main__":
    unittest.main()
