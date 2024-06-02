import argparse
import os
import sys
import logging
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.isa import read_code, IOAddresses
from source.ALU import ALU
from source.instruction_decoder import InstructionDecoder

log_stream = StringIO()
logging.basicConfig(
    stream=log_stream,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s",
)


class DataPath:
    def __init__(self, memory, inp_data):
        self.memory = memory  # Общая память
        self.stack = []  # Стек
        self.stack_pointer = 0  # Указатель стека
        self.input_buffer = list(inp_data) + [0]  # Буфер для входных данных
        self.output_buffer = list()  # Буфер для выходных данных

        """Инициализация ALU"""
        self.alu_latch = 0
        self.alu = ALU(self)

    # Можно ли оставить?
    def write_io(self, value, tochar=False):
        """Вывод IO"""
        if tochar:
            value = chr(value)
        logging.debug(
            "output: %s << %s", repr("".join(self.output_buffer)), repr(value)
        )
        self.output_buffer.append(str(value))

    """Помещает значение в стек и увеличивает счетчик стека на 1"""

    def push_to_stack(self, value):
        self.stack.append(value)
        self.stack_pointer = self.stack_pointer + 1

    """Возвращает значение из стека и уменьшает счетчик стека на 1"""

    def pop_from_stack(self):
        if self.stack_pointer > 0:
            self.stack_pointer = self.stack_pointer - 1
            return self.stack.pop()
        raise IndexError("Stack underflow")

    """Загружает значение из памяти в стек"""

    def load(self):
        addr = self.pop_from_stack()  # Адрес для загрузки берется из стека
        if (
            addr == IOAddresses.INP_ADDR
        ):  # Если это адрес ввода, то значение в стек попадает из input buffer
            if self.input_buffer:
                symbol = self.input_buffer.pop(0)
                symbol_code = 0
                if isinstance(symbol, str):
                    symbol_code = ord(symbol)

                self.push_to_stack(symbol_code)
                logging.debug("input: %s", repr(symbol))
            else:
                raise EOFError("Input buffer is empty!")

        else:  # Если это просто адрес из памяти, то значение из него помещается в стек
            value = self.memory[addr]
            self.push_to_stack(value)

    """Сохраняет значение из стека в память"""

    def save(self, tochar=True):
        addr = self.pop_from_stack()  # Адрес для сохранения берется из стека
        val = self.pop_from_stack()  # Значение для сохранения берется из стека
        if (
            addr == IOAddresses.OUT_ADDR
        ):  # Если это адрес вывода, то значение из стека помещается в output buffer
            self.write_io(val, tochar)
        else:  # Если это просто адрес из памяти, то по этому адресу записывается значение
            self.memory[addr] = val


