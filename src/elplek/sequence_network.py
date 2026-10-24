"""Sequence-network Thevenin equivalents at a selected bus."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import Network
from .ybus import build_sequence_ybus


@dataclass(frozen=True, slots=True)
class SequenceThevenin:
    """Positive-sequence prefault voltage and sequence Thevenin impedances."""

    prefault_voltage: complex
    z1: complex
    z2: complex
    z0: complex


def _source_impedance(source, sequence: str) -> complex:
    if sequence == "positive":
        z = complex(source.impedance)
    elif sequence == "negative":
        z = source.negative_sequence_impedance
    else:
        z = source.zero_sequence_impedance
    if z is None:
        raise ValueError(
            f"Source {source.name or source.bus_id} has no {sequence}-sequence impedance"
        )
    z = complex(z)
    if z == 0:
        raise ValueError("Ideal zero-impedance sources are not supported in sequence equivalents")
    return z


def _equivalent(network: Network, bus_id: int, sequence: str) -> tuple[complex, complex]:
    if bus_id not in network.bus_index:
        raise ValueError(f"Unknown bus id: {bus_id}")
    if not network.sources:
        raise ValueError("Network must contain at least one source")
    y = build_sequence_ybus(network, sequence).copy()
    index = network.bus_index

    source_admittances: list[tuple[int, complex, complex]] = []
    for source in network.sources:
        z = _source_impedance(source, sequence)
        k = index[source.bus_id]
        ys = 1 / z
        y[k, k] += ys
        source_admittances.append((k, ys, complex(source.voltage) if sequence == "positive" else 0j))

    try:
        unit = np.zeros(len(network.buses), dtype=complex)
        unit[index[bus_id]] = 1
        zth = complex(np.linalg.solve(y, unit)[index[bus_id]])
        rhs = np.zeros(len(network.buses), dtype=complex)
        for k, ys, voltage in source_admittances:
            rhs[k] += ys * voltage
        vth = complex(np.linalg.solve(y, rhs)[index[bus_id]])
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"Singular {sequence}-sequence network") from exc
    return vth, zth


def calculate_sequence_thevenin(network: Network, bus_id: int) -> SequenceThevenin:
    """Derive sequence Thevenin impedances from branch/source sequence data.

    The positive-sequence prefault voltage is calculated with ideal source EMFs
    behind their impedances and no loads. This is a no-load approximation, not
    a full power-flow prefault state.
    """
    v1, z1 = _equivalent(network, bus_id, "positive")
    _, z2 = _equivalent(network, bus_id, "negative")
    _, z0 = _equivalent(network, bus_id, "zero")
    return SequenceThevenin(v1, z1, z2, z0)
