"""Y-bus assembly from the basic network model."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .impedance import impedance_admittance, stamp_two_node
from .model import Network


def _clock_displacement_rad(clock: int) -> float:
    """Return positive-sequence to-side displacement from the IEC clock number.

    The from side is the reference. Clock 11 means to-side voltage leads by
    30 degrees; clock 1 means it lags by 30 degrees. Values 0 and 12 both
    represent zero displacement (0 is retained as the legacy default).
    """
    if clock in (0, 12):
        return 0.0
    return float(np.deg2rad((12 - clock) * 30.0))


def _stamp_with_phase_displacement(
    ybus: NDArray[np.complex128],
    from_eq: int,
    to_eq: int,
    admittance: complex,
    phase_displacement: float,
) -> None:
    """Stamp a unit-magnitude ideal phase-shifting transformer.

    phase_displacement is the angle of the to-side positive-sequence voltage
    relative to the from side. Sequence-network callers reverse its sign for
    negative sequence. The equations use a = exp(-j*phase_displacement):
    Yff = y, Yft = -y/conj(a), Ytf = -y/a, Ytt = y.
    """
    f = from_eq - 1
    t = to_eq - 1
    tap = np.exp(-1j * phase_displacement)
    ybus[f, f] += admittance
    ybus[f, t] -= admittance / np.conjugate(tap)
    ybus[t, f] -= admittance / tap
    ybus[t, t] += admittance


def build_ybus(network: Network) -> NDArray[np.complex128]:
    """Build the nodal admittance matrix for all series-impedance branches.

    Ground is represented by terminal ID 0 and has no matrix row/column.
    Matrix ordering follows network.buses insertion order. Series branches and
    transformer positive-sequence impedances and configured vector-group
    phase displacement are included; magnitude taps, shunts, mutual coupling
    and IEC peak corrections are not included.
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
        _stamp_with_phase_displacement(
            ybus,
            index[transformer.from_bus] + 1,
            index[transformer.to_bus] + 1,
            y,
            _clock_displacement_rad(transformer.vector_group_clock),
        )

    return ybus

def build_sequence_ybus(
    network: Network,
    sequence: str,
) -> NDArray[np.complex128]:
    """Build a sequence-specific Y-bus matrix.

    Positive and negative transformer networks use the vector-group phase
    displacement with opposite signs; zero-sequence phase displacement is
    zero and connection-dependent grounding rules are applied.
    Positive branches use R+jX. Negative branches fall back to positive
    impedance when omitted. Zero-sequence branch impedances are mandatory.
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
        elif sequence == "zero":
            # Clock displacement does not rotate zero-sequence quantities.
            stamp_two_node(ybus, from_eq, to_eq, y)
        else:
            phase = _clock_displacement_rad(transformer.vector_group_clock)
            if sequence == "negative":
                phase = -phase
            _stamp_with_phase_displacement(
                ybus, from_eq, to_eq, y, phase
            )

    return ybus

