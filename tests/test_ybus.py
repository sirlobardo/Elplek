import numpy as np
import pytest

from elplek.model import Branch, Bus, Network
from elplek.ybus import build_sequence_ybus, build_ybus


def test_two_bus_network_builds_expected_ybus():
    network = Network()
    network.add_bus(Bus(10, "A"))
    network.add_bus(Bus(20, "B"))
    network.add_branch(Branch(10, 20, resistance=3.0, reactance=4.0))

    expected = np.array(
        [[0.12 - 0.16j, -0.12 + 0.16j],
         [-0.12 + 0.16j, 0.12 - 0.16j]],
        dtype=complex,
    )
    np.testing.assert_allclose(build_ybus(network), expected)


def test_branch_to_ground_stamps_only_bus_diagonal():
    network = Network()
    network.add_bus(Bus(7))
    network.add_branch(Branch(7, 0, resistance=2.0, reactance=0.0))

    np.testing.assert_allclose(build_ybus(network), np.array([[0.5 + 0j]]))


def test_bus_ids_map_by_insertion_order_not_numeric_value():
    network = Network()
    network.add_bus(Bus(20))
    network.add_bus(Bus(5))
    network.add_branch(Branch(20, 5, 1.0, 0.0))

    np.testing.assert_allclose(
        build_ybus(network),
        np.array([[1 + 0j, -1 + 0j], [-1 + 0j, 1 + 0j]]),
    )


def test_duplicate_bus_rejected():
    network = Network()
    network.add_bus(Bus(1))
    with pytest.raises(ValueError, match="Duplicate"):
        network.add_bus(Bus(1))


def test_unknown_branch_terminal_rejected():
    network = Network()
    network.add_bus(Bus(1))
    with pytest.raises(ValueError, match="unknown bus"):
        network.add_branch(Branch(1, 2, 1.0, 0.0))


def test_ground_to_ground_branch_rejected():
    with pytest.raises(ValueError, match="ground to ground"):
        Branch(0, 0, 1.0, 0.0)


def test_sequence_ybus_uses_branch_specific_negative_impedance():
    network = Network()
    network.add_bus(Bus(1))
    network.add_bus(Bus(2))
    network.add_branch(
        Branch(1, 2, 1.0, 0.0, negative_sequence_impedance=2 + 0j)
    )

    np.testing.assert_allclose(
        build_sequence_ybus(network, "negative"),
        np.array([[0.5 + 0j, -0.5 + 0j], [-0.5 + 0j, 0.5 + 0j]]),
    )


def test_sequence_ybus_requires_zero_sequence_data():
    network = Network()
    network.add_bus(Bus(1))
    network.add_bus(Bus(2))
    network.add_branch(Branch(1, 2, 1.0, 0.0))

    with pytest.raises(ValueError, match="zero-sequence impedance"):
        build_sequence_ybus(network, "zero")


def test_sequence_ybus_assembles_zero_sequence_and_grounded_branch():
    network = Network()
    network.add_bus(Bus(1))
    network.add_bus(Bus(2))
    network.add_branch(
        Branch(1, 2, 1.0, 0.0, zero_sequence_impedance=4 + 0j)
    )
    network.add_branch(
        Branch(2, 0, 1.0, 0.0, zero_sequence_impedance=2 + 0j)
    )

    np.testing.assert_allclose(
        build_sequence_ybus(network, "zero"),
        np.array([[0.25 + 0j, -0.25 + 0j], [-0.25 + 0j, 0.75 + 0j]]),
    )


def test_sequence_ybus_rejects_unknown_sequence():
    with pytest.raises(ValueError, match="sequence must"):
        build_sequence_ybus(Network(), "negative-sequence")
