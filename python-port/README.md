# Elplek Python Port

This directory starts a clean Python implementation alongside the original Delphi source. It does not yet reproduce all Elplek features or claim numerical equivalence with v0.995.

## Roadmap
1. Build an independently testable electrical network model and solver.
2. Add reference cases and compare results with original Elplek.
3. Port short-circuit and IEC 60909 calculations into isolated modules.
4. Rebuild the single-line-diagram editor after the numerical core is stable.
5. Reverse-engineer and test the SLD file format before implementing import.

## Setup
Python 3.11+ is recommended.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"
    pytest

## Current scope
- AC bus/branch model using complex impedances.
- One fixed-voltage slack bus and constant-admittance shunts.
- Y-bus construction and solution for non-slack bus voltages.
- Basic tests for analytically checkable networks.

## Limitations
This is a foundation, not a completed port. It does not yet implement Elplek load-flow controls, dynamic machine models, IEC 60909 corrections, asymmetrical faults, protection relays, transformer connection groups, GUI, or SLD compatibility. Do not use it for engineering decisions until validated against reference cases.

## Attribution
The parent repository identifies Ilkka Leikkonen as the original author. Preserve original attribution and verify the applicable license and third-party component terms before redistribution.