class ControlUnit:
    def __init__(self, memory, input_data):
        self.memory = memory  # Общая память
        self.pc = 0  # Счётчик программ
        self.halted = False  # Состояние остановки модели
        self.data_path = DataPath(memory, input_data)  # Инициализация DataPath
        self.instr_counter = 0  # Счетчик выполненных инструкций
        self.tick_counter = 0  # Счетчик тиков (модельного времени)
        self.instr_latch = 0  # Регистр хранения инструкции
        self.decoder = InstructionDecoder(self)  # Декодер инструкций
        self.mem_inp_pointer = (
            IOAddresses.INPUT_STORAGE
        )  # Указатель для сохранения символов в память ввода
        self.mem_out_pointer = (
            IOAddresses.INPUT_STORAGE
        )  # Указатель для загрузки символов из памяти вывода

        """Инициализация регистра и return stack для управления циклами"""
        self.loop_counter = 0
        self.init_val = 0
        self.max_val = 0
        self.step = 1

        """Регистр для хранения информации о переходе"""
        self.jump_latch = 0

    def tick(self, value=1):
        self.tick_counter += value

    def instr(self):
        self.instr_counter += 1

    """Загрузка информации о цикле в return stack"""

    def start_loop(self):
        self.init_val = self.data_path.pop_from_stack()
        self.max_val = self.data_path.pop_from_stack()
        self.loop_counter = self.init_val
        self.tick(3)

    """Проверка условия и остановка цикла"""

    def end_loop(self):
        next_value = self.loop_counter + self.step
        self.tick()
        if next_value <= self.max_val:
            self.loop_counter = next_value
            self.tick()
            return True
        else:
            self.init_val = 0
            self.max_val = 0
            self.tick(2)
            return False

    """Загрузка инструкции в регистр"""

    def fetch_instruction(self):
        if self.pc < len(self.memory) and self.memory[self.pc] is not None:
            self.instr_latch = self.memory[self.pc]
        else:
            raise IndexError("Program counter out of bounds")

    """Обработка инструкции из регистра"""

    def execute_instruction(self):
        instruction = self.instr_latch
        self.decoder.decode(instruction)
        if self.jump_latch == 0:
            self.pc = self.pc + 1
            self.instr()
        self.jump_latch = 0

    def run(self):
        try:
            while not self.halted:
                self.fetch_instruction()
                self.execute_instruction()
                logging.debug(self)
            logging.info("End simulation")
            logging.info("output_buffer: %s", repr("".join(self.data_path.output_buffer)))
        except EOFError:
            logging.warning("Input buffer is empty!")
        return "".join(self.data_path.output_buffer)

    def __repr__(self):
        top_of_stack = self.data_path.stack[-1] if self.data_path.stack else "Empty"
        state_repr = (
            "TICK: {:3} PC: {:3} LOOP_COUNTER: {:3} TOP OF STACK: {:7} SP: {:3}".format(
                self.tick_counter,
                self.pc,
                self.loop_counter,
                top_of_stack,
                self.data_path.stack_pointer,
            )
        )

        instr = self.memory[self.pc]
        if isinstance(instr, dict):
            opcode = instr["opcode"]
            instr_repr = str(opcode)

            if "arg" in instr:
                instr_repr += " arg: {}".format(instr["arg"])
        else:
            instr_repr = str(instr)

        return "{} \t{}".format(state_repr, instr_repr)


"""Запуск симуляции"""


def simulation(program, input_data, data_segment):
    memory = [0] * 1024  # Инициализация памяти
    for i, instruction in enumerate(program):  # Загрузка инструкций в память
        memory[i] = instruction

    # Инициализация сегмента данных
    base_address = IOAddresses.STRING_STORAGE
    for offset, content in data_segment.items():
        address = base_address + int(offset)
        length = content[0]
        for i in range(length + 1):
            memory[address + i] = content[i]

    control_unit = ControlUnit(memory, input_data)
    output = control_unit.run()

    logs = log_stream.getvalue()
    return output, control_unit.instr_counter, control_unit.tick_counter, logs


def run_all_programs(directory, input_file):
    for file in os.listdir(directory):
        if file.endswith(".json"):
            code_file = os.path.join(directory, file)
            print(f"Processing {code_file}")
            print()
            run_simulation(code_file, input_file)


def main(argums):
    try:
        if argums.all:
            if argums.input_file is None:
                print("Please specify an input file.")
            else:
                machine_code_dir = "./source/machine_code"
                run_all_programs(machine_code_dir, argums.input_file)
        elif argums.machine_code_file and argums.input_file:
            run_simulation(argums.machine_code_file, argums.input_file)
        else:
            print("Invalid usage. Run 'python machine.py -h' for help.")
    except Exception as e:
        print(f"Error in machine: {e}")


def run_simulation(machine_code_file, input_file):
    try:
        machine_code = read_code(machine_code_file)
        program = machine_code["program"]
        data_segment = machine_code["data"]
        with open(input_file, "r", encoding="utf-8") as file:
            input_data = file.read()
        output, instr_count, ticks, logs = simulation(program, input_data, data_segment)
        print(logs, end="")
        print("".join(output))
        print(f"instr_counter: {instr_count} ticks: {ticks}", end="")
    except Exception as e:
        print(f"Error during simulation: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run FORTH machine code simulations.")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Process all JSON files in the machine code directory.",
    )
    parser.add_argument(
        "input_file",
        type=str,
        nargs="?",
        default=None,
        help="Path to the input file for the machine.",
    )
    parser.add_argument(
        "machine_code_file",
        type=str,
        nargs="?",
        help="Path to a specific machine code file to run.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
