import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from cpu import Processor, LmcMemoryAdapter

class LmcGui:
    def __init__(self, root):
        self.root = root
        root.title("Little Man Computer Simulator")
        root.resizable(False, False)

        self.memory_adapter = LmcMemoryAdapter()
        self.cpu = Processor(memory_bus=self.memory_adapter)
        self.halted = False
        self.is_running = False

        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Registers
        reg_frame = ttk.LabelFrame(main_frame, text="Registers", padding="8")
        reg_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.acc_label = ttk.Label(reg_frame, text="ACC: 000", font=("Courier", 14, "bold"))
        self.acc_label.grid(row=0, column=0, padx=20)
        self.pc_label = ttk.Label(reg_frame, text="PC: 00", font=("Courier", 14, "bold"))
        self.pc_label.grid(row=0, column=1, padx=20)
        self.ir_label = ttk.Label(reg_frame, text="IR: 000", font=("Courier", 14, "bold"))
        self.ir_label.grid(row=0, column=2, padx=20)

        # Memory Mapping
        mem_frame = ttk.LabelFrame(main_frame, text="Memory (0–99)", padding="5")
        mem_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self.mem_cells = []
        for r in range(10):
            row = []
            for c in range(10):
                lbl = tk.Label(mem_frame, text="000", width=5, relief=tk.RIDGE,
                               font=("Courier", 9), anchor="center", bg="#f0f0f0")
                lbl.grid(row=r, column=c, padx=1, pady=1)
                row.append(lbl)
            self.mem_cells.append(row)

        # Control Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.run_program, width=10)
        self.run_btn.grid(row=0, column=0, padx=4)
        self.step_btn = ttk.Button(btn_frame, text="Step", command=self.step, width=10)
        self.step_btn.grid(row=0, column=1, padx=4)
        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_cpu, width=10)
        self.reset_btn.grid(row=0, column=2, padx=4)
        self.load_btn = ttk.Button(btn_frame, text="Load Sample", command=self.load_sample, width=12)
        self.load_btn.grid(row=0, column=3, padx=4)

        self.status_var = tk.StringVar(value="Ready. Press Load Sample then Step or Run.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.refresh_display()

    def refresh_display(self):
        for addr in range(100):
            r, c = divmod(addr, 10)
            val = self.memory_adapter.read(addr)
            self.mem_cells[r][c].config(text=f"{val:03d}")

        self.acc_label.config(text=f"ACC: {self.cpu.acc.value:03d}")
        self.pc_label.config(text=f"PC: {self.cpu.pc.value:02d}")
        self.ir_label.config(text=f"IR: {self.cpu.ir.value:03d}")

    def _update_halted(self):
        self.halted = self.cpu.halted

    def _run_one_cycle(self):
        try:
            instr = self.cpu.ir.value
            running = self.cpu.execute_cycle()
            self._update_halted()

            if self.cpu.output_buffer:
                for v in list(self.cpu.output_buffer):
                    messagebox.showinfo("OUT", f"Output: {v:03d}")
                self.cpu.output_buffer.clear()

            self.refresh_display()

            if not running:
                self.status_var.set("Program halted (HLT)")
                return False

            self.status_var.set(f"Executed {instr:03d} | PC: {self.cpu.pc.value:02d}")
            return True

        except RuntimeError as e:
            if "INP: No input" in str(e):
                val = simpledialog.askinteger("INP", "Enter number (0-999):", 
                                            parent=self.root, minvalue=0, maxvalue=999)
                if val is None:
                    self.halted = True
                    return False
                self.cpu.set_input(val)
                return self._run_one_cycle()
            else:
                messagebox.showerror("Error", str(e))
                self.halted = True
                return False

    def step(self):
        if self.halted:
            messagebox.showinfo("Halted", "Press Reset to continue.")
            return
        self._run_one_cycle()

    def run_program(self):
        if self.halted:
            messagebox.showinfo("Halted", "Press Reset first.")
            return
        if self.is_running:
            return

        self.is_running = True
        self.run_btn.config(text="Running...", state="disabled")

        while self.is_running and not self.halted:
            self.root.update()
            if not self._run_one_cycle():
                break

        self.is_running = False
        self.run_btn.config(text="Run", state="normal")

    def reset_cpu(self):
        self.cpu.reset()
        self.halted = False
        self.is_running = False
        self.refresh_display()
        self.status_var.set("CPU has been reset.")

    def load_sample(self):
        for i in range(100):
            self.memory_adapter.write(i, 0)

        self.memory_adapter.write(0, 901)   # INP
        self.memory_adapter.write(1, 902)   # OUT
        self.memory_adapter.write(2, 508)   # LDA 08
        self.memory_adapter.write(3, 109)   # ADD 09
        self.memory_adapter.write(4, 902)   # OUT
        self.memory_adapter.write(5, 0)     # HLT

        self.memory_adapter.write(8, 25)
        self.memory_adapter.write(9, 17)

        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Sample loaded: INP → OUT → 25+17 → OUT")

if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()
