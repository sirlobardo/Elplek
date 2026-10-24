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
