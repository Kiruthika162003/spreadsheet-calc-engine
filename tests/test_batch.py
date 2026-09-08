from __future__ import annotations

import pytest

from gridiron.batch import Batch, measure_batch_saving
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def summed_engine() -> Engine:
    engine = Engine()
    for row in range(1, 11):
        engine.set_literal(ref(f"A{row}"), float(row))
    engine.set_formula(ref("C1"), "=SUM(A1:A10)")
    engine.set_formula(ref("C2"), "=C1*2")
    return engine


class TestTheBatch:
    def test_ten_edits_one_recalc(self):
        engine = summed_engine()
        batch = Batch(engine=engine)
        for row in range(1, 11):
            batch.set_literal(ref(f"A{row}"), float(row * 10))
        _report, receipt = batch.commit()
        assert receipt == (
            "10 edit(s), 2 evaluation(s) in one recalc"
        )
        assert engine.value(ref("C1")) == 550.0
        assert engine.value(ref("C2")) == 1100.0

    def test_batched_formulas_compute_in_the_same_close(self):
        engine = summed_engine()
        batch = Batch(engine=engine)
        batch.set_literal(ref("A1"), 100.0)
        batch.set_formula(ref("D1"), "=A1+C1")
        batch.commit()
        assert engine.value(ref("D1")) == 100.0 + 154.0

    def test_the_closed_batch_refuses_more_edits(self):
        engine = summed_engine()
        batch = Batch(engine=engine)
        batch.set_literal(ref("A1"), 1.0)
        batch.commit()
        with pytest.raises(Invalid) as caught:
            batch.set_literal(ref("A2"), 2.0)
        assert "wearing one receipt" in str(caught.value)

    def test_the_empty_batch_has_nothing_to_commit(self):
        with pytest.raises(Invalid):
            Batch(engine=Engine()).commit()


class TestTheMeasuredSaving:
    def test_the_saving_is_measured_not_asserted(self):
        edits = [
            (f"A{row}", float(row * 10))
            for row in range(1, 11)
        ]
        verdict = measure_batch_saving(summed_engine, edits)
        assert verdict == (
            "one-at-a-time paid 20 evaluation(s), the batch "
            "paid 2; 18 saved, measured by the engine's own "
            "reports"
        )
