from cpu import Processor, LmcMemoryAdapter


def run_sample():
    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)

    # Clear memory
    for i in range(100):
        mem.write(i, 0)

    # Sample program: LOAD 8 (508), ADD 9 (109), STORE 10 (310), HLT (000)
    mem.write(0, 508)
    mem.write(1, 109)
    mem.write(2, 310)
    mem.write(3, 0)

    # Data
    mem.write(8, 5)
    mem.write(9, 3)
    mem.write(10, 0)

    # Run until halt
    steps = 0
    print("Starting program execution...")
    while not cpu.halted and steps < 1000:
        running = cpu.execute_cycle()
        steps += 1

    print(f"Finished after {steps} steps. HALT reached: {not running}")
    print(f"ACC: {cpu.acc.value:03d}, PC: {cpu.pc.value:02d}, IR: {cpu.ir.value:03d}")
    print("Memory[10] (result):", mem.read(10))
    if cpu.output_buffer:
        print("Output buffer:", cpu.output_buffer)


if __name__ == '__main__':
    run_sample()
