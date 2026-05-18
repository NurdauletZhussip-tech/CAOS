import pytest
from cpu import Processor, LmcMemoryAdapter


def test_add_store():
    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)
    # Clear memory
    for i in range(100):
        mem.write(i, 0)

    # Program: LDA 8 (508), ADD 9 (109), STA 10 (310), HLT (000)
    mem.write(0, 508)
    mem.write(1, 109)
    mem.write(2, 310)
    mem.write(3, 0)

    # Data
    mem.write(8, 5)
    mem.write(9, 3)

    # Run
    steps = 0
    while not cpu.halted and steps < 20:
        cpu.execute_cycle()
        steps += 1

    assert mem.read(10) == 8
    assert cpu.acc.value == 8


def test_inp_out():
    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)
    for i in range(100):
        mem.write(i, 0)

    # Program: INP (901), OUT (902), HLT (000)
    mem.write(0, 901)
    mem.write(1, 902)
    mem.write(2, 0)

    cpu.set_input(123)
    cpu.execute_cycle()  # INP
    cpu.execute_cycle()  # OUT

    assert cpu.output_buffer == [123]
