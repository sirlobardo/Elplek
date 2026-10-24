import numpy as np
import pytest

from elplek.model import Branch, Bus, Network, Source
from elplek.short_circuit import solve_short_circuit


def test_single_bus_fault_current_equals_source_voltage_over_impedance():
    network = Network()
    network.add_bus(Bus(10, "Fault bus"))
    network.add_source(Source(10, 100 + 20j, 0.4 + 1.2j, "grid"))

    result = solve_short_circuit(network, 10)
    np.testing.assert_allclose(result.fault_current, (100 + 20j) / (0.4 + 1.2j))
    np.testing.assert_allclose(result.bus_voltages[10], 0j)
    np.testing.assert_allclose(result.source_currents["grid"], result.fault_current)


def test_two_bus_fault_includes_line_impedance():
    network = Network()
    network.add_bus(Bus(10, "Source"))
    network.add_bus(Bus(20, "Fault"))
    network.add_branch(Branch(10, 20, 0.3, 0.4))
    network.add_source(Source(10, 120 + 0j, 0.2 + 0.6j, "utility"))

    result = solve_short_circuit(network, 20)
    expected = 120 / ((0.2 + 0.6j) + (0.3 + 0.4j))
    np.testing.assert_allclose(result.fault_current, expected)
    np.testing.assert_allclose(result.bus_voltages[20], 0j)
    np.testing.assert_allclose(result.source_currents["utility"], expected)


def test_source_on_unknown_bus_rejected():
    network = Network()
    network.add_bus(Bus(1))
    with pytest.raises(ValueError, match="unknown bus"):
        network.add_source(Source(2, 100, 1j))


def test_short_circuit_without_source_rejected():
    network = Network()
    network.add_bus(Bus(1))
    with pytest.raises(ValueError, match="at least one source"):
        solve_short_circuit(network, 1)

def test_parallel_sources_contribute_to_fault_current():
    network = Network()
    network.add_bus(Bus(1, "Fault bus"))
    network.add_source(Source(1, 100 + 0j, 1 + 0j, "source_a"))
    network.add_source(Source(1, 100 + 0j, 1 + 0j, "source_b"))

    result = solve_short_circuit(network, 1)

    np.testing.assert_allclose(result.fault_current, 200 + 0j)
    np.testing.assert_allclose(result.source_currents["source_a"], 100 + 0j)
    np.testing.assert_allclose(result.source_currents["source_b"], 100 + 0j)


def test_parallel_sources_with_different_impedances_match_thevenin_sum():
    network = Network()
    network.add_bus(Bus(1, "Fault bus"))
    network.add_source(Source(1, 100 + 0j, 1 + 1j, "source_a"))
    network.add_source(Source(1, 80 + 0j, 2 + 0j, "source_b"))

    result = solve_short_circuit(network, 1)
    expected_a = (100 + 0j) / (1 + 1j)
    expected_b = (80 + 0j) / 2

    np.testing.assert_allclose(result.source_currents["source_a"], expected_a)
    np.testing.assert_allclose(result.source_currents["source_b"], expected_b)
    np.testing.assert_allclose(result.fault_current, expected_a + expected_b)

