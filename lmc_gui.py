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
        for row in range(10):
            row_labels = []
            for col in range(10):
                lbl = tk.Label(mem_frame, text="000", width=5, relief=tk.RIDGE,
                               font=("Courier", 9), anchor=tk.CENTER, bg="#f0f0f0")
                lbl.grid(row=row, column=col, padx=1, pady=1)
                row_labels.append(lbl)
            self.mem_cells.append(row_labels)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.run_program, width=10)
        self.run_btn.grid(row=0, column=0, padx=4)
        self.step_btn = ttk.Button(btn_frame, text="Step", command=self.step, width=10)
        self.step_btn.grid(row=0, column=1, padx=4)
        self.fetch_btn = ttk.Button(btn_frame, text="Fetch", command=self.fetch_step, width=10)
        self.fetch_btn.grid(row=0, column=2, padx=4)
        self.decode_btn = ttk.Button(btn_frame, text="Decode", command=self.decode_step, width=10)
        self.decode_btn.grid(row=0, column=3, padx=4)
        self.execute_btn = ttk.Button(btn_frame, text="Execute", command=self.execute_step, width=10)
        self.execute_btn.grid(row=0, column=4, padx=4)
        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_cpu, width=10)
        self.reset_btn.grid(row=0, column=5, padx=4)
        self.load_btn = ttk.Button(btn_frame, text="Load Sample", command=self.load_sample, width=12)
        self.load_btn.grid(row=0, column=6, padx=4)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        self.refresh_display()

    def refresh_display(self):
        for addr in range(100):
            row = addr // 10
            col = addr % 10
            value = self.memory_adapter.read(addr)
            self.mem_cells[row][col].config(text=f"{value:03d}")

        self.acc_label.config(text=f"ACC: {self.cpu.acc.value:03d}")
        self.pc_label.config(text=f"PC: {self.cpu.pc.value:02d}")
        self.ir_label.config(text=f"IR: {self.cpu.ir.value:03d}")

    def _update_halted(self):
        self.halted = self.cpu.halted

    def step(self):
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Reset to continue.")
            return
        self._run_one_cycle()

    def run_program(self):
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Reset to continue.")
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

    def _run_one_cycle(self):
        try:
            instr = self.cpu.ir.value
            running = self.cpu.execute_cycle()
            self._update_halted()

            if self.cpu.output_buffer:
                for val in list(self.cpu.output_buffer):
                    messagebox.showinfo("Output", f"OUT: {val:03d}")
                self.cpu.output_buffer.clear()

            self.refresh_display()

            if not running:
                self.status_var.set("Program halted (HLT)")
                return False
            else:
                self.status_var.set(f"Executed {instr:03d} → PC: {self.cpu.pc.value:02d}")
            return True

        except RuntimeError as e:
            if "INP: No input" in str(e):
                val = simpledialog.askinteger("INP", "Enter input (0-999):",
                                            parent=self.root, minvalue=0, maxvalue=999)
                if val is None:
                    self.halted = True
                    self.status_var.set("Execution cancelled")
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

    def fetch_step(self):
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted.")
            return
        try:
            self.cpu.fetch()
            self.refresh_display()
            self.status_var.set(f"Fetched: {self.cpu.ir.value:03d}")
        except Exception as e:
            messagebox.showerror("Fetch Error", str(e))

    def decode_step(self):
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted.")
            return
        try:
            self.cpu.decode()
            decoded = self.cpu.get_decoded()
            if decoded:
                op, addr = decoded
                mnemonics = {0:'HLT',1:'ADD',2:'SUB',3:'STA',5:'LDA',6:'BRA',7:'BRZ',8:'BRP',9:'IO'}
                m = mnemonics.get(op, 'UNK')
                if op == 9:
                    m = 'INP' if addr == 1 else 'OUT' if addr == 2 else f'IO{addr}'
                self.status_var.set(f"Decoded: {m} {addr:02d}")
        except Exception as e:
            messagebox.showerror("Decode Error", str(e))

    def execute_step(self):
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted.")
            return
        try:
            self.cpu.execute_decoded()
            if self.cpu.output_buffer:
                for val in list(self.cpu.output_buffer):
                    messagebox.showinfo("Output", f"OUT: {val:03d}")
                self.cpu.output_buffer.clear()
            self._update_halted()
            self.refresh_display()
            self.status_var.set(f"Executed → PC: {self.cpu.pc.value:02d}")
        except RuntimeError as e:
            if "INP: No input" in str(e):
                val = simpledialog.askinteger("INP", "Enter input (0-999):",
                                            parent=self.root, minvalue=0, maxvalue=999)
                if val is None:
                    self.halted = True
                    return
                self.cpu.set_input(val)
                self.cpu.execute_decoded()
                self.refresh_display()
            else:
                messagebox.showerror("Error", str(e))
                self.halted = True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.halted = True

    def reset_cpu(self):
        self.cpu.reset()
        self._update_halted()
        self.is_running = False
        self.refresh_display()
        self.status_var.set("CPU Reset")

    def load_sample(self):
        for i in range(100):
            self.memory_adapter.write(i, 0)

        self.memory_adapter.write(0, 508)
        self.memory_adapter.write(1, 109)
        self.memory_adapter.write(2, 310)
        self.memory_adapter.write(3, 0)
        self.memory_adapter.write(8, 5)
        self.memory_adapter.write(9, 3)
        self.memory_adapter.write(10, 0)

        self.cpu.reset()
        self._update_halted()
        self.refresh_display()
        self.status_var.set("Sample program loaded (5 + 3)")

if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()
