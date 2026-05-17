from abc import ABC, abstractmethod
import memory  # Importing your provided memory module

class MemoryInterface(ABC):
    """
    Dependency Inversion Principle (DIP) & Interface Segregation Principle (ISP):
    An abstract interface defining memory operations. The Processor will depend
    on this abstraction rather than the concrete global functions in memory.py.
    """
    @abstractmethod
    def read(self, address: int) -> int:
        pass

    @abstractmethod
    def write(self, address: int, value: int) -> None:
        pass


class LmcMemoryAdapter(MemoryInterface):
    """
    Structural Adapter Pattern:
    Bridges your existing procedural memory.py module with the
    object-oriented MemoryInterface abstraction.
    """
    def read(self, address: int) -> int:
        return memory.mem_read(address)

    def write(self, address: int, value: int) -> None:
        memory.mem_write(address, value)


class Register:
    """
    Single Responsibility Principle (SRP):
    Encapsulates a single hardware register's value, boundary validation, and formatting.
    """
    def __init__(self, name: str, min_value: int, max_value: int, display_width: int):
        self._name = name
        self._min_value = min_value
        self._max_value = max_value
        self._display_width = display_width
        self._value = 0

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_value: int):
        if not (self._min_value <= new_value <= self._max_value):
            raise ValueError(
                f"Register {self._name} Error: Value {new_value} is out of bounds "
                f"(${self._min_value} \\le \\text{{value}} \\le {self._max_value}$)."
            )
        self._value = new_value

    def reset(self) -> None:
        """Resets the register to its default zero state."""
        self._value = 0

    def __str__(self) -> str:
        """Provides uniform zero-padded string representation."""
        return f"{self._value:0{self._display_width}}"


class Processor:
    """
    Single Responsibility Principle (SRP) & Open/Closed Principle (OCP):
    Manages the architectural state (registers) and orchestrates CPU cycles.
    """
    def __init__(self, memory_bus: MemoryInterface):
        # Composition: Processor is composed of individual Register components
        self._acc = Register(name="ACC", min_value=0, max_value=999, display_width=3)  # Accumulator
        self._pc = Register(name="PC", min_value=0, max_value=99, display_width=2)     # Program Counter
        self._ir = Register(name="IR", min_value=0, max_value=999, display_width=3)    # Instruction Register
        self._memory_bus = memory_bus

    @property
    def acc(self) -> Register:
        return self._acc

    @property
    def pc(self) -> Register:
        return self._pc

    @property
    def ir(self) -> Register:
        return self._ir

    def increment_pc(self) -> None:
        """Increments the PC, ensuring it wraps around within the LMC 100-cell space."""
        self._pc.value = (self._pc.value + 1) % 100

    def reset(self) -> None:
        """Resets all internal registers."""
        self._acc.reset()
        self._pc.reset()
        self._ir.reset()

    def fetch(self) -> None:
        """Fetches the next instruction from memory into the IR and increments the PC."""
        current_address = self._pc.value
        self._ir.value = self._memory_bus.read(current_address)
        self.increment_pc()

    def display_status(self) -> None:
        """Prints the CPU's current execution status."""
        print(f"[CPU State] ACC: {self._acc} | PC: {self._pc} | IR: {self._ir}")


# Example Usage Breakdown
if __name__ == "__main__":
    # 1. Instantiate the memory layer via the adapter
    lmc_memory = LmcMemoryAdapter()

    # 2. Inject memory dependency into the Processor (DIP)
    cpu = Processor(memory_bus=lmc_memory)

    # 3. Simulate placing an instruction in memory (e.g., Load value from address 05 -> '505')
    lmc_memory.write(address=0, value=505)

    print("--- Initial CPU State ---")
    cpu.display_status()

    print("\n--- Executing Fetch Cycle ---")
    cpu.fetch()

    print("\n--- Post-Fetch CPU State ---")
    cpu.display_status()