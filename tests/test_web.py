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
        self.assertIn("3.422", html)
        self.assertIn("2.695", html)

    def test_ib_and_ie_use_their_own_units(self):
        html = self.post().get_data(as_text=True)
        self.assertIn("12.30 µA", html)
        self.assertIn("1.242 mA", html)

    def test_region_badge_is_shown(self):
        html = self.post().get_data(as_text=True)
        self.assertIn("ACTIVE", html.upper())


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
        self.assertIn("alert--warning", html)
        self.assertIn("VTH", html)

    def test_saturation_case_shows_warning(self):
        html = self.post(rc="15").get_data(as_text=True)
        self.assertIn("SATURATION", html.upper())
        self.assertIn("alert--warning", html)
        self.assertIn("ไม่น่าเชื่อถือ", html)

    def test_missing_field_through_route_does_not_500(self):
        data = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
                "re": "1", "vbe": "0.70"}
        res = self.client.post("/calculate", data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn("β ต้องเป็นตัวเลข", res.get_data(as_text=True))


class StaticAssetsTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_stylesheet_is_served(self):
        with self.client.get("/static/style.css") as res:
            self.assertEqual(res.status_code, 200)
            self.assertIn("text/css", res.headers["Content-Type"])

    def test_page_links_stylesheet_and_has_no_external_cdn(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="/static/style.css"', html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
