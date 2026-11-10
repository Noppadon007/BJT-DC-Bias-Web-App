"""Flask web layer for the BJT DC bias calculator.

The HTTP layer only parses the form, calls :mod:`dc_bias`, and renders the
template. Physics lives in ``dc_bias.py``.
"""

from flask import Flask, render_template, request

from dc_bias import BiasResult, calculate_voltage_divider, parse_inputs

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


def format_result(r: BiasResult) -> dict[str, str]:
    """Turn SI results into display strings with units."""
    return {
        "vb": f"{r.vb:.3f} V",
        "ve": f"{r.ve:.3f} V",
        "vc": f"{r.vc:.3f} V",
        "vce": f"{r.vce:.3f} V",
        "ic": f"{r.ic * 1000:.3f} mA",
        "ib": f"{r.ib * 1e6:.2f} µA",
        "ie": f"{r.ie * 1000:.3f} mA",
        "region": r.region,
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            form=DEFAULT_FORM,
            errors=[],
            result=None,
            display={},
        )

    @app.post("/calculate")
    def calculate():
        params, errors = parse_inputs(request.form)
        if params is None:
            return render_template(
                "index.html",
                form=request.form,
                errors=errors,
                result=None,
                display={},
            )

        result = calculate_voltage_divider(params)
        return render_template(
            "index.html",
            form=request.form,
            errors=[],
            result=result,
            display=format_result(result),
        )

    return app


app = create_app()
