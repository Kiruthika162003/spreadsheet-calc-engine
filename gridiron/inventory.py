"""Inventory costing: FIFO, LIFO, and weighted average, and why they disagree.

When units are bought at different prices and then sold, the
cost assigned to what left, and so the profit reported, depends
entirely on which units you say went out the door, and the
three conventions give three different answers from the same
transactions. FIFO sells the oldest layer first, so in a
rising market the cheap old stock is expensed and profit
looks high; LIFO sells the newest first, expensing the dear
recent stock and reporting lower profit; weighted average
blends every layer into one running cost per unit. This
module runs all three over the same purchase-and-sale
sequence and reports cost of goods sold and ending inventory
value, because the honest thing a costing tool does is show
that the method is a choice with consequences, not a fact.
The one hard refusal is overselling: a sale of more units
than are on hand is refused with the shortage named, because
inventory cannot go negative and a system that lets it
silently is one where the shrinkage hides. FIFO and LIFO keep
explicit cost layers and consume them in order, while
weighted average recomputes the blended cost on every
purchase, the moving-average method, so a sale is always
costed at the average as of that moment rather than a
period-end average that would smear a late purchase back over
earlier sales.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass
class Layer:
    quantity: float
    unit_cost: float


@dataclass
class CostingResult:
    cogs: float
    ending_units: float
    ending_value: float


def _run_layers(
    events: list[tuple[str, float, float]], lifo: bool
) -> CostingResult:
    layers: list[Layer] = []
    cogs = 0.0
    for kind, quantity, unit_cost in events:
        if kind == "buy":
            layers.append(
                Layer(
                    quantity=quantity, unit_cost=unit_cost
                )
            )
            continue
        remaining = quantity
        while remaining > 1e-12:
            if not layers:
                raise Invalid(
                    f"a sale of {quantity} oversells the "
                    "inventory; stock cannot go negative"
                )
            layer = layers[-1] if lifo else layers[0]
            take = min(layer.quantity, remaining)
            cogs += take * layer.unit_cost
            layer.quantity -= take
            remaining -= take
            if layer.quantity <= 1e-12:
                layers.remove(layer)
    ending_units = sum(la.quantity for la in layers)
    ending_value = sum(
        la.quantity * la.unit_cost for la in layers
    )
    return CostingResult(
        cogs=round(cogs, 10),
        ending_units=round(ending_units, 10),
        ending_value=round(ending_value, 10),
    )


def fifo(
    events: list[tuple[str, float, float]],
) -> CostingResult:
    return _run_layers(events, lifo=False)


def lifo(
    events: list[tuple[str, float, float]],
) -> CostingResult:
    return _run_layers(events, lifo=True)


def weighted_average(
    events: list[tuple[str, float, float]],
) -> CostingResult:
    units = 0.0
    value = 0.0
    cogs = 0.0
    for kind, quantity, unit_cost in events:
        if kind == "buy":
            units += quantity
            value += quantity * unit_cost
            continue
        if quantity > units + 1e-12:
            raise Invalid(
                f"a sale of {quantity} oversells the "
                f"{units} on hand; stock cannot go negative"
            )
        average = value / units if units else 0.0
        cogs += quantity * average
        value -= quantity * average
        units -= quantity
    return CostingResult(
        cogs=round(cogs, 10),
        ending_units=round(units, 10),
        ending_value=round(value, 10),
    )
