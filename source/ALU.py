from source.isa import Opcode


class ALU:
    def __init__(self, data_path):
        self.data_path = data_path

    def execute(self, opcode, a, b=None):
        result = 0
        if opcode == Opcode.ADD:
            result = self.add(a, b)
        elif opcode == Opcode.OR:
            result = self.or_op(a, b)
        elif opcode == Opcode.MOD:
            result = self.mod(a, b)
        elif opcode == Opcode.EQUALS:
            result = self.equals(a, b)

        self.data_path.alu_latch = result

    @staticmethod
    def add(a, b):
        result = a + b
        return result

    @staticmethod
    def or_op(a, b):
        result = a | b
        return result

    @staticmethod
    def mod(a, b):
        result = b % a
        return result

    @staticmethod
    def equals(a, b):
        result = 1 if a == b else 0
        return result
