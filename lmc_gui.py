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

        self.fetch_btn = ttk.Button(btn_frame, text="Fetch", command=self.fetch_step)
        self.fetch_btn.grid(row=0, column=0, padx=3)

        self.decode_btn = ttk.Button(btn_frame, text="Decode", command=self.decode_step)
        self.decode_btn.grid(row=0, column=1, padx=3)

        self.execute_btn = ttk.Button(btn_frame, text="Execute", command=self.execute_step)
        self.execute_btn.grid(row=0, column=2, padx=3)

        # Full-step and utility buttons
        self.step_btn = ttk.Button(btn_frame, text="Step (Fetch+Execute)", command=self.step)
        self.step_btn.grid(row=0, column=3, padx=5)

        self.reset_btn = ttk.Button(btn_frame, text="Reset CPU", command=self.reset_cpu)
        self.reset_btn.grid(row=0, column=4, padx=5)

        self.load_btn = ttk.Button(btn_frame, text="Load Sample Program", command=self.load_sample)
        self.load_btn.grid(row=0, column=5, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Press Step to execute instructions.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # Initial refresh
        self.refresh_display()
        self._update_halted_status()

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
    # Status update helper
    # --------------------------------------------------------------------------
    def _update_halted_status(self):
        """Synchronizes GUI halted flag with CPU halted status."""
        self.halted = self.cpu.halted

    # --------------------------------------------------------------------------
    # Control actions
    # --------------------------------------------------------------------------
    def step(self):
        """Perform one fetch+decode+execute cycle."""
        self._update_halted_status()
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Press Reset to continue.")
            return

        while True:
            try:
                # Execute one complete fetch-decode-execute cycle
                instruction_before = self.cpu.ir.value
                running = self.cpu.execute_cycle()
                self._update_halted_status()

                # If there are OUT values, display them and clear buffer
                if self.cpu.output_buffer:
                    for outv in list(self.cpu.output_buffer):
                        messagebox.showinfo("OUT", f"Output: {outv:03d}")
                    self.cpu.output_buffer.clear()

                # Update displayed state
                self.refresh_display()

                if running:
                    self.status_var.set(f"Executed: {instruction_before:03d} | PC now: {self.cpu.pc.value:02d}")
                else:
                    self.status_var.set("Program halted. (HLT instruction executed)")
                break

            except RuntimeError as e:
                # Handle INP when no input is available by prompting the user
                if "INP: No input" in str(e):
                    from tkinter import simpledialog
                    val = simpledialog.askinteger("INP", "Enter input (0-999):", parent=self.root, minvalue=0, maxvalue=999)
                    if val is None:
                        messagebox.showwarning("INP cancelled", "No input provided. Halting execution.")
                        self.halted = True
                        break
                    try:
                        self.cpu.set_input(int(val))
                    except Exception as ex:
                        messagebox.showerror("Input Error", str(ex))
                        self.halted = True
                        break
                    # Retry executing the cycle which will now consume the input
                    continue
                else:
                    messagebox.showerror("Execution Error", str(e))
                    self.halted = True
                    break

            except Exception as e:
                messagebox.showerror("Execution Error", str(e))
                self.halted = True
                break

    def fetch_step(self):
        """Perform Fetch micro-step: load instruction from memory into IR and increment PC."""
        self._update_halted_status()
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Press Reset to continue.")
            return
        try:
            self.cpu.fetch()
            self.refresh_display()
            self.status_var.set(f"Fetched IR: {self.cpu.ir.value:03d} | PC: {self.cpu.pc.value:02d}")
        except Exception as e:
            messagebox.showerror("Fetch Error", str(e))

    def decode_step(self):
        """Perform Decode micro-step: decode the current IR and show mnemonic."""
        self._update_halted_status()
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Press Reset to continue.")
            return
        try:
            self.cpu.decode()
            decoded = self.cpu.get_decoded()
            if decoded is None:
                self.status_var.set("No instruction decoded")
                return
            opcode, operand = decoded
            mnemonic = {
                0: 'HLT', 1: 'ADD', 2: 'SUB', 3: 'STA', 5: 'LDA', 6: 'BRA', 7: 'BRZ', 8: 'BRP', 9: 'IO'
            }.get(opcode, f'UNK({opcode})')
            if opcode == 9:
                if operand == 1:
                    mnemonic = 'INP'
                elif operand == 2:
                    mnemonic = 'OUT'
                else:
                    mnemonic = f'IO({operand})'
            self.status_var.set(f"Decoded: {mnemonic} {operand:02d}")
        except Exception as e:
            messagebox.showerror("Decode Error", str(e))

    def execute_step(self):
        """Perform Execute micro-step: execute the previously decoded instruction."""
        self._update_halted_status()
        if self.halted:
            messagebox.showinfo("Halted", "CPU is halted. Press Reset to continue.")
            return
        try:
            # Execute may raise RuntimeError for INP if no input available
            self.cpu.execute_decoded()

            # If there are OUT values, display them and clear buffer
            if self.cpu.output_buffer:
                for outv in list(self.cpu.output_buffer):
                    messagebox.showinfo("OUT", f"Output: {outv:03d}")
                self.cpu.output_buffer.clear()

            self._update_halted_status()
            self.refresh_display()
            self.status_var.set(f"Executed. PC: {self.cpu.pc.value:02d}")
        except RuntimeError as e:
            # Handle INP when no input is available by prompting the user
            if "INP: No input" in str(e):
                from tkinter import simpledialog
                val = simpledialog.askinteger("INP", "Enter input (0-999):", parent=self.root, minvalue=0, maxvalue=999)
                if val is None:
                    messagebox.showwarning("INP cancelled", "No input provided. Halting execution.")
                    self.halted = True
                    return
                try:
                    self.cpu.set_input(int(val))
                except Exception as ex:
                    messagebox.showerror("Input Error", str(ex))
                    self.halted = True
                    return
                # Retry execution now that input has been provided
                try:
                    self.cpu.execute_decoded()
                except Exception as ex:
                    messagebox.showerror("Execution Error", str(ex))
                    self.halted = True
                    return
            else:
                messagebox.showerror("Execution Error", str(e))
                self.halted = True
                return

    def reset_cpu(self):
        """Reset CPU registers and clear halted flag."""
        self.cpu.reset()
        self._update_halted_status()
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
        self._update_halted_status()
        self.refresh_display()
        self.status_var.set("Sample program loaded (adds 5 + 3, stores result at address 10). Use Step to run.")

# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()