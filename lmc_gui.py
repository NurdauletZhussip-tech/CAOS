import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from cpu import Processor, LmcMemoryAdapter

class LmcGui:
    def __init__(self, root):
        self.root = root
        root.title("Little Man Computer Simulator (Step-by-Step)")
        root.resizable(False, False)

        # Инициализация бэкенда ядра LMC
        self.memory_adapter = LmcMemoryAdapter()
        self.cpu = Processor(memory_bus=self.memory_adapter)
        self.halted = False
        self.is_running = False

        # Переменная для отслеживания микрошагов цикла процессора: "FETCH", "DECODE", "EXECUTE"
        self.cycle_phase = "FETCH"

        # Главный контейнер
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Фрейм Регистров и Фаз Процессора ---
        reg_frame = ttk.LabelFrame(main_frame, text="Registers & CPU Phase", padding="8")
        reg_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.acc_label = ttk.Label(reg_frame, text="ACC: 000", font=("Courier", 14, "bold"))
        self.acc_label.grid(row=0, column=0, padx=15)

        self.pc_label = ttk.Label(reg_frame, text="PC: 00", font=("Courier", 14, "bold"))
        self.pc_label.grid(row=0, column=1, padx=15)

        self.ir_label = ttk.Label(reg_frame, text="IR: 000", font=("Courier", 14, "bold"))
        self.ir_label.grid(row=0, column=2, padx=15)

        # Текстовый индикатор текущей фазы
        self.phase_label = ttk.Label(reg_frame, text="PHASE: FETCH", font=("Courier", 12, "bold"), foreground="#1f77b4")
        self.phase_label.grid(row=0, column=3, padx=15)

        # --- Фрейм Сетки Памяти ---
        mem_frame = ttk.LabelFrame(main_frame, text="Memory (0–99) [Click cell to Edit]", padding="5")
        mem_frame.grid(row=1, column=0, pady=(0, 10), sticky="nw")

        self.mem_cells = []
        for r in range(10):
            row = []
            for c in range(10):
                addr = r * 10 + c
                lbl = tk.Label(mem_frame, text="000", width=5, relief=tk.RIDGE,
                               font=("Courier", 9), anchor="center", bg="#f0f0f0", cursor="hand2")
                lbl.grid(row=r, column=c, padx=1, pady=1)

                # Привязываем ручное редактирование ячейки по клику мыши
                lbl.bind("<Button-1>", self.make_cell_click_handler(addr))
                row.append(lbl)
            self.mem_cells.append(row)

        # --- Панель Конструктора Команд (Ручной выбор и ввод) ---
        input_frame = ttk.LabelFrame(main_frame, text="Command Builder / Manual Input", padding="8")
        input_frame.grid(row=1, column=1, padx=(10, 0), pady=(0, 10), sticky="nwe")

        ttk.Label(input_frame, text="Instruction:").grid(row=0, column=0, sticky="w", pady=4)
        self.cmd_combo = ttk.Combobox(input_frame, width=15, state="readonly")
        self.cmd_combo['values'] = [
            "ADD (1xx)", "SUB (2xx)", "STA (3xx)", "LDA (5xx)",
            "BRA (6xx)", "BRZ (7xx)", "BRP (8xx)", "INP (901)",
            "OUT (902)", "HLT (000)", "DATA (Value)"
        ]
        self.cmd_combo.current(0)
        self.cmd_combo.grid(row=0, column=1, pady=4, sticky="w")
        self.cmd_combo.bind("<<ComboboxSelected>>", self.on_command_select)

        ttk.Label(input_frame, text="Operand/Value:").grid(row=1, column=0, sticky="w", pady=4)
        self.op_entry = ttk.Entry(input_frame, width=10)
        self.op_entry.insert(0, "0")
        self.op_entry.grid(row=1, column=1, pady=4, sticky="w")

        ttk.Label(input_frame, text="Cell Address:").grid(row=2, column=0, sticky="w", pady=4)
        self.addr_entry = ttk.Entry(input_frame, width=10)
        self.addr_entry.insert(0, "0")
        self.addr_entry.grid(row=2, column=1, pady=4, sticky="w")

        self.write_btn = ttk.Button(input_frame, text="Write to Memory", command=self.write_command_to_mem)
        self.write_btn.grid(row=3, column=0, columnspan=2, pady=12, sticky="ew")

        # --- Фрейм Управления Симуляцией ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.run_program, width=12)
        self.run_btn.grid(row=0, column=0, padx=6)

        self.step_btn = ttk.Button(btn_frame, text="Micro-Step", command=self.step, width=12)
        self.step_btn.grid(row=0, column=1, padx=6)

        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_cpu, width=12)
        self.reset_btn.grid(row=0, column=2, padx=6)

        self.load_btn = ttk.Button(btn_frame, text="Load Sample", command=self.load_sample, width=14)
        self.load_btn.grid(row=0, column=3, padx=6)

        # Строка Статуса
        self.status_var = tk.StringVar(value="Ready. Build commands, click cells, or click Micro-Step.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="3")
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.refresh_display()

    def refresh_display(self):
        """Обновление всего графического интерфейса в соответствии с состоянием памяти и CPU."""
        for addr in range(100):
            r, c = divmod(addr, 10)
            val = self.memory_adapter.read(addr)
            self.mem_cells[r][c].config(text=f"{val:03d}")

            # Подсветка ячейки, на которую указывает программный счетчик (PC) в фазе FETCH
            if addr == self.cpu.pc.value and not self.halted:
                self.mem_cells[r][c].config(bg="#cfe2ff")  # Нежно-синий цвет для текущего PC
            else:
                self.mem_cells[r][c].config(bg="#f0f0f0")

        # Обновление лейблов регистров
        self.acc_label.config(text=f"ACC: {self.cpu.acc.value:03d}")
        self.pc_label.config(text=f"PC: {self.cpu.pc.value:02d}")
        self.ir_label.config(text=f"IR: {self.cpu.ir.value:03d}")

        # Обновление фазового индикатора и его цвета
        self.phase_label.config(text=f"PHASE: {self.cycle_phase}")
        if self.cycle_phase == "FETCH":
            self.phase_label.config(foreground="#1f77b4") # Синий
        elif self.cycle_phase == "DECODE":
            self.phase_label.config(foreground="#ff7f0e") # Оранжевый
        elif self.cycle_phase == "EXECUTE":
            self.phase_label.config(foreground="#2ca02c") # Зеленый

    def _update_halted(self):
        self.halted = self.cpu.halted

    def step(self):
        """Выполняет строго ОДНУ микро-операцию из Fetch->Decode->Execute."""
        if self.halted:
            messagebox.showinfo("Halted", "Processor is halted. Press Reset to start over.")
            return

        try:
            if self.cycle_phase == "FETCH":
                current_pc = self.cpu.pc.value
                self.cpu.fetch()
                self.cycle_phase = "DECODE"
                self.refresh_display()
                self.status_var.set(f"[FETCH] Inst from cell {current_pc:02d} loaded into IR ({self.cpu.ir.value:03d}). PC incremented.")

            elif self.cycle_phase == "DECODE":
                self.cpu.decode()
                decoded = self.cpu.get_decoded()
                self.cycle_phase = "EXECUTE"
                self.refresh_display()
                if decoded:
                    op, operand = decoded
                    cmd_name = self.get_cmd_name(op, operand)
                    self.status_var.set(f"[DECODE] IR broken down into -> Operation: {cmd_name}, Operand address: {operand:02d}.")

            elif self.cycle_phase == "EXECUTE":
                decoded = self.cpu.get_decoded()
                if decoded:
                    op, operand = decoded
                    # Перехват ручного ввода INP, если буфер пуст
                    if op == 9 and operand == 1 and not self.cpu._input_buffer:
                        was_running = self.is_running
                        self.is_running = False  # Приостанавливаем авто-ран

                        val = simpledialog.askinteger("INP Instruction", "Enter an integer (0-999):",
                                                      parent=self.root, minvalue=0, maxvalue=999)
                        if val is None:
                            self.status_var.set("Execution paused. Waiting for valid INP input.")
                            return
                        self.cpu.set_input(val)

                        if was_running: # Возвращаем авто-ран, если он был активен
                            self.is_running = True
                            self.root.after(10, self.run_loop)
                            return

                # Сама стадия выполнения
                self.cpu.execute_decoded()
                self._update_halted()

                # Проверка буфера вывода OUT
                if self.cpu.output_buffer:
                    for v in list(self.cpu.output_buffer):
                        messagebox.showinfo("OUT Instruction", f"LMC Output Window: {v:03d}")
                    self.cpu.output_buffer.clear()

                self.cycle_phase = "FETCH"
                self.refresh_display()

                if self.halted:
                    self.status_var.set("Program execution finished (HLT reached).")
                else:
                    self.status_var.set("[EXECUTE] Instruction cycle finished. Ready for next FETCH.")

        except Exception as e:
            messagebox.showerror("Execution Error", str(e))
            self.halted = True
            self.is_running = False

    def run_program(self):
        """Запуск программы в автоматическом режиме с визуализацией микрошагов."""
        if self.halted:
            messagebox.showinfo("Halted", "Press Reset first.")
            return
        if self.is_running:
            return

        self.is_running = True
        self.run_btn.config(text="Stop", command=self.stop_program)
        self.run_loop()

    def run_loop(self):
        """Асинхронный цикл симуляции через root.after, чтобы интерфейс не зависал."""
        if self.is_running and not self.halted:
            self.step()
            # 500мс задержка между микрошагами (Fetch->Decode->Execute), чтобы глаз успевал следить
            if self.is_running and not self.halted:
                self.root.after(500, self.run_loop)
        else:
            self.is_running = False
            self.run_btn.config(text="Run", command=self.run_program)

    def stop_program(self):
        """Остановка автоматического выполнения."""
        self.is_running = False
        self.run_btn.config(text="Run", command=self.run_program)

    def reset_cpu(self):
        """Полный сброс процессора и фазы машины."""
        self.cpu.reset()
        self.halted = False
        self.is_running = False
        self.cycle_phase = "FETCH"
        self.refresh_display()
        self.status_var.set("CPU Reset. Phase set to FETCH. Ready.")

    # --- Обработчики ручного ввода и селектора команд ---

    def make_cell_click_handler(self, addr):
        """Фабрика функций для обработки кликов по конкретной ячейке сетки."""
        return lambda event: self.edit_cell_dialog(addr)

    def edit_cell_dialog(self, addr):
        """Диалоговое окно прямого редактирования значения ячейки памяти."""
        val = simpledialog.askinteger("Edit Cell", f"Enter raw data for cell {addr:02d} (0-999):",
                                      parent=self.root, minvalue=0, maxvalue=999)
        if val is not None:
            self.memory_adapter.write(addr, val)
            self.refresh_display()
            self.status_var.set(f"Manually injected data {val:03d} into cell {addr:02d}")

    def on_command_select(self, event):
        """Динамическое включение/выключение поля операнда в зависимости от выбранной команды."""
        selected = self.cmd_combo.get()
        if "INP" in selected or "OUT" in selected or "HLT" in selected:
            self.op_entry.delete(0, tk.END)
            self.op_entry.insert(0, "0")
            self.op_entry.config(state="disabled")
        else:
            self.op_entry.config(state="normal")

    def write_command_to_mem(self):
        """Сборка машинного кода команды из GUI конструктора и запись в указанный адрес ячейки."""
        selected = self.cmd_combo.get()
        try:
            addr = int(self.addr_entry.get())
            if not (0 <= addr <= 99):
                raise ValueError("Cell target address must be between 0 and 99.")

            operand = int(self.op_entry.get() if self.op_entry.get() else 0)
            if not (0 <= operand <= 99) and "DATA" not in selected:
                raise ValueError("Operand address must be 0-99.")

            # Кодирование команд в соответствии со спецификацией LMC Instruction Set
            if "ADD" in selected: code = 100 + operand
            elif "SUB" in selected: code = 200 + operand
            elif "STA" in selected: code = 300 + operand
            elif "LDA" in selected: code = 500 + operand
            elif "BRA" in selected: code = 600 + operand
            elif "BRZ" in selected: code = 700 + operand
            elif "BRP" in selected: code = 800 + operand
            elif "INP" in selected: code = 901
            elif "OUT" in selected: code = 902
            elif "HLT" in selected: code = 0
            elif "DATA" in selected:
                code = operand
                if not (0 <= code <= 999):
                    raise ValueError("Raw data value must be 0-999.")
            else:
                raise ValueError("Unknown configuration selection.")

            self.memory_adapter.write(addr, code)
            self.refresh_display()
            self.status_var.set(f"Assembled and wrote {code:03d} to memory cell {addr:02d}.")
        except Exception as e:
            messagebox.showerror("Assembling Error", str(e))

    def get_cmd_name(self, op, am):
        """Вспомогательный хелпер для разбора имени команды по коду операции."""
        if op == 0: return "HLT"
        if op == 1: return f"ADD (Address {am:02d})"
        if op == 2: return f"SUB (Address {am:02d})"
        if op == 3: return f"STA (Address {am:02d})"
        if op == 5: return f"LDA (Address {am:02d})"
        if op == 6: return f"BRA (Branch {am:02d})"
        if op == 7: return f"BRZ (Branch Zero {am:02d})"
        if op == 8: return f"BRP (Branch Positive {am:02d})"
        if op == 9:
            if am == 1: return "INP"
            if am == 2: return "OUT"
        return "UNKNOWN"

    def load_sample(self):
        """Загрузка базового демонстрационного примера со всеми ключевыми операциями."""
        for i in range(100):
            self.memory_adapter.write(i, 0)

        # Пишем цепочку команд: INP -> OUT -> LDA -> ADD -> STA -> OUT -> HLT
        self.memory_adapter.write(0, 901)   # INP
        self.memory_adapter.write(1, 902)   # OUT
        self.memory_adapter.write(2, 508)   # LDA 08
        self.memory_adapter.write(3, 109)   # ADD 09
        self.memory_adapter.write(4, 310)   # STA 10
        self.memory_adapter.write(5, 902)   # OUT
        self.memory_adapter.write(6, 0)     # HLT

        # Статические данные для теста
        self.memory_adapter.write(8, 45)
        self.memory_adapter.write(9, 27)

        self.cpu.reset()
        self.cycle_phase = "FETCH"
        self.halted = False
        self.is_running = False
        self.refresh_display()
        self.status_var.set("Sample loaded: INP → OUT → LDA → ADD → STA → OUT → HLT.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LmcGui(root)
    root.mainloop()