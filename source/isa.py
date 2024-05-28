import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Операции"""
    CR = "CR"  # Перевод строки
    DUP = "DUP"  # Продублировать верхний элемент стека
    JZ = "JZ"  # Условный переход, если на вершине стека ноль (jump if zero)
    LOOP_START = "LOOP_START"  # Начало цикла и его параметры
    LOOP_END = "LOOP_END"  # Окончание цикла
    PUSH = "PUSH"  # Добавить значение в стек
    PRINT_TOP = "PRINT_TOP"  # Вывод верхнего элемент
    EQUALS = "EQUALS"  # Равно
    MOD = "MOD"  # Деление по модулю
    OR = "OR"  # Или
    ADD = "ADD"  # Сложить 2 верхних элемента стека
    LOAD = "LOAD"  # Загрузить элемент из памяти в стек
    DEC_I = "DEC_I"  # Уменьшить значение счетчика цикла на 1
    SAVE = "SAVE"  # Сохранить значение из стека в память
    HALT = "HALT"  # Остановка

    def __str__(self):
        return str(self.value)


class IOAddresses:
    INP_ADDR = 0x0100  # Адрес ввода
    OUT_ADDR = 0x0101  # Адрес вывода
    INPUT_STORAGE = 0x0200  # Хранилище ввода
    STRING_STORAGE = 0x0300  # Начало области хранения строк


"""Машкод в файл"""


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(code, file, indent=4)


"""Чтение машкода из файла"""


def read_code(filename):
    with open(filename, "r", encoding="utf-8") as file:
        code = json.load(file)
    for instruction in code["program"]:
        instruction["opcode"] = Opcode(instruction["opcode"])
    return code
