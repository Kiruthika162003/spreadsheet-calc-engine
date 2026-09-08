from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.optimizer import Optimizer
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def model(formula: str) -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 0.0)
    engine.set_formula(ref("B1"), formula)
    return engine


class TestMinimize:
    def test_a_parabola_bottoms_at_its_vertex(self):
        engine = model("=(A1-3)*(A1-3)")
        result = Optimizer(engine=engine).minimize(
            ref("B1"), ref("A1"), 0.0, 10.0
        )
        assert result.input_value == pytest.approx(
            3.0, abs=1e-4
        )
        assert result.output_value == pytest.approx(
            0.0, abs=1e-6
        )

    def test_the_input_cell_holds_the_optimum(self):
        engine = model("=(A1-3)*(A1-3)")
        Optimizer(engine=engine).minimize(
            ref("B1"), ref("A1"), 0.0, 10.0
        )
        assert engine.value(ref("A1")) == pytest.approx(
            3.0, abs=1e-4
        )

    def test_the_verdict_names_it_local(self):
        engine = model("=(A1-3)*(A1-3)")
        line = (
            Optimizer(engine=engine)
            .minimize(ref("B1"), ref("A1"), 0.0, 10.0)
            .line()
        )
        assert "local minimum" in line
        assert "bracket tighter" in line


class TestMaximize:
    def test_a_dome_peaks_at_its_vertex(self):
        engine = model("=5-(A1-2)*(A1-2)")
        result = Optimizer(engine=engine).maximize(
            ref("B1"), ref("A1"), 0.0, 10.0
        )
        assert result.input_value == pytest.approx(
            2.0, abs=1e-4
        )
        assert result.output_value == pytest.approx(
            5.0, abs=1e-6
        )

    def test_max_and_min_share_one_search(self):
        # Minimizing the negated dome finds the same vertex.
        engine = model("=(A1-2)*(A1-2)-5")
        result = Optimizer(engine=engine).minimize(
            ref("B1"), ref("A1"), 0.0, 10.0
        )
        assert result.input_value == pytest.approx(
            2.0, abs=1e-4
        )


class TestRefusals:
    def test_an_inverted_bracket_is_refused(self):
        engine = model("=A1*A1")
        with pytest.raises(Invalid) as caught:
            Optimizer(engine=engine).minimize(
                ref("B1"), ref("A1"), 5.0, 1.0
            )
        assert "low < high" in str(caught.value)

    def test_a_model_error_halts_the_search(self):
        engine = model("=SQRT(A1)")
        # Every probe in a negative bracket is a #NUM!.
        with pytest.raises(Invalid) as caught:
            Optimizer(engine=engine).minimize(
                ref("B1"), ref("A1"), -4.0, -1.0
            )
        assert "wound is nonsense" in str(caught.value)
