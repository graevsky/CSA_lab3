import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from source.isa import Opcode, write_code, IOAddresses


def first_pass(lines):
    procedures = {}
    main_program = []
    current_proc = None

    for line in lines:
        line = line.split("\\")[0].strip()
        if not line:
            continue
        commands = line.split()
        i = 0
        while i < len(commands):
            command = commands[i]
            if command == ":":
                current_proc = commands[i + 1]
                procedures[current_proc] = []
                i += 2
            elif command == ";":
                current_proc = None
                i += 1
            elif current_proc:
                procedures[current_proc].append(commands[i])
                i += 1
            else:
                main_program.append(commands[i])
                i += 1
    return procedures, main_program


def expand_procedures(commands, procedures):
    expanded_program = []
    for command in commands:
        if command in procedures:
            expanded_program.extend(expand_procedures(procedures[command], procedures))
        else:
            expanded_program.append(command)
    return expanded_program


def preprocess_commands(commands):
    preprocessed = []
    strings = {}
    string_address = 0

    i = 0
    while i < len(commands):
        command = commands[i]
        if command == "do":
            if i < 2:
                raise ValueError("Invalid 'do' loop syntax")
            preprocessed.pop()
            preprocessed.pop()
            preprocessed.append(f"{commands[i - 2]} {commands[i - 1]} do")
        elif command.startswith('."'):
            string_literal = command[2:]
            if string_literal.endswith('"'):
                string_literal = string_literal[:-1]
            else:
                while i + 1 < len(commands) and not commands[i + 1].endswith('"'):
                    string_literal += " " + commands[i + 1]
                    i += 1
                if i + 1 < len(commands) and commands[i + 1].endswith('"'):
                    string_literal += " " + commands[i + 1][:-1]
                    i += 1

            string_length = len(string_literal)
            strings[string_address] = [string_length] + [
                ord(char) for char in string_literal
            ]
            preprocessed.append(f"PSTR {string_address}")
            string_address += string_length + 1
        else:
            preprocessed.append(command)
        i += 1
    return preprocessed, strings


command_to_opcode = {
    ".": Opcode.PRINT_TOP,
    "mod": Opcode.MOD,
    "or": Opcode.OR,
    "==": Opcode.EQUALS,
    "cr": Opcode.CR,
    "+": Opcode.ADD,
    "dup": Opcode.DUP,
    "dec_i": Opcode.DEC_I,
    "save": Opcode.SAVE,
}


