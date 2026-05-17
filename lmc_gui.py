import tkinter as tk
from tkinter import ttk, messagebox
from cpu import Processor, LmcMemoryAdapter

class LmcGui:
    def __init__(self, root):
        self.root = root
        root.title("Little Man Computer Simulator")
        root.resizable(False, False)

        # --- Core components ---
        self.memory_adapter = LmcMemoryAdapter()
        self.cpu = Processor(memory_bus=self.memory_adapter)
        self.halted = False

        # --- Build UI ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Register display area
        reg_frame = ttk.LabelFrame(main_frame, text="Registers", padding="5")
        reg_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.acc_label = ttk.Label(reg_frame, text="ACC: 000", font=("Courier", 14, "bold"))
        self.acc_label.grid(row=0, column=0, padx=20)
        self.pc_label = ttk.Label(reg_frame, text="PC: 00", font=("Courier", 14, "bold"))
        self.pc_label.grid(row=0, column=1, padx=20)
        self.ir_label = ttk.Label(reg_frame, text="IR: 000", font=("Courier", 14, "bold"))
        self.ir_label.grid(row=0, column=2, padx=20)

        # Memory table (10x10 grid)
        mem_frame = ttk.LabelFrame(main_frame, text="Memory (0–99)", padding="5")
        mem_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self.mem_cells = []  # 2D list of Label widgets
        for row in range(10):
            row_labels = []
            for col in range(10):
                lbl = tk.Label(mem_frame, text="000", width=4, relief=tk.RIDGE,
                               font=("Courier", 10), anchor=tk.CENTER)
                lbl.grid(row=row, column=col, padx=1, pady=1)
                row_labels.append(lbl)
            self.mem_cells.append(row_labels)

        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

        self.step_btn = ttk.Button(btn_frame, text="Step (Fetch+Execute)", command=self.step)
        self.step_btn.grid(row=0, column=0, padx=5)

        self.reset_btn = ttk.Button(btn_frame, text="Reset CPU", command=self.reset_cpu)
        self.reset_btn.grid(row=0, column=1, padx=5)

        self.load_btn = ttk.Button(btn_frame, text="Load Sample Program", command=self.load_sample)
        self.load_btn.grid(row=0, column=2, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Press Step to execute instructions.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # Initial refresh
        self.refresh_display()

    # --------------------------------------------------------------------------
    # Display updates
    # --------------------------------------------------------------------------
    def refresh_display(self):
        """Update memory grid and register labels from current state."""
        # Update memory table
        for addr in range(100):
            row = addr // 10
            col = addr % 10
            value = self.memory_adapter.read(addr)
            self.mem_cells[row][col].config(text=f"{value:03d}")

        # Update register labels
        self.acc_label.config(text=f"ACC: {self.cpu.acc.value:03d}")
        self.pc_label.config(text=f"PC: {self.cpu.pc.value:02d}")
        self.ir_label.config(text=f"IR: {self.cpu.ir.value:03d}")

    # --------------------------------------------------------------------------
    # LMC Instruction Execution (called after fetch)
    # --------------------------------------------------------------------------
    def execute_instruction(self):
        """Decode and execute the instruction currently in IR."""
        opcode = self.cpu.ir.value // 100        # first digit
        operand = self.cpu.ir.value % 100        # last two digits (address)

        # Branch helpers
        def branch_to(addr):
            self.cpu.pc.value = addr

        if opcode == 0:          # HALT
            self.halted = True
            self.status_var.set("HALT encountered – execution stopped.")
            return

        elif opcode == 1:        # ADD
            val = self.memory_adapter.read(operand)
            new_acc = (self.cpu.acc.value + val) % 1000
            self.cpu.acc.value = new_acc

        elif opcode == 2:        # SUB
            val = self.memory_adapter.read(operand)
            new_acc = (self.cpu.acc.value - val) % 1000
            self.cpu.acc.value = new_acc

        elif opcode == 3:        # STORE
            self.memory_adapter.write(operand, self.cpu.acc.value)

        elif opcode == 5:        # LOAD
            self.cpu.acc.value = self.memory_adapter.read(operand)

        elif opcode == 6:        # BRANCH (unconditional)
            branch_to(operand)

        elif opcode == 7:        # BRANCHZ (branch if ACC == 0)
            if self.cpu.acc.value == 0:
                branch_to(operand)

        elif opcode == 8:        # BRANCHPOS (branch if ACC >= 0)
            if self.cpu.acc.value >= 0:
                branch_to(operand)

        else:
            self.status_var.set(f"Unknown opcode {opcode} (ignored).")

    # --------------------------------------------------------------------------
    # Control actions
    # --------------------------------------------------------------------------
    def step(self):
        """Perform one fetch+execute cycle."""
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Press Reset to continue.")
            return

        try:
            # Fetch instruction into IR and increment PC
            self.cpu.fetch()
            # Execute the fetched instruction
            self.execute_instruction()
            # Update displayed state
            self.refresh_display()

            if not self.halted:
                self.status_var.set(f"Executed: {self.cpu.ir.value:03d} | PC now: {self.cpu.pc.value:02d}")
            else:
                self.status_var.set("Program halted.")
        except Exception as e:
            messagebox.showerror("Execution Error", str(e))
            self.halted = True

    def reset_cpu(self):
        """Reset CPU registers and clear halted flag."""
        self.cpu.reset()
        self.halted = False
        self.refresh_display()
        self.status_var.set("CPU reset. Program counter = 0.")

    def load_sample(self):
        """
        Load a simple addition program:
        0: LOAD 8   (508)
        1: ADD  9   (109)
        2: STORE 10 (310)
        3: HALT     (000)
        Data at address 8 = 5, address 9 = 3, address 10 = 0
        """
        # Clear memory first (optional)
        for i in range(100):
            self.memory_adapter.write(i, 0)

        # Program
        self.memory_adapter.write(0, 508)   # LOAD 8
        self.memory_adapter.write(1, 109)   # ADD  9
        self.memory_adapter.write(2, 310)   # STORE 10
        self.memory_adapter.write(3, 0)     # HALT

        # Data
        self.memory_adapter.write(8, 5)
        self.memory_adapter.write(9, 3)
        self.memory_adapter.write(10, 0)

        # Reset CPU and start from address 0
        self.cpu.reset()
        self.halted = False
        self.refresh_display()
        self.status_var.set("Sample program loaded (adds 5 + 3, stores result at address 10). Use Step to run.")

# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()