# LMC Memory: 100 cells, each stores values 000–999
memory = [0] * 100

def validate_value(value):
    """Ensure value is within LMC range 0–999."""
    if not (0 <= value <= 999):
        raise ValueError(f"Value {value} out of range (0–999)")

def mem_write(address, value):
    """Write a value to a memory cell."""
    if not (0 <= address <= 99):
        raise IndexError(f"Address {address} out of range (0–99)")
    validate_value(value)
    memory[address] = value

def mem_read(address):
    """Read a value from a memory cell."""
    if not (0 <= address <= 99):
        raise IndexError(f"Address {address} out of range (0–99)")
    return memory[address]

def mem_display():
    """Print memory in a readable 10x10 grid."""
    print("     " + "  ".join(f"{i:2}" for i in range(10)))
    print("    " + "----" * 10)
    for row in range(10):
        values = [f"{memory[row * 10 + col]:03}" for col in range(10)]
        print(f"{row * 10:3} | {' '.join(values)}")