def second_pass(commands):
    code = []
    index = 0
    loop_stack = []
    if_stack = []

    i = 0
    while i < len(commands):
        command = commands[i]
        opcode = None
        arguments = []

        if command.isdigit() or command == "i":
            arguments.append(int(command) if command.isdigit() else "i")
            opcode = Opcode.PUSH
        elif " do" in command:
            parts = command.split()
            if len(parts) != 3 or parts[2] != "do":
                raise ValueError("Invalid 'do' loop syntax")
            max_value = int(parts[0])
            initial_value = int(parts[1])

            code.append(
                {
                    "index": index,
                    "opcode": Opcode.PUSH,
                    "arg": max_value,
                }
            )
            index += 1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.PUSH,
                    "arg": initial_value,
                }
            )
            index += 1
            loop_start_index = index
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.LOOP_START,
                    "arg": None,
                }
            )
            loop_stack.append(loop_start_index)
            index += 1
            i += 1
            continue
        elif command == "loop":
            if not loop_stack:
                raise ValueError("Mismatched 'loop' without 'do'")

            loop_start_index = loop_stack.pop()
            code.append(
                {"index": index, "opcode": Opcode.LOOP_END, "arg": loop_start_index}
            )
            index += 1
            i += 1
            continue
        elif command == "if":
            if_stack.append(index)
            code.append({"index": index, "opcode": Opcode.JZ, "arg": None})
            index += 1
        elif command == "then":
            if not if_stack:
                raise ValueError("Mismatched 'then' without 'if'")
            if_index = if_stack.pop()
            code[if_index]["arg"] = index
        elif command.startswith("PSTR"):
            address = int(command.split()[1])

            index += 1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.PUSH,
                    "arg": address + IOAddresses.STRING_STORAGE,
                }
            )
            index += 1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.LOAD,
                    "arg": None,
                }
            )
            index += 1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.PUSH,
                    "arg": 1,
                }
            )
            index += 1

            loop_start_index = index-1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.LOOP_START,
                    "arg": None,
                }
            )
            index += 1
            code.append(
                {
                    "index": index,
                    "opcode": Opcode.PUSH,
                    "arg": address + IOAddresses.STRING_STORAGE,
                }
            )
            index += 1
            code.append({"index": index, "opcode": Opcode.PUSH, "arg": "i"})
            index += 1
            code.append({"index": index, "opcode": Opcode.ADD, "arg": None})
            index += 1
            code.append({"index": index, "opcode": Opcode.LOAD, "arg": None})
            index += 1
            code.append(
                {"index": index, "opcode": Opcode.PUSH, "arg": IOAddresses.OUT_ADDR}
            )
            index += 1
            code.append({"index": index, "opcode": Opcode.SAVE, "arg": None})
            index += 1
            code.append(
                {"index": index, "opcode": Opcode.LOOP_END, "arg": loop_start_index}
            )
            index += 1
        elif command == "inp":
            code.append(
                {"index": index, "opcode": Opcode.PUSH, "arg": IOAddresses.INP_ADDR}
            )
            index += 1
            code.append({"index": index, "opcode": Opcode.LOAD, "arg": None})
            index += 1
        elif command == "out":
            code.append({"index": index, "opcode": Opcode.DUP, "arg": None})
            index += 1
            code.append(
                {"index": index, "opcode": Opcode.PUSH, "arg": IOAddresses.OUT_ADDR}
            )
            index += 1
            code.append({"index": index, "opcode": Opcode.SAVE, "arg": None})
            index += 1
        elif command == "store":
            code.append({"index": index, "opcode": Opcode.PUSH, "arg": "in_pointer"})
            index += 1
            code.append({"index": index, "opcode": Opcode.SAVE, "arg": None})
            index += 1
        elif command == "load":
            code.append({"index": index, "opcode": Opcode.PUSH, "arg": "out_pointer"})
            index += 1
            code.append({"index": index, "opcode": Opcode.LOAD, "arg": None})
            index += 1
        elif command in command_to_opcode:
            opcode = command_to_opcode[command]

        if opcode:
            code.append(
                {
                    "index": index,
                    "opcode": opcode.value,
                    "arg": arguments[0] if arguments else None,
                }
            )
            index += 1
        i += 1

    code.append({"index": index, "opcode": Opcode.HALT, "arg": None})
    for i, instr in enumerate(code):
        instr["index"] = i
    return code

def translate(text):
    lines = text.strip().split("\n")
    loc = len(lines)

    procedures, main_program = first_pass(lines)

    expanded_program = expand_procedures(main_program, procedures)
    preprocessed_commands, strings = preprocess_commands(expanded_program)
    code = second_pass(preprocessed_commands)

    print(
        f"source LoC: {loc} code instr: {len(code)}"
    )

    return {"data": strings, "program": code}


def process_dir(directory, output_folder):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".forth"):
                source_path = os.path.join(root, file)
                machine_code = translate(
                    open(source_path, "r", encoding="utf-8").read()
                )
                output_file = os.path.join(
                    output_folder, file.replace(".forth", ".json")
                )
                write_code(output_file, machine_code)
                print(f"Machine code has been written to {output_file}")


def main(arguments):
    try:
        if arguments.all:
            process_dir(arguments.input_folder, arguments.output_folder)
        else:
            source_file = arguments.source_file
            target_file = arguments.target_file
            with open(source_file, "r", encoding="utf-8") as file:
                source_text = file.read()
            machine_code = translate(source_text)
            output_dir = arguments.output_folder
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_file = os.path.join(output_dir, target_file)
            write_code(output_file, machine_code)
    except Exception as e:
        print(f"Error in translator: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Translate FORTH code to machine code."
    )
    parser.add_argument(
        "source_file", nargs="?", help="The FORTH source file to translate."
    )
    parser.add_argument(
        "target_file", nargs="?", help="Machine code target file."
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Process all FORTH files in the specified directory.",
    )
    parser.add_argument(
        "-i",
        "--input_folder",
        default="./progs",
        help="Directory containing FORTH files.",
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        default="./source/machine_code",
        help="Directory to store the output JSON files.",
    )
    args = parser.parse_args()

    if not args.all:
        if not args.source_file or not args.target_file:
            parser.error("the following arguments are required: source_file, target_file")

    return args


if __name__ == "__main__":
    args = parse_args()
    main(args)
