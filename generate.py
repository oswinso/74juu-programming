from typing import Dict, List, Tuple, NewType, Callable
import numpy as np
import functools

# 6 bits opcode, 7 bits counter

ControlBit = NewType('ControlBit', int)
uStep = np.ndarray
CommentedStep = Tuple[uStep, str]

uInstruction = List[CommentedStep]

Opcode = NewType('Opcode', int)
Operation = NewType('Operation', Callable[[uStep], uStep])
uCode = Dict[Opcode, uInstruction]

# Control Bits
NEG_uIR_W = ControlBit(0)
NEG_Out_W = ControlBit(1)
NEG_MEM_R = ControlBit(2)
NEG_MEM_W = ControlBit(3)
NEG_MAR_W = ControlBit(4)

NEG_SEG_EN = ControlBit(6)
SEG_W = ControlBit(7)

NEG_REG_EN = ControlBit(8)
REG_W = ControlBit(9)

JUMP_INTR_EN = ControlBit(5)
JUMP_SEL = np.array([ControlBit(32), ControlBit(33), ControlBit(34), ControlBit(35)])

CIN = ControlBit(21)
ALU_S = np.array([ControlBit(19), ControlBit(18), ControlBit(17)])  # LSB on right
SEG_SEL = np.array([ControlBit(37), ControlBit(36)])

ADDR_MODE = np.array([ControlBit(23), ControlBit(22)])

NEG_ALU_B_W = ControlBit(13)
NEG_ALU_A_W = ControlBit(14)

ALU_SHIFT_RIGHT = ControlBit(15)
ALU_SHIFT_LEFT = ControlBit(16)

NEG_ALU_R = ControlBit(20)

CLK_ENABLE = ControlBit(30)
HALT = ControlBit(28)
CLK_LOAD = ControlBit(29)

NEG_uPC_CLEAR = ControlBit(31)

IR_W = ControlBit(37)


class ALU:
    CLEAR = np.array([0, 0, 0])
    B_MINUS_A = np.array([0, 0, 1])
    A_MINUS_B = np.array([0, 1, 0])
    ADD = np.array([0, 1, 1])
    XOR = np.array([1, 0, 0])
    OR = np.array([1, 0, 1])
    AND = np.array([1, 0, 1])


class SEG:
    CS = np.array([0, 0])
    IP = np.array([0, 0])
    DS = np.array([0, 0])
    ES = np.array([0, 0])


class ADDR:
    NONE = np.array([0, 0])
    REG_REG = np.array([0, 1])
    REG_VAL = np.array([1, 0])
    VAL = np.array([1, 1])


do_nothing = np.array([
    1,  # 0     -uir_w
    1,  # 1     ~out_W
    1,  # 2     ~mem_R
    1,  # 3     ~mem_W
    1,  # 4     ~mar_W
    0,  # 5
    1,  # 6     ~seg_en
    0,  # 7     seg_w
    1,  # 8     ~reg_en
    0,  # 9     reg_w
    1,  # 10    ~flag_w
    0,  # 11    flag_sel_bus
    1,  # 12    ~flag_re
    1,  # 13    ~alu_b_w
    1,  # 14    ~alu_a_w
    0,  # 15    shift_right
    0,  # 16    shift_left
    0,  # 17    alu_s0
    0,  # 18    alu_s1
    0,  # 19    alu_s2
    1,  # 20    ~alu_re
    0,  # 21    cin
    0,  # 22    addr_mode0
    0,  # 23    addr_mode1
    0,  # 24    reg_sel
    1,  # 25    ~jump_re
    0,  # 26    inta
    1,  # 27    ~int_re
    0,  # 28    halt
    0,  # 29    empty
    0,  # 30    empty
    1,  # 31    ~uPC_Clear
    0,  # 32    jsel0
    0,  # 33    jsel1
    0,  # 34    jsel2
    0,  # 35    jsel3
    0,  # 36    SEG_SEL0
    0,  # 37    SEG_SEL1
    0,  # 38    IR_W
    0   # 39    empty
])


def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def get_result(comment: str = "", original=None, *functions: Operation) -> CommentedStep:
    if original is None:
        original = base()
    composed = compose(*functions)
    return composed(original), comment


def modify_step(step: CommentedStep, comment: str = None, *functions: Operation) -> CommentedStep:
    if comment is None:
        comment = step[1]
    return get_result(comment, step[0], functions)


def base():
    return do_nothing.copy()


def fetch_instruction() -> uInstruction:
    code: uInstruction = [
        get_result("Write IP to ALU A", ip_read, write_alu_a),
        get_result("Write CS to ALU B", cs_read, write_alu_b),
        get_result("Write sum to MAR", alu_add, write_mar),
        reset_alu_b(),
        get_result("Increment IP", set_cin, alu_add, ip_write),
        get_result("Read instructions from memory, write to IR", read_memory, write_IR),
        get_result("Write from IR to uIR, reset uPC", write_uIR, clear_uPC)
    ]
    return code


def add_reg_reg() -> uInstruction:
    code: uInstruction = [
        get_result("Read source register into ALU A", )
    ]


