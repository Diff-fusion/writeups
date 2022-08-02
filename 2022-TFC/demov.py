from capstone import *
from capstone.x86 import *
from elftools.elf.elffile import ELFFile

# load ELF
f = open("./one", "rb")
e = ELFFile(f)
code = e.get_section_by_name(".text")
ops = code.data()
addr = code["sh_addr"]
# init disassembler
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# disassemble all instructions
instructions = list(md.disasm(ops, addr))
addr_to_index = {}
for i, ins in enumerate(instructions):
    addr_to_index[ins.address] = i

class OpMatch:
    def __init__(
        self,
        type=None,
        reg=None,
        imm=None,
        mem_segment=None,
        mem_base=None,
        mem_index=None,
        mem_scale=None,
        mem_disp=None,
    ):
        if type == X86_OP_REG or reg is not None:
            self.reg = reg
            self.type = X86_OP_REG
        if type == X86_OP_IMM or imm is not None:
            self.imm = imm
            self.type = X86_OP_IMM
        if (
            type == X86_OP_MEM
            or mem_segment is not None
            or mem_base is not None
            or mem_index is not None
            or mem_scale is not None
            or mem_disp is not None
        ):
            self.mem_segment = mem_segment
            self.mem_base = mem_base
            self.mem_index = mem_index
            self.mem_scale = mem_scale
            self.mem_disp = mem_disp
            self.type = X86_OP_MEM

        if not self.type:
            print("Could not infere type")

    def match(self, op):
        if self.type != op.type:
            return False

        if self.type == X86_OP_REG:
            if self.reg is not None and self.reg != op.value.reg:
                return False
        elif self.type == X86_OP_IMM:
            if self.imm is not None and self.imm != op.value.imm:
                return False
        elif self.type == X86_OP_MEM:
            if self.mem_segment is not None and self.mem_segment != op.value.mem.segment:
                return False
            if self.mem_base is not None and self.mem_base != op.value.mem.base:
                return False
            if self.mem_index is not None and self.mem_index != op.value.mem.index:
                return False
            if self.mem_scale is not None and self.mem_scale != op.value.mem.scale:
                return False
            if self.mem_disp is not None and self.mem_disp != op.value.mem.disp:
                return False

        return True


subb = False


def match(start, expr):
    global subb
    if subb:
        print("In sub")
        print(expr)
    cursor = start
    expr_c = 0
    repeat = False
    while True:
        if not repeat:
            opm1, opm2 = expr[expr_c]
        ins = instructions[cursor]
        if ins.mnemonic != "mov":
            # print("Invalid instruction")
            return False, cursor
        # print(f"0x{ins.address:x}:\t{ins.mnemonic}\t{ins.op_str}")

        op1, op2 = ins.operands

        if opm1 == "multi":
            for path in opm2:
                # subb = True
                found, cursor = match(cursor, path)
                subb = False
                if found:
                    break
            else:
                return False, cursor
            expr_c += 1
            if expr_c >= len(expr) or cursor >= len(instructions):
                break
            continue
        if opm1 == "repeat":
            opm1, opm2 = opm2
            repeat = True

        if subb:
            print(ins.op_str)
            print(cursor)

        if opm1:
            if opm1.match(op1):
                # print("Match1")
                pass
            else:
                if repeat:
                    cursor -= 1
                    repeat = False
                    opm2 = None
                else:
                    return False, cursor

        if opm2:
            if opm2.match(op2):
                # print("Match2")
                pass
            else:
                if repeat:
                    cursor -= 1
                    repeat = False
                else:
                    return False, cursor

        cursor += 1
        if not repeat:
            expr_c += 1
        if expr_c >= len(expr) or cursor >= len(instructions):
            break
    return True, cursor


def find(start, expr):
    count = 0
    for ins in instructions[start:]:
        # if count > 100:
        #     break
        # print(f"0x{ins.address:x}:\t{ins.mnemonic}\t{ins.op_str}")
        found, index = match(addr_to_index[ins.address], expr)
        if found:
            # print("Index of found:", index)
            return True, addr_to_index[ins.address], index

        count += 1
    return False, 0, 0


ALU_X = 0x8274690
ALU_Y = 0x8274694

op_select_data = (
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(type=X86_OP_REG), OpMatch(mem_base=0, mem_scale=4)),
)

op_on = (
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0, mem_index=X86_REG_EAX, mem_scale=4)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(imm=1)),
)
op_off = (
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0, mem_index=X86_REG_EAX, mem_scale=4)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(imm=0)),
)

