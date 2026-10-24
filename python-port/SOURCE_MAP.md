# Original Elplek source map

This map was prepared by inspecting the uploaded `elpleksource.zip` and the original Delphi units. It is a planning aid, not a claim that every dependency has been exhaustively traced.

## Application entry point and UI

- `Imagopro.dpr`: Delphi application entry point; registers forms and units.
- `Imagopas.pas`: main application form and orchestration. It imports the load-flow, short-circuit, IEC, node, component and diagram units.
- `Imagopas.dfm` and the other `.dfm` files: Delphi VCL form resources.
- `Drawcomp.pas`, `Skemadef.pas`, `Skemproc.pas`, `Nodes.pas`: diagram/component model, interactions and connectivity logic. These are tightly coupled to UI objects and global component state.

## Numerical calculation areas

- `LoadFlow.pas`: load-flow entry point `LoadFlowCalculation` and class `TLoadFlow`; the source imports `Nodes`, `Elplex`, `Compdef`, `Skemproc`, `GenVolt`, `Cmatmul` and `Matmul`.
- `IEC.pas`: IEC 60909 short-circuit entry points `IECShort`, `IECTwoPhase`, `IECEarthFault`, and `IECLineLineEarth`; depends on node topology, component data and multiple fault-analysis units.
- `Shortcir.pas`: dynamic/superposition short-circuit calculations, generator/motor models and relay/current-transformer calculations; very large and strongly coupled.
- `TWOSHORT.PAS`: phase-to-phase faults and symmetrical-component conversions. Exposes `PhaseToPhaseShort`, `PhaseToSeq`/related sequence transformations and fault-current routines.
- `earthflt.pas`: earth-fault calculations.
- `AllShort.pas`: orchestration/UI for calculations across buses and measurement points; not a good first numerical module to port.
- `GenProc.pas`: synchronous-machine parameter and equation helpers; imports `Shortcir`, so it is not yet a clean standalone numerical library.
- `Elplex.pas`, `Matmul.pas`, `Cmatmul.pas`, `Utildef.pas`, `Imagodef.pas`, `Compdef.pas`: shared types, complex/matrix utilities, component definitions and global application data. These dependencies need tracing before translating algorithms.

## Recommended migration order

1. **Keep this scaffold separate from the Delphi program.** Do not overwrite or rename original files.
2. **Inventory core types and units:** identify complex-number representation, matrix indexing, node numbering, component kinds, sign conventions, units and global state in `Utildef`, `Imagodef`, `Compdef`, `Elplex`, `Matmul` and `Cmatmul`.
3. **Build reference fixtures:** small networks with known values and matching outputs from the original executable. Record voltages, currents, fault type, source parameters and calculation mode.
4. **Port a narrow calculation path:** start with the smallest independent matrix/impedance routine, then expand toward load flow and IEC 60909.
5. **Implement SLD import only after documenting the binary/text format** and making sample files available as tests.
6. **Rebuild the GUI last** with a separate diagram model and PySide6/Qt Graphics View or another graph-editor framework.

## Important engineering distinction

The current `solver.py` is only a linear Y-bus voltage solver with one fixed slack voltage and constant-admittance shunts. It is **not** a Newton-Raphson load-flow solver and does not model constant-power loads, generator limits, transformer tap control, sequence networks, IEC 60909 corrections or protection relays. Its tests have been added but have not been executed in this environment. Numerical equivalence must be established against reference cases before use.

## License and attribution

The repository README names Ilkka Leikkonen as the original author and asks derivative users to credit the original source. Keep that attribution. Check the repository's LICENSE and third-party component licenses before publishing a derivative.
