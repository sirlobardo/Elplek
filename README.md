# Elplek
Saved copy of Elplek v. 0.995  (short circuit and load flow, freeware).

This is not an official repository of the program and this account is not affiliated with the original author of Elplek software. The goal of this repository is to preserve a unique freeware program to download and for possible further development of the program as the source code was available to download on the official site after the author had finished its development. If you use any parts of Elplek source code please provide links to the original author:  Ilkka Leikkonen, Kokkola, Finland.

This program is written in Delphi 2 and with minor editions can be compiled in Delphi 3. If you have any ideas how to upgrade the source code to Lazarus or Delphi of recent versions, feel free to share your suggestions here.

Read the preserved original description of the program in the Wiki: https://github.com/Sibiriak/Elplek/wiki



Сохраненная копия бесплатной программы Elplek версии 0.995 для расчета токов короткого замыкания и перетоков мощности.

Это не официальный репозиторий программы и этот аккаунт никак не связан с её оригинальными авторами. Цель репозитория - сохранить уникальную  бесплатную программу для скачивания и возможного дальнейшего развития, т.к. исходный код программы был опубликован автором на официальном сайте, после того как развитие проекта прекратилось. Если Вы используете любые части исходного кода Elplek, пожалуйста, указывайте её автора: Ilkka Leikkonen, Kokkola, Finland.

Программа написана на Delphi 2 и с минимальными изменениями может быть скомпилирована в Delphi 3й версии. Если у Вас есть идеи как усовершенствовать исходный код для компиляции в Lazarus или в Delphi более свежих версии, пишите Ваши предложения.

Перевод оригинального описания программы можно прочесть здесь: https://github.com/Sibiriak/Elplek/wiki/%D0%9E%D0%BF%D0%B8%D1%81%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D1%8B-%D0%BD%D0%B0-%D1%80%D1%83%D1%81%D1%81%D0%BA%D0%BE%D0%BC



## Incremental Python port (`python-port`)

The Python implementation is an incremental port and is not yet a drop-in
replacement for the original Delphi program. Current transformer models support
positive-, negative- and simplified zero-sequence equivalents, winding
connection labels, neutral impedances, and an optional vector-group clock
number.

Example:

```python
from elplek.model import Network, Bus, Shunt, Transformer
from elplek.ybus import build_ybus, build_sequence_ybus

network = Network()
network.add_bus(Bus(1, "HV"))
network.add_bus(Bus(2, "LV"))
network.add_transformer(Transformer(
    from_bus=1,
    to_bus=2,
    positive_sequence_impedance=0.01 + 0.08j,
    negative_sequence_impedance=0.01 + 0.08j,
    zero_sequence_impedance=0.02 + 0.10j,
    from_connection="grounded_wye",
    to_connection="delta",
    vector_group_clock=11,
    tap_ratio=1.05,  # ideal magnitude ratio on the from_bus side
))
network.add_shunt(Shunt(
    bus_id=2,
    admittance=0.0 + 0.04j,
    negative_sequence_admittance=0.0 + 0.04j,
    zero_sequence_admittance=0.0 + 0.0j,
    name="LV capacitor bank",
))
y_positive = build_ybus(network)
y_negative = build_sequence_ybus(network, "negative")
y_zero = build_sequence_ybus(network, "zero")
```

The clock number describes the phase displacement of the `to_bus` winding
relative to `from_bus`: clock 11 means the to-side positive-sequence voltage
leads by 30 degrees; clock 1 means it lags by 30 degrees. Clock 0 is the legacy
no-shift default, while clock 12 is the explicit zero-displacement clock
position. Negative-sequence phase displacement is reversed. Zero-sequence
network behavior depends on the configured winding connections and neutral
impedances; its simplified model does not encode all transformer core designs.

Tap magnitude ratios are supported as ideal complex taps on the from_bus side.
Their positive- and negative-sequence Y-bus stamps are included; zero-sequence
tap treatment follows the simplified connection model. Magnetizing branches,
complete vector-group/terminal conventions, full transformer grounding details,
load-flow equivalence, and complete IEC 60909 corrections remain outside the
current implementation.
The port is still under validation and should not yet be used as a certified
replacement for the original program or an independently validated
short-circuit study package.


### Bus shunts

The `Shunt` model stamps a complex admittance directly onto the selected
bus diagonal. Use admittance values in the same per-unit or physical-unit
system as the rest of the network. Positive-sequence admittance is required;
negative-sequence admittance defaults to positive sequence if omitted. For
zero-sequence assembly, provide `zero_sequence_admittance` explicitly rather
than assuming that the positive-sequence value is valid. Shunts are included
in both the conventional `build_ybus` and `build_sequence_ybus` matrices.


### Conventional short-circuit solver

`solve_short_circuit(network, fault_bus_id, fault_impedance=...)` uses the
conventional Y-bus with source equivalents and a single fault-current unknown.
Consequently, transformer positive-sequence impedance, ideal magnitude taps,
configured clock displacement, and bus shunts affect its result. This API
remains a single-phase-equivalent solver; use `solve_network_fault` for the
separate, simplified symmetrical-component fault path. Neither API is yet a
certified implementation of IEC 60909.
