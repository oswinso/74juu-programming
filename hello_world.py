from programming import generate
from typing import Tuple


name = "Hello_World"


def get_instructions() -> Tuple[generate.uCode, generate.uInstruction]:
    code = {
        generate.Opcode(0): generate.output_alu_one()
    }
    default = generate.go_to_first()
    return code, default


def main():
    generate.save_instruction_set(name, *get_instructions())


if __name__ == "__main__":
    main()
