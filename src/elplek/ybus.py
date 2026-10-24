"""Y-bus assembly from the basic network model."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .impedance import impedance_admittance, stamp_two_node
from .model import Network


def build_ybus(network: Network) -> NDArray[np.complex128]:
    """Build the nodal admittance matrix for all series-impedance branches.

    Ground is represented by terminal ID 0 and has no matrix row/column.
    Matrix ordering follows network.buses insertion order. Series branches and
    transformer positive-sequence impedances are included; shunts, tap ratios,
    mutual coupling and IEC peak corrections are not included.
    """
    n = len(network.buses)
    ybus = np.zeros((n, n), dtype=np.complex128)
    index = network.bus_index

    for branch in network.branches:
        y = impedance_admittance(branch.resistance, branch.reactance)
        upstream = 0 if branch.from_bus == 0 else index[branch.from_bus] + 1
        downstream = 0 if branch.to_bus == 0 else index[branch.to_bus] + 1
        stamp_two_node(ybus, upstream, downstream, y)

    for transformer in network.transformers:
        y = impedance_admittance(
            complex(transformer.positive_sequence_impedance).real,
            complex(transformer.positive_sequence_impedance).imag,
        )
        stamp_two_node(
            ybus,
            index[transformer.from_bus] + 1,
            index[transformer.to_bus] + 1,
            y,
        )

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

    for transformer in network.transformers:
        if sequence == "positive":
            impedance = transformer.positive_sequence_impedance
            mode = "through"
        elif sequence == "negative":
            impedance = transformer.negative_sequence_impedance
            mode = "through"
        else:
            mode = transformer.zero_sequence_mode
            impedance = transformer.zero_sequence_impedance
            from_eq = index[transformer.from_bus] + 1
            to_eq = index[transformer.to_bus] + 1

            if transformer.from_connection is not None:
                # Explicit winding connections take precedence over the legacy
                # zero_sequence_mode. This is a simplified sequence model:
                # winding/core construction and vector-group phase displacement
                # are not represented.
                from_conn = transformer.from_connection
                to_conn = transformer.to_connection
                if from_conn == "ungrounded_wye" or to_conn == "ungrounded_wye":
                    continue
                if from_conn == "delta" and to_conn == "delta":
                    continue
                if impedance is None:
                    raise ValueError(
                        f"Transformer {transformer.name or transformer.from_bus} "
                        "needs zero-sequence impedance for its winding connections"
                    )

                y = impedance_admittance(complex(impedance).real, complex(impedance).imag)
                if from_conn == "grounded_wye" and to_conn == "grounded_wye":
                    z_total = (
                        complex(impedance)
                        + 3 * complex(transformer.from_neutral_impedance)
                        + 3 * complex(transformer.to_neutral_impedance)
                    )
                    y_total = impedance_admittance(z_total.real, z_total.imag)
                    stamp_two_node(ybus, from_eq, to_eq, y_total)
                elif from_conn == "grounded_wye" and to_conn == "delta":
                    z_total = complex(impedance) + 3 * complex(transformer.from_neutral_impedance)
                    y_total = impedance_admittance(z_total.real, z_total.imag)
                    ybus[from_eq - 1, from_eq - 1] += y_total
                elif from_conn == "delta" and to_conn == "grounded_wye":
                    z_total = complex(impedance) + 3 * complex(transformer.to_neutral_impedance)
                    y_total = impedance_admittance(z_total.real, z_total.imag)
                    ybus[to_eq - 1, to_eq - 1] += y_total
                continue

            if mode == "blocked":
                continue
            if impedance is None:
                raise ValueError(
                    f"Transformer {transformer.name or transformer.from_bus} "
                    "has no zero-sequence impedance"
                )

        y = impedance_admittance(complex(impedance).real, complex(impedance).imag)
        from_eq = index[transformer.from_bus] + 1
        to_eq = index[transformer.to_bus] + 1
        if sequence == "zero" and mode == "grounded_wye_delta":
            # Legacy simplified mode: zero-sequence current returns through
            # the grounded neutral on the from side; no transfer to to_bus.
            ybus[from_eq - 1, from_eq - 1] += y
        else:
            stamp_two_node(ybus, from_eq, to_eq, y)

    return ybus

