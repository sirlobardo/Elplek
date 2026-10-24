import numpy as np
import pytest

from elplek.model import Branch, Bus, Network, Source
from elplek.sequence_network import calculate_sequence_thevenin


def test_sequence_thevenin_single_bus_source():
    network = Network()
    network.add_bus(Bus(1))
    network.add_source(Source(
        1, 120 + 0j, 1 + 1j, "grid",
        negative_sequence_impedance=2 + 1j,
        zero_sequence_impedance=3 + 1j,
    ))
    result = calculate_sequence_thevenin(network, 1)
    np.testing.assert_allclose(result.prefault_voltage, 120)
    np.testing.assert_allclose(result.z1, 1 + 1j)
    np.testing.assert_allclose(result.z2, 2 + 1j)
    np.testing.assert_allclose(result.z0, 3 + 1j)


def test_sequence_thevenin_includes_branch_impedance():
    network = Network()
    network.add_bus(Bus(1))
    network.add_bus(Bus(2))
    network.add_branch(Branch(
        1, 2, 0.5, 0.5,
        negative_sequence_impedance=0.7 + 0.4j,
        zero_sequence_impedance=1 + 0.5j,
    ))
    network.add_source(Source(
        1, 120, 0.2 + 0.2j, "grid",
        negative_sequence_impedance=0.3 + 0.3j,
        zero_sequence_impedance=0.4 + 0.4j,
    ))
    result = calculate_sequence_thevenin(network, 2)
    np.testing.assert_allclose(result.prefault_voltage, 120)
    np.testing.assert_allclose(result.z1, 0.7 + 0.7j)
    np.testing.assert_allclose(result.z2, 1.0 + 0.7j)
    np.testing.assert_allclose(result.z0, 1.4 + 0.9j)


def test_sequence_thevenin_requires_zero_sequence_source_data():
    network = Network()
    network.add_bus(Bus(1))
    network.add_source(Source(1, 120, 1j, "grid"))
    with pytest.raises(ValueError, match="zero-sequence impedance"):
        calculate_sequence_thevenin(network, 1)
