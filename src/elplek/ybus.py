"""Y-bus assembly from the basic network model."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .impedance import impedance_admittance, stamp_two_node
from .model import Network


def build_ybus(network: Network) -> NDArray[np.complex128]:
    """Build the nodal admittance matrix for all series-impedance branches.

    Ground is represented by terminal ID 0 and has no matrix row/column.
    Matrix ordering follows network.buses insertion order. This first version
    supports series R+jX branches only; shunts, transformers, mutual coupling,
    sequence networks and IEC peak corrections are not included.
    """
    n = len(network.buses)
    ybus = np.zeros((n, n), dtype=np.complex128)
    index = network.bus_index

    for branch in network.branches:
        y = impedance_admittance(branch.resistance, branch.reactance)
        upstream = 0 if branch.from_bus == 0 else index[branch.from_bus] + 1
        downstream = 0 if branch.to_bus == 0 else index[branch.to_bus] + 1
        stamp_two_node(ybus, upstream, downstream, y)

    return ybus

def build_sequence_ybus(
    network: Network,
    sequence: str,
) -> NDArray[np.complex128]:
    """Build a sequence-specific Y-bus matrix.

    positive uses each branch's resistance + j*reactance.
    negative uses negative_sequence_impedance when provided and otherwise
    falls back to positive-sequence impedance as an approximation.
    zero requires zero_sequence_impedance for every branch; missing data
    raises ValueError rather than silently assuming a grounding path.
    """
    if sequence not in {"positive", "negative", "zero"}:
        raise ValueError("sequence must be 'positive', 'negative', or 'zero'")

    n = len(network.buses)
    ybus = np.zeros((n, n), dtype=np.complex128)
    index = network.bus_index

    for branch in network.branches:
        if sequence == "positive":
            impedance = complex(branch.resistance, branch.reactance)
        elif sequence == "negative":
            impedance = branch.negative_sequence_impedance
            if impedance is None:
                impedance = complex(branch.resistance, branch.reactance)
        else:
            impedance = branch.zero_sequence_impedance
            if impedance is None:
                label = branch.name or f"{branch.from_bus}-{branch.to_bus}"
                raise ValueError(f"Branch {label} has no zero-sequence impedance")

        y = impedance_admittance(impedance.real, impedance.imag)
        upstream = 0 if branch.from_bus == 0 else index[branch.from_bus] + 1
        downstream = 0 if branch.to_bus == 0 else index[branch.to_bus] + 1
        stamp_two_node(ybus, upstream, downstream, y)

    return ybus

