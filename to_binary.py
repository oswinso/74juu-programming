import re
import binascii

header = "74juuxxx"
footer = "lmaofter"
OPCODE_SIZE = 2**6
COUNTER_SIZE = 2**7


def control_bits_to_bytes(control_bits):
    # print("_________")
    # bits = control_bits + "0"*(8-len(control_bits)%8)
    # print(bits)
    # for pos in range(len(bits)//8):
    #     print(bits[pos*8:pos*8+8])
    # print("_________")
    # return 0
    print(control_bits[::-1])
    print(int(control_bits[::-1], 2))
    byte = int(control_bits[::-1], 2).to_bytes((len(control_bits) + 7) // 8, 'little')
    return byte


def to_binary(filename):
    output = bytearray(header, 'ascii')
    print(output)
    with open(f'{filename}.instr', "r") as file:
        text = file.read()
        name = re.search(r'INSTRUCTION SET NAME: (.*)\n', text, re.M).group(1)
        print(f'Name: {name}')
        default_steps = re.search(r'DEFAULT:\n((?:.*\n)+?)\n', text).group(1).strip()
        print("Default:")
        default = 0
        for counter, line in enumerate(default_steps.split("\n")):
            control_bits = line.split("\t")[1]
            control_bits = control_bits[1:-1].replace(", ","")
            default = control_bits_to_bytes(control_bits)
        print(binascii.hexlify(default))

        instruction_dict = {}
        instructions = re.findall(r'([0-9A-F]{4}):\n((?:.+\n)+)\n', text)
        print("instructions: ", instructions)
        for (opcode_hex, instruction) in instructions:
            opcode = int(opcode_hex, 16)
            print("instruction: ", opcode, " - ", instruction)
            instruction_dict[opcode] = []
            for counter, line in enumerate(instruction.strip().split("\n")):
                control_bits = line.split("\t")[1]
                control_bits = control_bits[1:-1].replace(", ","")
                instruction_dict[opcode].append(control_bits_to_bytes(control_bits))
        print(instruction_dict)

        for opcode in range(OPCODE_SIZE):
            if opcode in instruction_dict:
                for i in range(COUNTER_SIZE):
                    if i < len(instruction_dict[opcode]):
                        output += instruction_dict[opcode][i]
                    else:
                        output += default
            else:
                for i in range(COUNTER_SIZE):
                    output += default
        output += bytearray(footer, "ascii")
    with open(f'{filename}.bin', 'wb') as file:
        file.write(output)


def from_binary(filename):
    with open(f'{filename}.bin', 'rb') as file:
        data = file.read()
        if data[0:8] != b'74juuxxx':
            print(data[0:8], " is not ", b'74juuxxx')
            print("Incorrect header.")
            exit(1)
        if data[-8:] != b'lmaofter':
            print(data[-8:], " is not ", b'lmaofter')
            print(data[-8:])
            print("Incorrect footer")
            exit(2)
        if len(data) != OPCODE_SIZE*COUNTER_SIZE*5+2*8:
            print("Incorrect binary size")
            exit(3)
        for i in range(OPCODE_SIZE*COUNTER_SIZE):
            raw_control_bits = data[i*5+8:i*5+5+8]
            int_form = int.from_bytes(raw_control_bits, byteorder='little')
            control_bits = f'{int_form:0{40}b}'
            print(f'{i*5+8:04x}', ":", f'{i*5+5+8:04x}', " -> ", binascii.hexlify(raw_control_bits), " = ", control_bits[::-1])


def main():
    to_binary("Hello_World")
    from_binary("Hello_World")


if __name__ == "__main__":
    main()