def go_to_first() -> uInstruction:
    """Read bus (all 0s) to uIP, clear uPC"""
    code: uInstruction = [
        get_result("Write 0 to IR", write_IR),
        get_result("Write IR to uIR, clear uPC", write_uIR, clear_uPC)]
    return code


def output_alu_one() -> uInstruction:
    code: uInstruction = [
        *get_one(),
        get_result("Halt, repeat previous to prevent reset", set_cin, alu_add, halt)]
    return code


def get_one() -> uInstruction:
    code: uInstruction = [
        reset_alu_a(),
        reset_alu_b(),
        get_result("Add A and B with Carry In", set_cin, alu_add)]
    return code


def add_and_write_a() -> CommentedStep:
    return get_result("Save sum to A", alu_add, alu_read, write_alu_a)


def add_and_write_b() -> CommentedStep:
    return get_result("Save sum to B", alu_add, alu_read, write_alu_b)


def reset_alu_a() -> CommentedStep:
    return get_result("Set ALU A to 0", write_alu_a)


def reset_alu_b() -> CommentedStep:
    return get_result("Set ALU B to 0", write_alu_b)


def alu_shift_sum_left_a() -> CommentedStep:
    return modify_step(add_and_write_a(), "Shift sum left, write to A", alu_shift_left)


def alu_shift_sum_right_a() -> CommentedStep:
    return modify_step(add_and_write_a(), "Shift sum left, write to A", alu_shift_right)


def write_mar(step: uStep) -> uStep:
    step[NEG_MAR_W] = 0
    return step


def read_memory(step: uStep) -> uStep:
    step[NEG_MEM_R] = 0
    return step


def write_memory(step: uStep) -> uStep:
    step[NEG_MEM_W] = 0
    return step


def write_alu_a(step: uStep) -> uStep:
    step[NEG_ALU_A_W] = 0
    return step


def write_alu_b(step: uStep) -> uStep:
    step[NEG_ALU_B_W] = 0
    return step


def set_cin(step: uStep) -> uStep:
    step[CIN] = 1
    return step


def alu_add(step: uStep) -> uStep:
    step[ALU_S] = ALU.ADD
    return step


def alu_subtract_a_minus_b(step: uStep) -> uStep:
    step[ALU_S] = ALU.A_MINUS_B
    step[CIN] = 1
    return step


def alu_subtract_b_minus_a(step: uStep) -> uStep:
    step[ALU_S] = ALU.B_MINUS_A
    step[CIN] = 1
    return step


def alu_xor(step: uStep) -> uStep:
    step[ALU_S] = ALU.XOR
    return step


def alu_or(step: uStep) -> uStep:
    step[ALU_S] = ALU.OR
    return step


def alu_and(step: uStep) -> uStep:
    step[ALU_S] = ALU.AND
    return step


def alu_shift_left(step: uStep) -> uStep:
    step[ALU_SHIFT_LEFT] = 1
    return step


def alu_shift_right(step: uStep) -> uStep:
    step[ALU_SHIFT_RIGHT] = 1
    return step


def alu_read(step: uStep) -> uStep:
    step[NEG_ALU_R] = 0
    return step


def clk_enable(step: uStep) -> uStep:
    step[CLK_ENABLE] = 1
    return step


def write_IR(step: uStep) -> uStep:
    step[IR_W] = 1
    return step


def ip_write(step: uStep) -> uStep:
    step[SEG_SEL] = SEG.IP
    step[SEG_W] = 1
    step[NEG_SEG_EN] = 0
    return step


def ip_read(step: uStep) -> uStep:
    step[SEG_SEL] = SEG.IP
    step[SEG_W] = 0
    step[NEG_SEG_EN] = 0
    return step


def cs_write(step: uStep) -> uStep:
    step[SEG_SEL] = SEG.CS
    step[SEG_W] = 1
    step[NEG_SEG_EN] = 0
    return step


def cs_read(step: uStep) -> uStep:
    step[SEG_SEL] = SEG.CS
    step[SEG_W] = 0
    step[NEG_SEG_EN] = 0
    return step


def halt(step: uStep) -> uStep:
    step[HALT] = 1
    return step


def write_uIR(step: uStep) -> uStep:
    step[NEG_uIR_W] = 0
    return step


def clear_uPC(step: uStep) -> uStep:
    step[NEG_uPC_CLEAR] = 0
    return step


def save_instruction_set(instruction_name: str, instructions: uCode, default: uInstruction):
    out = ""
    out += f'INSTRUCTION SET NAME: {instruction_name}\n'
    out += "\nDEFAULT:\n"
    for counter, (control_bits, comment) in enumerate(default):
        out += f'{counter:0{2}x}\t{control_bits.tolist()}\t{comment}\n'

    out += "\nINSTRUCTIONS:\n"
    for opcode, steps in instructions.items():
        out += f'{opcode:0{4}x}:\n'
        for counter, (step, comment) in enumerate(steps):
            out += f'{counter:0{2}x}\t{step.tolist()}\t{comment}\n'
        out += '\n'
    with open(f'{instruction_name}.instr', 'w') as file:
        file.write(out)
