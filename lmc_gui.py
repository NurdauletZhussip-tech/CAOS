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

        reg_frame = ttk.LabelFrame(main_frame, text="Registers", padding="8")
        reg_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.acc_label = ttk.Label(reg_frame, text="ACC: 000", font=("Courier", 14, "bold"))
        self.acc_label.grid(row=0, column=0, padx=15)
        self.pc_label = ttk.Label(reg_frame, text="PC: 00", font=("Courier", 14, "bold"))
        self.pc_label.grid(row=0, column=1, padx=15)
        self.ir_label = ttk.Label(reg_frame, text="IR: 000", font=("Courier", 14, "bold"))
        self.ir_label.grid(row=0, column=2, padx=15)

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

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.run_program, width=10)
        self.run_btn.grid(row=0, column=0, padx=3)
        self.step_btn = ttk.Button(btn_frame, text="Step", command=self.step, width=10)
        self.step_btn.grid(row=0, column=1, padx=3)
        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_cpu, width=10)
        self.reset_btn.grid(row=0, column=2, padx=3)
        self.load_btn = ttk.Button(btn_frame, text="Load Program", command=self.load_program_menu, width=12)
        self.load_btn.grid(row=0, column=3, padx=3)

        self.status_var = tk.StringVar(value="Ready. Load a program and press Step or Run.")
        status = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)

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
                self.status_var.set("Program finished (HLT)")
                return False

            self.status_var.set(f"Executed {instr:03d} | PC: {self.cpu.pc.value:02d}")
            return True

        except RuntimeError as e:
            if "INP: No input" in str(e):
                val = simpledialog.askinteger("Input (INP)", "Enter number (0-999):",
                                              parent=self.root, minvalue=0, maxvalue=999)
                if val is None:
                    self.status_var.set("Input cancelled")
                    self.halted = True
                    return False
                self.cpu.set_input(val)
                return self._run_one_cycle()
            else:
                messagebox.showerror("Error", str(e))
                self.halted = True
                return False
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.halted = True
            return False

    def step(self):
        if self.halted:
            messagebox.showinfo("Halted", "Reset to continue.")
            return
        self._run_one_cycle()

    def run_program(self):
        if self.halted:
            messagebox.showinfo("Halted", "Reset first.")
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
        self._update_halted()
        self.is_running = False
        self.refresh_display()
        self.status_var.set("CPU Reset. Ready.")

    def load_program_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="1. Addition (5+3)", command=self.load_addition)
        menu.add_command(label="2. Multiplication (4×6)", command=self.load_multiplication)
        menu.add_command(label="3. Input + Output", command=self.load_inp_out)
        menu.add_command(label="4. Find Maximum", command=self.load_max)
        menu.add_separator()
        menu.add_command(label="Clear Memory", command=self.clear_memory)
        menu.tk_popup(self.load_btn.winfo_rootx(), self.load_btn.winfo_rooty() + 30)

    def clear_memory(self):
        for i in range(100):
            self.memory_adapter.write(i, 0)
        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Memory cleared.")

    def load_addition(self):
        self.clear_memory()
        self.memory_adapter.write(0, 508)
        self.memory_adapter.write(1, 109)
        self.memory_adapter.write(2, 310)
        self.memory_adapter.write(3, 0)
        self.memory_adapter.write(8, 5)
        self.memory_adapter.write(9, 3)
        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Loaded: Addition 5 + 3")

    def load_multiplication(self):
        self.clear_memory()
        self.memory_adapter.write(0, 508)
        self.memory_adapter.write(1, 109)
        self.memory_adapter.write(2, 109)
        self.memory_adapter.write(3, 109)
        self.memory_adapter.write(4, 109)
        self.memory_adapter.write(5, 109)
        self.memory_adapter.write(6, 109)
        self.memory_adapter.write(7, 310)
        self.memory_adapter.write(8, 0)
        self.memory_adapter.write(9, 6)
        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Loaded: 4 × 6 = 24")

    def load_inp_out(self):
        self.clear_memory()
        self.memory_adapter.write(0, 901)
        self.memory_adapter.write(1, 902)
        self.memory_adapter.write(2, 0)
        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Loaded: INP → OUT")

    def load_max(self):
        self.clear_memory()
        self.memory_adapter.write(0, 901)
        self.memory_adapter.write(1, 310)
        self.memory_adapter.write(2, 901)
        self.memory_adapter.write(3, 210)
        self.memory_adapter.write(4, 813)
        self.memory_adapter.write(5, 510)
        self.memory_adapter.write(6, 902)
        self.memory_adapter.write(7, 0)
        self.cpu.reset()
        self.refresh_display()
        self.status_var.set("Loaded: Find Maximum")

if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()
