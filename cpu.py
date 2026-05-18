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
                f"Register {self._name} Error: Value {new_value} is out of bounds ({self._min_value}..{self._max_value})."
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
    Implements the LMC instruction set with proper fetch-decode-execute cycle.
    """
    def __init__(self, memory_bus: MemoryInterface):
        # Composition: Processor is composed of individual Register components
        self._acc = Register(name="ACC", min_value=0, max_value=999, display_width=3)  # Accumulator
        self._pc = Register(name="PC", min_value=0, max_value=99, display_width=2)     # Program Counter
        self._ir = Register(name="IR", min_value=0, max_value=999, display_width=3)    # Instruction Register
        self._memory_bus = memory_bus
        self._halted = False
        self._input_buffer = []
        self._output_buffer = []
        # Decoded instruction placeholders for micro-step execution
        self._decoded_opcode = None
        self._decoded_operand = None

    @property
    def acc(self) -> Register:
        return self._acc

    @property
    def pc(self) -> Register:
        return self._pc

    @property
    def ir(self) -> Register:
        return self._ir

    @property
    def halted(self) -> bool:
        return self._halted

    @property
    def output_buffer(self) -> list:
        return self._output_buffer

    def set_input(self, value: int) -> None:
        """Sets input value for INP instruction."""
        if not (0 <= value <= 999):
            raise ValueError(f"Input value {value} must be 0-999")
        self._input_buffer.append(value)

    def increment_pc(self) -> None:
        """Increments the PC, ensuring it wraps around within the LMC 100-cell space."""
        self._pc.value = (self._pc.value + 1) % 100

    def _signed_acc(self) -> int:
        """Return accumulator interpreted as signed value (-500..+499).

        Values 0..499 -> 0..499 (non-negative)
        Values 500..999 -> -500..-1 (negative)
        This helps branch instructions (BRP) decide sign correctly when arithmetic wraps around modulo 1000.
        """
        v = self._acc.value
        return v if v < 500 else v - 1000

    def reset(self) -> None:
        """Resets all internal registers."""
        self._acc.reset()
        self._pc.reset()
        self._ir.reset()
        self._halted = False
        self._output_buffer.clear()

    def fetch(self) -> None:
        """Fetches the next instruction from memory into the IR and increments the PC."""
        if self._halted:
            return
        current_address = self._pc.value
        self._ir.value = self._memory_bus.read(current_address)
        self.increment_pc()

    def decode(self) -> None:
        """Decode the instruction currently in IR and store decoded fields for later execution.

        This method does not execute the instruction; it only determines opcode and operand
        and stores them in internal placeholders for execute_decoded().
        """
        if self._halted:
            return
        opcode = self._ir.value // 100
        operand = self._ir.value % 100
        self._decoded_opcode = opcode
        self._decoded_operand = operand

    def execute_decoded(self) -> None:
        """Execute the previously decoded instruction.

        Requires that decode() was called before. After execution the decoded fields
        are cleared.
        """
        if self._halted:
            return
        if self._decoded_opcode is None:
            raise RuntimeError("No decoded instruction to execute. Call decode() first.")

        opcode = self._decoded_opcode
        operand = self._decoded_operand

        # Clear decoded placeholders (single-shot execution)
        self._decoded_opcode = None
        self._decoded_operand = None

        # Execute based on opcode
        if opcode == 0:
            self._execute_hlt()
        elif opcode == 1:
            self._execute_add(operand)
        elif opcode == 2:
            self._execute_sub(operand)
        elif opcode == 3:
            self._execute_sta(operand)
        elif opcode == 5:
            self._execute_lda(operand)
        elif opcode == 6:
            self._execute_bra(operand)
        elif opcode == 7:
            self._execute_brz(operand)
        elif opcode == 8:
            self._execute_brp(operand)
        elif opcode == 9:
            if operand == 1:
                self._execute_inp()
            elif operand == 2:
                self._execute_out()
            else:
                raise ValueError(f"Unknown instruction code: {opcode}{operand:02d}")
        else:
            raise ValueError(f"Unknown opcode: {opcode}")

    def decode_and_execute(self) -> None:
        """Backward-compatible convenience that decodes then executes immediately."""
        self.decode()
        self.execute_decoded()

    def get_decoded(self):
        """Return the last decoded (opcode, operand) or None if nothing decoded."""
        if self._decoded_opcode is None:
            return None
        return (self._decoded_opcode, self._decoded_operand)

    def execute_cycle(self) -> bool:
        """
        Executes one complete fetch-decode-execute cycle.
        Returns True if CPU is still running, False if halted.
        """
        if self._halted:
            return False
        
        try:
            self.fetch()
            self.decode_and_execute()
            return not self._halted
        except Exception as e:
            print(f"Execution error: {e}")
            self._halted = True
            return False

    # ========================================================================
    # LMC Instruction Implementations
    # ========================================================================

    def _execute_hlt(self) -> None:
        """HLT (000): Halt the computer."""
        self._halted = True

    def _execute_add(self, address: int) -> None:
        """ADD (1xx): Add value at address to ACC."""
        value = self._memory_bus.read(address)
        self._acc.value = (self._acc.value + value) % 1000

    def _execute_sub(self, address: int) -> None:
        """SUB (2xx): Subtract value at address from ACC."""
        value = self._memory_bus.read(address)
        self._acc.value = (self._acc.value - value) % 1000

    def _execute_sta(self, address: int) -> None:
        """STA (3xx): Store ACC value at address."""
        self._memory_bus.write(address, self._acc.value)

    def _execute_lda(self, address: int) -> None:
        """LDA (5xx): Load value from address into ACC."""
        self._acc.value = self._memory_bus.read(address)

    def _execute_bra(self, address: int) -> None:
        """BRA (6xx): Branch unconditionally to address."""
        self._pc.value = address

    def _execute_brz(self, address: int) -> None:
        """BRZ (7xx): Branch to address if ACC is zero."""
        if self._acc.value == 0:
            self._pc.value = address

    def _execute_brp(self, address: int) -> None:
        """BRP (8xx): Branch to address if ACC is positive (>= 0).

        Uses signed interpretation of the accumulator to decide positivity when
        arithmetic wraps modulo 1000.
        """
        if self._signed_acc() >= 0:
            self._pc.value = address

    def _execute_inp(self) -> None:
        """INP (901): Read input and store in ACC."""
        if not self._input_buffer:
            raise RuntimeError("INP: No input available")
        value = self._input_buffer.pop(0)
        self._acc.value = value

    def _execute_out(self) -> None:
        """OUT (902): Output ACC value."""
        self._output_buffer.append(self._acc.value)

    def display_status(self) -> None:
        """Prints the CPU's current execution status."""
        print(f"[CPU State] ACC: {self._acc} | PC: {self._pc} | IR: {self._ir} | Halted: {self._halted}")


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