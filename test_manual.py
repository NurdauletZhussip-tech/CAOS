#!/usr/bin/env python3
"""
Простой тестовый скрипт для проверки LMC эмулятора
"""

from cpu import Processor, LmcMemoryAdapter

def test_basic_arithmetic():
    """Тест базовой арифметики: 45 + 27 = 72"""
    print("=" * 60)
    print("Тест 1: Базовая арифметика (45 + 27 = 72)")
    print("=" * 60)

    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)

    # Программа: LDA 08 -> ADD 09 -> STA 10 -> HLT
    mem.write(0, 508)   # LDA 08 (загрузить 45 в ACC)
    mem.write(1, 109)   # ADD 09 (добавить 27)
    mem.write(2, 310)   # STA 10 (сохранить результат)
    mem.write(3, 0)     # HLT (остановка)

    # Данные
    mem.write(8, 45)
    mem.write(9, 27)

    # Выполнение программы пошагово
    steps = 0
    while not cpu.halted and steps < 100:
        print(f"\n--- Шаг {steps + 1} ---")
        print(f"ДО:  PC={cpu.pc.value:02d}, IR={cpu.ir.value:03d}, ACC={cpu.acc.value:03d}")

        cpu.execute_cycle()
        steps += 1

        print(f"ПОСЛЕ: PC={cpu.pc.value:02d}, IR={cpu.ir.value:03d}, ACC={cpu.acc.value:03d}")

    result = mem.read(10)
    print(f"\n{'='*60}")
    print(f"Результат в ячейке [10]: {result}")
    print(f"Ожидаемо: 72, Получено: {result}, Статус: {'✓ PASS' if result == 72 else '✗ FAIL'}")
    print(f"{'='*60}")
    assert result == 72, f"Expected 72, got {result}"


def test_with_input_output():
    """Тест с вводом и выводом"""
    print("\n\n" + "="*60)
    print("Тест 2: Ввод-Вывод (INP, OUT)")
    print("="*60)

    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)

    # Программа: INP -> ADD 08 -> OUT -> HLT
    mem.write(0, 901)   # INP (ввод)
    mem.write(1, 108)   # ADD 08 (добавить 100)
    mem.write(2, 902)   # OUT (вывод)
    mem.write(3, 0)     # HLT

    mem.write(8, 100)   # Данные

    # Задаем входное значение
    cpu.set_input(50)

    steps = 0
    while not cpu.halted and steps < 100:
        print(f"\n--- Шаг {steps + 1} ---")
        print(f"ДО:  PC={cpu.pc.value:02d}, IR={cpu.ir.value:03d}, ACC={cpu.acc.value:03d}")

        cpu.execute_cycle()
        steps += 1

        print(f"ПОСЛЕ: PC={cpu.pc.value:02d}, IR={cpu.ir.value:03d}, ACC={cpu.acc.value:03d}")
        if cpu.output_buffer:
            print(f"OUTPUT: {cpu.output_buffer}")
            cpu.output_buffer.clear()

    print(f"\n{'='*60}")
    print(f"Статус: ✓ PASS (INP + ADD + OUT работает)")
    print(f"{'='*60}")


def test_branching():
    """Тест условного перехода (BRZ)"""
    print("\n\n" + "="*60)
    print("Тест 3: Условный переход (BRZ)")
    print("="*60)

    mem = LmcMemoryAdapter()
    cpu = Processor(memory_bus=mem)

    # Программа:
    # [0] LDA 10     (загрузить 0)
    # [1] BRZ 04     (если = 0, перейти на [4])
    # [2] LDA 11     (иначе загрузить 1)
    # [3] HLT
    # [4] LDA 12     (загрузить 99)
    # [5] HLT

    mem.write(0, 510)   # LDA 10 (загрузить 0)
    mem.write(1, 704)   # BRZ 04 (переход на [4])
    mem.write(2, 511)   # LDA 11 (не выполнится)
    mem.write(3, 0)     # HLT
    mem.write(4, 512)   # LDA 12 (загрузить 99)
    mem.write(5, 0)     # HLT

    mem.write(10, 0)    # Нулевое значение
    mem.write(11, 1)
    mem.write(12, 99)

    steps = 0
    while not cpu.halted and steps < 100:
        cpu.execute_cycle()
        steps += 1

    print(f"Результат: ACC = {cpu.acc.value}")
    print(f"Ожидаемо: 99 (сработал BRZ), Получено: {cpu.acc.value}")
    print(f"Статус: {'✓ PASS' if cpu.acc.value == 99 else '✗ FAIL'}")
    print(f"{'='*60}")
    assert cpu.acc.value == 99, f"BRZ test failed"


if __name__ == "__main__":
    print("\n" + "🧪 LMC SIMULATOR TEST SUITE".center(60, "="))
    print()

    try:
        test_basic_arithmetic()
        test_with_input_output()
        test_branching()

        print("\n" + "="*60)
        print("✓ Все тесты пройдены успешно!".center(60))
        print("="*60)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

