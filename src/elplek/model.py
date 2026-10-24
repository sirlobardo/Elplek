"""Basic network data structures for the incremental Elplek port."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Bus:
    """Electrical bus. IDs are positive integers; ground is represented by 0."""

    id: int
    name: str = ""

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("Bus id must be positive; use 0 only for ground terminals")


@dataclass(frozen=True, slots=True)
class Branch:
    """Series impedance between two buses (or one bus and ground)."""

    from_bus: int
    to_bus: int
    resistance: float
    reactance: float
    name: str = ""

    def __post_init__(self) -> None:
        if self.from_bus < 0 or self.to_bus < 0:
            raise ValueError("Branch terminal IDs cannot be negative")
        if self.from_bus == 0 and self.to_bus == 0:
            raise ValueError("A branch cannot connect ground to ground")


@dataclass(slots=True)
class Network:
    """Network with bus IDs independent of matrix row ordering."""

    buses: list[Bus] = field(default_factory=list)
    branches: list[Branch] = field(default_factory=list)

    def add_bus(self, bus: Bus) -> None:
        if any(existing.id == bus.id for existing in self.buses):
            raise ValueError(f"Duplicate bus id: {bus.id}")
        self.buses.append(bus)

    def add_branch(self, branch: Branch) -> None:
        known_ids = {bus.id for bus in self.buses}
        for terminal in (branch.from_bus, branch.to_bus):
            if terminal != 0 and terminal not in known_ids:
                raise ValueError(f"Branch references unknown bus id: {terminal}")
        self.branches.append(branch)

    @property
    def bus_index(self) -> dict[int, int]:
        """Map bus IDs to zero-based Y-bus matrix indices."""
        return {bus.id: index for index, bus in enumerate(self.buses)}