op_load_jmp_regs1 = (
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_IMM)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0, mem_index=X86_REG_ECX, mem_scale=4)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(mem_base=0)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(reg=X86_REG_EDX)),
)
op_load_jmp_regs2 = (
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_load_jmp_regs3 = (
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_load_jmp_regs = (
    (OpMatch(reg=X86_REG_ECX), OpMatch(mem_base=0)),
    *op_load_jmp_regs1,
    *op_load_jmp_regs1,
    *op_load_jmp_regs1,
    *op_load_jmp_regs1,
    *op_load_jmp_regs2,
    *op_load_jmp_regs2,
    *op_load_jmp_regs2,
    *op_load_jmp_regs3,
    *op_load_jmp_regs3,
    *op_load_jmp_regs3,
)

op_execution_on = (
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(imm=1)),
)

op_push = (
    (OpMatch(reg=X86_REG_EAX), None),
    (OpMatch(mem_base=0), OpMatch(reg=X86_REG_EAX)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(type=X86_OP_IMM)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(mem_base=0)),
    *op_select_data,
    #
    (OpMatch(reg=X86_REG_EDX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(type=X86_OP_MEM)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(reg=X86_REG_EDX)),
    (None, None),
    (None, None),
    *op_select_data,
    #
    (None, None),
    (None, None),
)

op_pushm8 = (
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    *op_select_data,
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    *op_select_data,
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_bool = (
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_eq = (
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(reg=X86_REG_EAX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_ECX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_AL), OpMatch(type=X86_OP_MEM)),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    *op_bool,
    *op_bool,
    *op_bool,
    (None, None),
    (OpMatch(mem_base=0), OpMatch(reg=X86_REG_EAX)),
)

op_add16_fast = (
    (OpMatch(reg=X86_REG_AX), None),
    (OpMatch(reg=X86_REG_CX), None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_add = (
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    # add32
    (OpMatch(reg=X86_REG_EAX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_ECX), OpMatch(imm=0)),
    (OpMatch(mem_base=0), OpMatch(imm=0)),
    *op_add16_fast,
    *op_add16_fast,
    #
    (OpMatch(type=X86_OP_REG), OpMatch(mem_base=0)),
)


op_sub16_fast = (
    (OpMatch(reg=X86_REG_AX), None),
    (OpMatch(reg=X86_REG_CX), None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),
)

op_sub32 = (
    # add32
    (OpMatch(reg=X86_REG_EAX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_ECX), OpMatch(imm=0)),
    (OpMatch(mem_base=0), OpMatch(imm=1)),
    *op_sub16_fast,
    *op_sub16_fast,
)

op_sub = (
    (OpMatch(mem_base=0, mem_disp=ALU_X), OpMatch(type=X86_OP_REG)),
    (OpMatch(mem_base=0, mem_disp=ALU_Y), OpMatch(type=X86_OP_REG)),
    *op_sub32,
    (OpMatch(type=X86_OP_REG), OpMatch(mem_base=0)),
)

op_bxor8 = (
    (OpMatch(reg=X86_REG_EAX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(imm=0)),
    (OpMatch(reg=X86_REG_AL), None),
    (OpMatch(reg=X86_REG_DL), None),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_AL), None),
    # (None, OpMatch(reg=X86_REG_AL)),
)

op_cmp = (
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    (OpMatch(mem_base=0), OpMatch(type=X86_OP_REG)),
    *op_sub32,
)

op_function = (
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(type=X86_OP_IMM)),
    *op_eq,
    *op_load_jmp_regs,
    *op_execution_on,
    *op_push,
    # push register
    *op_push,
    *op_push,
    *op_push,
    *op_push,
    *op_push,
    *op_pushm8,
    *op_pushm8,
    (None, None),
    (None, None),
    *op_select_data,
    (None, None),
    (None, None),
    (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=0)),
    (
        "multi",
        (
            (
                ("repeat", (OpMatch(reg=X86_REG_EAX), OpMatch(mem_base=X86_REG_EAX))),
                (OpMatch(mem_base=0), OpMatch(reg=X86_REG_EAX)),
            ),
            (
                (OpMatch(reg=X86_REG_EDX), OpMatch(type=X86_OP_IMM)),
                *op_add,
                (OpMatch(mem_base=0), OpMatch(reg=X86_REG_EAX)),
            ),
        ),
    ),
    (OpMatch(reg=X86_REG_EAX), OpMatch(type=X86_OP_IMM)),
    (OpMatch(reg=X86_REG_EDX), OpMatch(mem_base=0)),
    *op_select_data,
    (OpMatch(reg=X86_REG_EDX), OpMatch(mem_base=0)),
    (OpMatch(mem_base=X86_REG_EAX), OpMatch(reg=X86_REG_EDX)),
)

# first instruction
i_iter = iter(instructions)
inst = next(i_iter)
assert inst.mnemonic == "mov"
assert inst.operands[1].value.reg == 30  # reg is esp

cursor = 1
match_counter = 0

cursor = addr_to_index[0x08060700]
bb_end = addr_to_index[0x0806664D]
while True:
    i = instructions[cursor]
    # print(f"0x{i.address:x}:\t{i.mnemonic}\t{i.op_str}")
    expr = op_cmp
    found, start, end = find(cursor, expr)
    if start > bb_end:
        break
    cursor = end
    if found:
        # print("FOUND!")
        match_counter += 1
        idx = start
        # idx = end
        for ins in instructions[idx : idx + 1]:
            print(f"0x{ins.address:x}:\t{ins.mnemonic}\t{ins.op_str}")
        continue
    break

print(match_counter)
