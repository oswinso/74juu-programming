from programming.generate import *
from typing import Tuple

name = "Simple_ALU_Test"


def get_instructions() -> Tuple[uCode, uInstruction]:
    code = {
        Opcode(0): alu_check()
    }
    default = go_to_first()
    return code, default


def alu_check() -> uInstruction:
    code: uInstruction = [
        reset_alu_a(),  # A=0, B=X
        reset_alu_b(),  # A=0, B=0
        modify_step(add_and_write_a(), "set A to one", set_cin),  # A=1, B=0
        add_and_write_b(),  # A=1, B=1
        alu_shift_sum_left_a(),  # A=2, B=1
        alu_shift_sum_left_a(),  # A=4, B=1
        add_and_write_b(),  # A=004, B=0005
        get_result("XOR and write to A", alu_xor, alu_read, write_alu_a),  # A=0001, B=0005
        get_result("a - b, write to a", alu_subtract_a_minus_b, alu_read, write_alu_a),  # A = -4 <=> FFFC, B = 0005
        get_result("a or b, write to b", alu_or, alu_read, write_alu_b)  # A = FFFC, B = FFFD
    ]
    return code


def main():
    save_instruction_set(name, *get_instructions())


if __name__ == "__main__":
    main()
