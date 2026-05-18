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