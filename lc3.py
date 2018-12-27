from programming.generate import *
from typing import Tuple

name = "LC3_Clone"


def get_instructions() -> Tuple[uCode, uInstruction]:
    code = {
        Opcode(0): fetch_instruction(),
        Opcode(1): add_reg_reg(),
        Opcode(2): add_reg_imm(),
        Opcode(3): logical_and_reg_reg(),
        Opcode(4): logical_and_reg_imm(),
        Opcode(5): jeq(),
        Opcode(6): jump(),
        Opcode(7): call_offset(),
        Opcode(8): call_reg(),
        Opcode(9): mov_reg_offset(),
        Opcode(10): mov_reg_imm(),
        Opcode(11): load_effective_address(),
        Opcode(12): not_reg_reg(),
        Opcode(13): ret(),
        Opcode(14): interrupt_ret(),
        Opcode(15): mov_offset_reg(),
        Opcode(16): mov_indirect_reg(),
        Opcode(17): mov_reg_reg_offset(),
        # Opcode(18): trap() # Rip can't do software traps
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
