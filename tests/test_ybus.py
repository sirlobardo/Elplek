import numpy as np
import pytest

from elplek.model import Branch, Bus, Network
from elplek.ybus import build_ybus


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
