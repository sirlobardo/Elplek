"""Sequence-network fault calculations for a single equivalent source.

These analytical helpers are independent of the bus-network solver. Voltages
and impedances are phase-domain sequence equivalents in consistent units.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FaultType = Literal["three_phase", "line_to_line", "single_line_to_ground", "double_line_to_ground"]


@dataclass(frozen=True, slots=True)
class SequenceFaultResult:
    """Sequence currents and a representative fault current.

    For line-to-line faults, fault_current is phase-b current (phase-c current
    is its negative). For ground faults, it is total ground current. For
    three-phase faults, it is phase-a current.
    """

    positive_current: complex
    negative_current: complex
    zero_current: complex
    fault_current: complex


def solve_sequence_fault(
    fault_type: FaultType,
    *,
    phase_voltage: complex,
    z1: complex,
    z2: complex,
    z0: complex = 0j,
    fault_impedance: complex = 0j,
) -> SequenceFaultResult:
    """Calculate standard sequence-network currents for common fault types.

    phase_voltage is the prefault phase-to-neutral Thevenin voltage. z1, z2
    and z0 are positive-, negative- and zero-sequence Thevenin impedances at
    the fault location. For ground faults, fault impedance is phase-to-ground
    and appears as 3*Zf in the sequence network. This does not assemble
    sequence networks from bus-level network data.
    """
    z1, z2, z0, zf = map(complex, (z1, z2, z0, fault_impedance))
    voltage = complex(phase_voltage)

    if fault_type == "three_phase":
        i1 = voltage / (z1 + zf)
        return SequenceFaultResult(i1, 0j, 0j, i1)

    if fault_type == "single_line_to_ground":
        i0 = voltage / (z1 + z2 + z0 + 3 * zf)
        return SequenceFaultResult(i0, i0, i0, 3 * i0)

    if fault_type == "line_to_line":
        i1 = voltage / (z1 + z2 + zf)
        i2 = -i1
        ib = complex(0, -(3**0.5)) * i1
        return SequenceFaultResult(i1, i2, 0j, ib)

    if fault_type == "double_line_to_ground":
        z0f = z0 + 3 * zf
        parallel_denominator = z2 + z0f
        if parallel_denominator == 0:
            raise ZeroDivisionError("Negative- and zero-sequence parallel impedance is zero")
        parallel = z2 * z0f / parallel_denominator
        i1 = voltage / (z1 + parallel)
        i2 = -i1 * z0f / parallel_denominator
        i0 = -i1 * z2 / parallel_denominator
        return SequenceFaultResult(i1, i2, i0, 3 * i0)

    raise ValueError(f"Unsupported fault type: {fault_type!r}")
