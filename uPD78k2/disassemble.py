
class IllegalInstructionError(Exception):
    pass


class FlowTypes(object):
    Continue = 0
    Stop = 1
    UnconditionalJump = 2
    IndirectUnconditionalJump = 3
    ConditionalJump = 4
    SubroutineCall = 5
    SubroutineReturn = 6

class ArgumentTypes(object):
    ReferencedAddress = 1
    TargetAddress = 2

class Instruction(object):
    def __init__(self, asm, asm_args, flow_type, opcode, operands):
        self.asm = asm
        self.asm_args = asm_args
        self.flow_type = flow_type
        self.opcode = opcode
        self.operands = operands

    def __len__(self):
        return len(self.opcode) + len(self.operands)

    def __str__(self):
        return self.asm

    def to_string(self, symbols=None):
        if symbols is None:
            symbols = {}  # address: (name, comment)

        addresses = []
        for a, _ in self.asm_args:
            address = eval('0x'+a)
            if address in symbols:
                name, comment = symbols[address]
                addresses.append(name)
            else:
                addresses.append(address)

        return self.asm.format(*addresses)

    @property
    def all_bytes(self):
        return list(self.opcode) + list(self.operands)

    @property
    def referenced_addresses(self):
        '''Return all addresses that are read, written, or branched
        by the instruction.  For indirect or relative addresses, only
        the target is returned.'''
        addresses = []
        for address, arg_type in self.asm_args:
            if arg_type == ArgumentTypes.ReferencedAddress:
                addresses.append(eval('0x'+address))

        return addresses

    @property
    def target_address(self):
        '''Return the branch target address, or None if instruction cannot branch'''
        for address, arg_type in self.asm_args:
            if arg_type == ArgumentTypes.TargetAddress:
                return eval('0x'+address)

        return None

def _reg(opcode):
    r = opcode & 0b111
    return ('X', 'A', 'C', 'B', 'E', 'D', 'L', 'H')[r]

def _regpair(opcode):
    rp = (opcode >> 1) & 0b11
    return ('AX', 'BC', 'DE', 'HL')[rp]

def _saddr(low):
    saddr = 0xfe00 + low
    return saddr

def _sfr(low):
    sfr = 0xff00 + low
    return sfr

def _mem_indirect(mem):
    mem = mem & 0b111
    try:
        return ('[DE+]', '[HL+]', '[DE-]', '[HL-]', '[DE]', '[HL]')[mem]
    except IndexError as exc:
        raise IllegalInstructionError("Illegal mem for adressing mode") from exc

def _mem_base(mem):
    mem = mem & 0b111
    try:
        return ('[DE+0x%02x]', '[SP+0x%02x]', '[HL+0x%02x]')[mem]
    except IndexError as exc:
        raise IllegalInstructionError("Illegal mem for adressing mode") from exc

def _mem_indexed(mem):
    mem = mem & 0b111
    try:
        return ('0x%04x [DE]', '0x%04x [A]', '0x%04x [HL]', '0x%04x [B]')[mem]
    except IndexError as exc:
        raise IllegalInstructionError("Illegal mem for adressing mode") from exc
        
def _mem1(opcode):
    return ("[DE]","[HL]")[opcode & 0x01]

def _math_ops(opcode):
    op = opcode & 0x07
    return ("ADD", "ADDC", "SUB", "SUBC", "AND", "XOR", "OR", "CMP")[op]

def _math_ops(opcode):
    op = opcode & 0x07
    return ("ADD", "ADDC", "SUB", "SUBC", "AND", "XOR", "OR", "CMP")[op]

def _math_opsW(opcode):
    op = opcode & 0x03
    return ("ADDW", "ADDW", "SUBW", "CMPW")[op]

def _addr16(low, high):
    return low + (high << 8)

def _addr16p(low, high):
    addr16p = low + (high << 8)
    if addr16p & 1 != 0:
        raise IllegalInstructionError("addr16p must be an even address")
    return addr16p

def _I8(param):
    return  "%02x" % param

def _I11(param):
    return  "%03x" % param

def _I16(param):
    return  "%04x" % param

def disassemble(rom, pc):
    inst = None

    asm_args = ()
    flow_type=FlowTypes.Continue
    opcodes = [rom[pc]]
    operands=()
    
    mem_prefix=''
    if opcodes[0] == 0x01: #FIXME: should check for illegal usage of 0x1
        pc = pc + 1
        opcodes.append(rom[pc])
        mem_prefix='&'

    # NOP
    if rom[pc] == 0b00000000:
        asm = "nop"

    # MOV STBC, #byte
    elif (rom[pc] == 0b00001001) and (rom[pc+1] == 0b11000000):
        byte = _I8(rom[pc+3])
        asm = f"MOV STBC, #{byte}"
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # SEL RBn
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xfc) == 0b10101000):
        bank = rom[pc+1] & 0x03
        asm = f"SEL RB{bank}"
        operands=(rom[pc+1], )

    # EI/DI
    elif (rom[pc] & 0xfe) == 0b01001010:
        asm = ("DI", "EI")[rom[pc] & 0x01]
    
    # MOV r, #byte
    elif (rom[pc] & 0xf8) == 0b10111000:
        r = _reg(rom[pc])
        byte = _I8(rom[pc+1])
        asm = f"MOV {r}, #{byte}"
        operands=(rom[pc+1],)

    # MOV saddr, #byte
    elif rom[pc] == 0b00111010:
        saddr = _I16(_saddr(rom[pc+1]))
        byte = _I8(rom[pc+2])
        asm = f"MOV {{0}}, #{byte}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # MOV sfr, #byte
    elif rom[pc] == 0b00101011:
        sfr  = _I16(_sfr(rom[pc+1]))
        byte = _I8(rom[pc+2])
        asm = f"MOV {{0}}, #{byte}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # MOV r, r’
    elif (rom[pc] == 0b00100100) and ((rom[pc+1] & 0x88) == 0x00):
        rp = _reg(rom[pc+1])
        r = _reg(rom[pc+1] >> 4)
        asm = f"MOV {r}, {rp}"
        operands=(rom[pc+1],)

    # MOV A, r
    elif (rom[pc] & 0xf8) == 0b11010000:
        r = _reg(rom[pc])
        asm = f"MOV A, {r}"

    # MOV A, saddr
    elif rom[pc] == 0b00100000:
        saddr  = _I16(_saddr(rom[pc+1]))
        asm = f"MOV A, {{0}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOV saddr, A
    elif rom[pc] == 0b00100010:
        saddr = _I16(_saddr(rom[pc+1]))
        asm = f"MOV {{0}}, A"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOV A, sfr
    elif rom[pc] == 0b00010000:
        sfr  = _I16(_sfr(rom[pc+1]))
        asm = f"MOV A, {{0}}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOV sfr, A
    elif rom[pc] == 0b00010010:
        sfr  = _I16(_sfr(rom[pc+1]))
        asm = f"MOV {{0}}, A"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOV saddr, saddr’
    elif rom[pc] == 0b00111000:
        saddr  = _I16(_saddr(rom[pc+1]))
        saddrp = _I16(_saddr(rom[pc+2]))
        asm = f"MOV {{0}}, {{1}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # MOV A, mem and MOV A, &mem (short 1/2B code)
    elif ((rom[pc] & 0xf8) == 0b01011000) and ((rom[pc] & 0x07) < 6):
        asm = f"MOV A, {mem_prefix}{_mem_indirect(rom[pc])}"

    # MOV A, mem and MOV A, &mem
    elif rom[pc] in (0b00010110, 0b00000110, 0b00001010) and ((rom[pc+1] & 0x8f) == 0b00000000):
        if rom[pc] == 0b00010110:
            mem = _mem_indirect(rom[pc+1] >> 4)
            operands=(rom[pc+1],)
        elif rom[pc] == 0b00000110:
            mem = _mem_base(rom[pc+1] >> 4) % rom[pc+2]
            operands=(rom[pc+1], rom[pc+2])
        elif rom[pc] == 0b00001010:
            mem = _mem_indexed(rom[pc+1] >> 4) % _addr16p(rom[pc+2], rom[pc+3])
            operands=(rom[pc+1], rom[pc+2], rom[pc+3])
        else:
            raise IllegalInstructionError(f"Illegal opcode 0x{rom[pc]:02x} at 0x{pc:04x}")
        asm = f"MOV A, {mem_prefix}{mem}"

    # MOV mem, A and MOV &mem, A (short 1/2B code)
    elif ((rom[pc] & 0xf8) == 0b01010000) and ((rom[pc] & 0x07) < 6):
        asm = f"MOV {mem_prefix}{_mem_indirect(rom[pc])}, A"

    # MOV mem, A and MOV &mem, A
    elif rom[pc] in (0b00010110, 0b00000110, 0b00001010)  and ((rom[pc+1] & 0x8f) == 0b10000000):
        if rom[pc] == 0b00010110:
            mem = _mem_indirect(rom[pc+1] >> 4)
            operands=(rom[pc+1],)
        elif rom[pc] == 0b00000110:
            mem = _mem_base(rom[pc+1] >> 4) % rom[pc+2]
            operands=(rom[pc+1], rom[pc+2])
        elif rom[pc] == 0b00001010:
            mem = _mem_indexed(rom[pc+1] >> 4) % _addr16p(rom[pc+2], rom[pc+3])
            operands=(rom[pc+1], rom[pc+2], rom[pc+3])
        else:
            raise IllegalInstructionError(f"Illegal opcode 0x{rom[pc]:02x} at 0x{pc:04x}")
        asm = f"MOV {mem_prefix}{mem}, A"

    # MOV A, !addr16 and MOV A, &!addr16
    elif (rom[pc] == 0b00001001) and (rom[pc+1] == 0b11110000):
        addr16 = _I16(_addr16(rom[pc+2], rom[pc+3]))
        asm = f"MOV A, {mem_prefix}!{{0}}"
        asm_args = (
            (addr16, ArgumentTypes.ReferencedAddress),
        )
        opcodes.append(rom[pc+1])
        operands=(rom[pc+2], rom[pc+3])

    # MOV !addr16, A and MOV &!addr16, A
    elif (rom[pc] == 0b00001001) and (rom[pc+1] == 0b11110001):
        addr16 = _I16(_addr16(rom[pc+2], rom[pc+3]))
        asm = f"MOV {mem_prefix}!{{0}}, A"
        asm_args = (
            (addr16, ArgumentTypes.ReferencedAddress),
        )
        opcodes.append(rom[pc+1])
        operands=(rom[pc+2], rom[pc+3])

    # MOV PSW, #byte
    elif (rom[pc] == 0b00101011) and (rom[pc+1] == 0b11111110):
        byte = _I8(rom[pc+2])
        asm = f"MOV PSW, {byte}"
        opcodes.append(rom[pc+1])
        operands=(rom[pc+2],)

    # MOV PSW, A
    elif (rom[pc] == 0b00010010) and (rom[pc+1] == 0b11111110):
        asm = "MOV PSW, A"
        opcodes.append(rom[pc+1])

    # MOV A, PSW
    elif (rom[pc] == 0b00010000) and (rom[pc+1] == 0b11111110):
        asm = "MOV A, PSW"
        opcodes.append(rom[pc+1])

    # XCH r, r’
    elif (rom[pc] == 0b00100101) and ((rom[pc+1] & 0x88) == 0x00):
        rp = _reg(rom[pc+1])
        r = _reg(rom[pc+1] >> 4)
        asm = f"XCH {r}, {rp}"
        operands=(rom[pc+1],)

    # XCH A, r
    elif (rom[pc] & 0xf8) == 0b11011000:
        r = _reg(rom[pc])
        asm = f"XCH A, {r}"

    # XCH A, saddr and XCH A, sfr
    elif rom[pc] == 0b00100001:
        if opcodes[0] == 0b00000001:
            sfr = _I16(_sfr(rom[pc+1]))
            asm = f"XCH A, {{0}}"
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        else:
            saddr = _I16(_saddr(rom[pc+1]))
            asm = f"XCH A, {{0}}"
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        operands=(rom[pc+1],)

    # XCH saddr, saddr’
    elif rom[pc] == 0b00111001:
        saddr = _I16(_saddr(rom[pc+1]))
        saddrp = _I16(_saddr(rom[pc+2]))
        asm = f"XCH {{0}}, {{1}}"
        asm_args = (
            (saddr , ArgumentTypes.ReferencedAddress),
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # XCH A, mem and XCH A, &mem
    elif rom[pc] in (0b00010110, 0b00000110, 0b00001010) and ((rom[pc+1] & 0x8f) == 0b00000100):
        if rom[pc] == 0b00010110:
            mem = _mem_indirect(rom[pc+1] >> 4)
            operands=(rom[pc+1],)
        elif rom[pc] == 0b00000110:
            mem = _mem_base(rom[pc+1] >> 4) % rom[pc+2]
            operands=(rom[pc+1], rom[pc+2])
        elif rom[pc] == 0b00001010:
            mem = _mem_indexed(rom[pc+1] >> 4) % _addr16p(rom[pc+2], rom[pc+3])
            operands=(rom[pc+1], rom[pc+2], rom[pc+3])
        else:
            raise IllegalInstructionError(f"Illegal opcode 0x{rom[pc]:02x} at 0x{pc:04x}")
        asm = f"XCH A, {mem_prefix}{mem}"

    # MOVW rp, #word
    elif (rom[pc] & 0xf8) == 0b01100000:
        rp = _regpair(rom[pc])
        word = _I16(_addr16(rom[pc+1], rom[pc+2]))
        asm = f"MOVW {rp}, #{word}"
        operands=(rom[pc+1], rom[pc+2])

    # MOVW saddrp, #word
    elif rom[pc] == 0b00001100:
        saddrp = _I16(_saddr(rom[pc+1]))
        word = _I16(_addr16(rom[pc+2], rom[pc+3]))
        asm = f"MOVW {{0}}, #{word}"
        asm_args = (
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # MOVW sfrp, #word and MOVW SP, #word
    elif rom[pc] == 0b00001011:
        word = _I16(_addr16(rom[pc+2], rom[pc+3]))
        if rom[pc+1] == 0b11111100:
            asm = f"MOVW SP, #{word}"
        else:
            sfrp = _I16(_sfr(rom[pc+1]))
            asm = f"MOVW {{0}}, #{word}"
            asm_args = (
                (sfrp, ArgumentTypes.ReferencedAddress),
            )
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # MOVW r, r’
    elif (rom[pc] == 0b00100100) and ((rom[pc+1] & 0x99) == 0x08):
        rp = _regpair(rom[pc+1])
        r = _regpair(rom[pc+1] >> 4)
        asm = f"MOVW {r}, {rp}"
        operands=(rom[pc+1],)

    # MOVW AX, saddrp
    elif rom[pc] == 0b00011100:
        saddrp = _I16(_saddr(rom[pc+1]))
        asm = f"MOVW AX, {{0}}"
        asm_args = (
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOVW saddrp, AX
    elif rom[pc] == 0b00011010:
        saddrp = _I16(_saddr(rom[pc+1]))
        asm = f"MOVW {{0}}, AX"
        asm_args = (
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1],)

    # MOVW AX, sfrp/SP and MOVW sfrp/SP, AX
    elif (rom[pc] & 0xfd) == 0b00010001:
        if rom[pc+1] == 0b11111100:
            asm = "MOVW AX, SP" if (rom[pc] & 0x2) == 0 else "MOVW SP, AX"
        else:
            sfrp = _I16(_sfr(rom[pc+1]))
            asm = f"MOVW AX, {{0}}" if (rom[pc] & 0x2) == 0 else f"MOVW {{0}}, AX"
            asm_args = (
                (sfrp, ArgumentTypes.ReferencedAddress),
            )
        operands=(rom[pc+1],)

    # MOVW AX, mem1
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xfe) == 0b11100010):
        mem1 = _mem1(rom[pc+1])
        asm = f"MOVW AX, {mem_prefix}{mem1}"
        operands=(rom[pc+1],)

    # MOVW mem1, AX
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xfe) == 0b11100110):
        mem1 = _mem1(rom[pc+1])
        asm = f"MOVW {mem_prefix}{mem1}, AX"
        operands=(rom[pc+1],)

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP A, #byte
    elif (rom[pc] & 0xf8) == 0b10101000:
        op = _math_ops(rom[pc])
        byte = _I8(rom[pc+1])
        asm = f"{op} A, #{byte}"
        operands=(rom[pc+1],)

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP saddr/sfr, #byte
    elif (rom[pc] & 0xf8) == 0b01101000:
        op = _math_ops(rom[pc])
        byte = _I8(rom[pc+2])
        if opcodes[0] == 0x01:
            sfr = _I16(_sfr(rom[pc+1]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        else:
            saddr = _I16(_saddr(rom[pc+1]))
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"{op} {{0}}, #{byte}"
        operands=(rom[pc+1], rom[pc+2])

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP r, r'
    elif ((rom[pc] & 0xf8) == 0b10001000) and ((rom[pc+1] & 0x88) == 0x00):
        op = _math_ops(rom[pc])
        rp = _reg(rom[pc+1])
        r = _reg(rom[pc+1] >> 4)
        asm = f"{op} {r}, {rp}"
        operands=(rom[pc+1], )

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP A, saddr/sfr
    elif (rom[pc] & 0xf8) == 0b10011000:
        op = _math_ops(rom[pc])
        if opcodes[0] == 0x01:
            sfr = _I16(_sfr(rom[pc+1]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        else:
            saddr = _I16(_saddr(rom[pc+1]))
            asm_args = (
                (saddr,  ArgumentTypes.ReferencedAddress),
            )
        asm = f"{0} A, {1}"
        operands=(rom[pc+1],)

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP A, saddr/saddr'
    elif (rom[pc] & 0xf8) == 0b01111000:
        op = _math_ops(rom[pc])
        saddr = _I16(_saddr(rom[pc+1]))
        saddrp = _I16(_saddr(rom[pc+2]))
        asm = f"{op} {{0}}, {{1}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
            (saddrp, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # ADD/ADDC/SUB/SUBC/AND/OR/XOR/CMP A, mem and &mem
    elif rom[pc] in (0b00010110, 0b00000110, 0b00001010) and ((rom[pc+1] & 0x88) == 0x08):
        op = _math_ops(rom[pc+1])
        if rom[pc] == 0b00010110:
            mem = _mem_indirect(rom[pc+1] >> 4)
            operands=(rom[pc+1],)
        elif rom[pc] == 0b00000110:
            mem = _mem_base(rom[pc+1] >> 4) % rom[pc+2]
            operands=(rom[pc+1], rom[pc+2])
        elif rom[pc] == 0b00001010:
            mem = _mem_indexed(rom[pc+1] >> 4) % _addr16p(rom[pc+2], rom[pc+3])
            operands=(rom[pc+1], rom[pc+2], rom[pc+3])
        else:
            raise IllegalInstructionError(f"Illegal opcode 0x{rom[pc]:02x} at 0x{pc:04x}")
        asm = f"{op} A, {mem_prefix}{mem}"

    # ADDW/SUBW/CMPW AX, #word
    elif rom[pc] in (0b00101101, 0b00101110, 0b00101111):
        op = _math_opsW(rom[pc])
        word = _I16(_addr16(rom[pc+1], rom[pc+2]))
        asm = f"{op} AX, #{word}"
        operands=(rom[pc+1], rom[pc+2])

    # ADDW/SUBW/CMPW AX, rp
    elif rom[pc] in (0b10001000, 0b10001010, 0b10001111) and ((rom[pc+1] & 0xf9) == 0x08):
        op = _math_opsW(rom[pc])
        rp = _regpair(rom[pc+1])
        asm = f"{op} AX, {rp}"
        operands=(rom[pc+1], )

    # ADDW/SUBW/CMPW AX, saddrp/sfrp
    elif rom[pc] in (0b00011101, 0b00011110, 0b00011111):
        op = _math_opsW(rom[pc])
        if opcodes[0] == 0x01:
            sfrp = _I16(_sfr(rom[pc+1]))
            asm_args = (
                (sfrp, ArgumentTypes.ReferencedAddress),
            )
        else:
            saddrp = _I16(_saddr(rom[pc+1]))
            asm_args = (
                (saddrp, ArgumentTypes.ReferencedAddress),
            )
        asm = f"{op} AX, {{0}}"
        operands=(rom[pc+1], )

    # MULU and DIVUW rp
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xe8) == 0x08):
        op = ("MULU", "DIVUW")[(rom[pc+1] >> 4) & 0x1]
        rp = _regpair(rom[pc+1])
        asm = f"{op} {rp}"
        operands=(rom[pc+1], )
        
    # INC/DEC r
    elif (rom[pc] & 0xf0) == 0b11000000:
        op = ("INC", "DEC")[(rom[pc] >> 3) & 0x1]
        r = _reg(rom[pc])
        asm = f"{op} {r}"

    # INC/DEC saddr
    elif (rom[pc] & 0xfe) == 0b00100110:
        op = ("INC", "DEC")[rom[pc] & 0x1]
        saddr = _I16(_saddr(rom[pc+1]))
        asm = f"{op} {{0}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], )

    # INCW/DECW rp
    elif (rom[pc] & 0xf4) == 0b01000100:
        op = ("INCW", "DECW")[(rom[pc] >> 3) & 0x1]
        rp = _regpair(rom[pc] << 1)
        asm = f"{op} {rp}"

    # ROR/ROL/RORC/ROLC/SHR/SHL/SHRW/SHLW r, n
    elif (rom[pc] & 0xfe) == 0b00110000:
        op = ("RORC", "ROR", "SHR", "SHRW", "ROLC", "ROL", "SHL", "SHLW")[(rom[pc+1] >> 6) & 0x03 + ((rom[pc] & 0x01) << 2)]
        r = _reg(rom[pc+1])
        n = (rom[pc+1] >> 3) & 0x07
        asm = f"{op} {r}, {n:1d}"
        operands=(rom[pc+1], )

    # ROR4 et ROL4 mem1 and & mem1
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xed) == 0b10001100):
        op = ("ROR4", "ROL4")[(rom[pc+1] >> 4) & 0x1]
        mem1 = _mem1((rom[pc+1] >> 1) & 0x1)
        asm = f"{op} {mem_prefix}{mem1}"
        operands=(rom[pc+1])

    # ADJBA/ADJBS
    elif (rom[pc] & 0xfe) == 0b000001110:
        asm = ("ADJBA", "ADJBS")[rom[pc] & 0x01]

    # MOV1/AND1/OR1/XOR1 CY, saddr/sfr.bit
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0x90) == 0b00000000):
        op = ("MOV1", "AND1", "OR1", "XOR1")[(rom[pc+1] >> 5) & 0x03]
        bit = rom[pc+1] & 0x7
        if (rom[pc+1] & 0x08) == 0:
            saddr = _I16(_saddr(rom[pc+2]))
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        else:
            sfr = _I16(_sfr(rom[pc+2]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"{op} CY, {{0}}.{bit:1d}"
        operands=(rom[pc+1], rom[pc+2])

    # MOV1 saddr/sfr.bit, CY
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xf0) == 0b00010000):
        bit = rom[pc+1] & 0x7
        if (rom[pc+1] & 0x08) == 0:
            saddr = _I16(_saddr(rom[pc+2]))
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        else:
            sfr = _I16(_sfr(rom[pc+2]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"MOV1 {{0}}.{bit:1d}, CY"
        operands=(rom[pc+1], rom[pc+2])

    # AND1 CY, /saddr.bit or /sfr.bit
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xf0) == 0b00110000):
        bit = rom[pc+1] & 0x7
        if (rom[pc+1] & 0x08) == 0:
            saddr = _I16(_saddr(rom[pc+2]))
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        else:
            sfr = _I16(_sfr(rom[pc+2]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"AND1 CY, /{{0}}.{bit:1d}, CY"
        operands=(rom[pc+1], rom[pc+2])

    # OR1 CY, /saddr.bit or /sfr.bit
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xf0) == 0b01010000):
        bit = rom[pc+1] & 0x7
        if (rom[pc+1] & 0x08) == 0:
            saddr = _I16(_saddr(rom[pc+2]))
            asm_args = (
                (saddr, ArgumentTypes.ReferencedAddress),
            )
        else:
            sfr = _I16(_sfr(rom[pc+2]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"OR1 CY, /{{0}}.{bit:1d}, CY"
        operands=(rom[pc+1], rom[pc+2])

    # NOT1 saddr.bit or sfr.bit
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xf0) == 0b01110000):
        bit = rom[pc+1] & 0x7
        if (rom[pc+1] & 0x08) == 0:
            saddr = _I16(_saddr(rom[pc+2]))
            asm_args = (
                (saddr    , ArgumentTypes.ReferencedAddress),
            )
        else:
            sfr = _I16(_sfr(rom[pc+2]))
            asm_args = (
                (sfr, ArgumentTypes.ReferencedAddress),
            )
        asm = f"NOT1 {{0}}.{bit:1d}"
        operands=(rom[pc+1], rom[pc+2])

    # SET1/CLR1 sfr.bit
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xe8) == 0b10001000):
        op = ("SET1", "CLR1")[(rom[pc+1] >> 4) & 0x1]
        sfr = _I16(_sfr(rom[pc+2]))
        bit = rom[pc+1] & 0x7
        asm = f"{op} {{0}}.{bit:1d}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # MOV1/AND1/OR1/XOR1 CY, X.bit or A.bit
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0x90) == 0b00000000):
        op = ("MOV1", "AND1", "OR1", "XOR1")[(rom[pc+1] >> 5) & 0x03]
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"{op} CY, {r}.{bit:1d}" % (op, r)
        operands=(rom[pc+1], )

    # MOV1 X.bit or A.bit, CY
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xf0) == 0b00010000):
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"MOV1 {r}.{bit:1d}, CY"
        operands=(rom[pc+1], )

    # AND1 CY, /X.bit or /A.bit
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xf0) == 0b00110000):
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"AND1 CY, /{r}.{bit:1d}"
        operands=(rom[pc+1], )

    # OR1 CY, /X.bit or /A.bit
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xf0) == 0b01010000):
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"OR1 CY, /{r}.{bit:1d}"
        operands=(rom[pc+1], )

    # NOT1 X.bit or A.bit
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xf0) == 0b01110000):
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"NOT1 {r}.{bit:1d}"
        operands=(rom[pc+1], )

    # SET1/CLR1 X.bit or A.bit
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xe0) == 0b10000000):
        op = ("SET1", "CLR1")[(rom[pc+1] >> 4) & 0x1]
        r = ("X", "A")[(rom[pc+1] >> 3) & 0x01]
        bit = rom[pc+1] & 0x7
        asm = f"{op} {r}.{bit:1d}"
        operands=(rom[pc+1], )

    # CLR1 CY
    elif rom[pc] == 0b01000000:
        asm = "CLR1 CY"

    # SET1 CY
    elif rom[pc] == 0b01000001:
        asm = "SET1 CY"

    # NOT1 CY
    elif rom[pc] == 0b01000010:
        asm = "NOT1 CY"

    # SET1/CLR1 saddr.bit
    elif ((rom[pc] & 0xe8) == 0b10100000):
        op = ("SET1", "CLR1")[(rom[pc] >> 4) & 0x1]
        saddr = _I16(_saddr(rom[pc+1]))
        bit = rom[pc] & 0x7
        asm = f"{op} {saddr}.{bit:1d}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], )

    # MOV1/AND1/OR1/XOR1 CY, PSW.bit
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0x90) == 0b00000000):
        op = ("MOV1", "AND1", "OR1", "XOR1")[(rom[pc+1] >> 5) & 0x03]
        bit = rom[pc+1] & 0x7
        asm = f"{op} CY, PSW.{bit:1d}"
        operands=(rom[pc+1], )

    # MOV1 PSW.bit, CY
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0xf8) == 0b00010000):
        bit = rom[pc+1] & 0x7
        asm = f"MOV1 PSW.{bit:1d}, CY"
        asm_args = (
            (rom[pc+1] & 0x7, ArgumentTypes.AsIs),
        )
        operands=(rom[pc+1], )

    # AND1 CY, /PSW.bit
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0xf8) == 0b00110000):
        bit = rom[pc+1] & 0x7
        asm = f"AND1 CY, /PSW.{bit:1d}"
        operands=(rom[pc+1], )

    # OR1 CY, /PSW.bit
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0xf8) == 0b01010000):
        bit = rom[pc+1] & 0x7
        asm = f"OR1 CY, /PSW.{bit:1d}"
        operands=(rom[pc+1], )

    # NOT1 PSW.bit
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0xf8) == 0b01110000):
        bit = rom[pc+1] & 0x7
        asm = f"NOT1 PSW.{bit:1d}"
        operands=(rom[pc+1], )

    # SET1/CLR1 PSW.bit
    elif (rom[pc] == 0b00000010) and ((rom[pc+1] & 0xe8) == 0b10000000):
        op = ("SET1", "CLR1")[(rom[pc+1] >> 4) & 0x1]
        bit = rom[pc+1] & 0x7
        asm = f"{op} PSW.{bit:1d}"
        operands=(rom[pc+1], )

    # CALL !addr16
    elif rom[pc] == 0b00101000:
        flow_type = FlowTypes.SubroutineCall
        target_address = _I16(_addr16(rom[pc+1], rom[pc+2]))
        asm = f"CALL !{{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # CALL rp
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xf8) == 0b01011000):
        rp = _regpair(rom[pc+1])
        asm = f"CALL {rp}"
        operands=(rom[pc+1], )

    # CALLF !addr11
    elif ((rom[pc] & 0xf8) == 0b10010000):
        flow_type = FlowTypes.SubroutineCall
        target_address = _I11(0x0800 + rom[pc+1] + ((rom[pc] & 0x07) << 8))
        asm = f"CALLF !{{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], )

    # CALLT [addr5]
    elif ((rom[pc] & 0xe0) == 0b11100000):
        flow_type = FlowTypes.SubroutineCall
        addr5 = rom[pc] & 0x1f
        target_address = _I16(rom[0x0040 + addr5])
        asm = f"CALLT [{addr5:02x}]:{{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )

    # BRK/RET/RETI/RETB
    elif ((rom[pc] & 0xf6) == 0b01010110):
        flow_type = FlowTypes.Stop if (rom[pc] == 0b01011110) else FlowTypes.SubroutineReturn
        asm = ("RET", "RETI", "BRK", "RETB")[((rom[pc] & 0x08) >> 2) + rom[pc] & 0x01]

    # PUSH/POP rp
    elif ((rom[pc] & 0xf4) == 0b00110100):
        op = ("POP", "PUSH")[(rom[pc] >> 3) & 0x1]
        rp = _regpair(rom[pc] << 1)
        asm = f"{op} {rp}"

    # PUSH/POP PSW
    elif ((rom[pc] & 0xfe) == 0b01001000):
        op = ("POP", "PUSH")[rom[pc] & 0x1]
        asm = f"{op} PSW"

    # PUSH sfr
    elif rom[pc] == 0b00101001:
        sfr = _I16(_sfr(rom[pc+1]))
        asm = f"PUSH {{0}}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], )

    # POP sfr
    elif rom[pc] == 0b01000011:
        sfr = _I16(_sfr(rom[pc+1]))
        asm = f"POP {{0}}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
        )
        operands=(rom[pc+1], )

    # INCW SP and DECW SP
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xfe) == 0b11001000):
        op = ("INCW", "DECW")[rom[pc+1] & 0x1]
        asm = f"{op} SP"
        operands=(rom[pc+1], )

    # BR !addr16
    elif rom[pc] == 0b00101100:
        flow_type = FlowTypes.UnconditionalJump
        target_address = _I16(_addr16(rom[pc+1], rom[pc+2]))
        asm = f"BR !{{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # BR rp
    elif (rom[pc] == 0b00000101) and ((rom[pc+1] & 0xf9) == 0b01001000):
        rp = _regpair(rom[pc+1])
        asm = f"BR !{rp}"
        operands=(rom[pc+1], )

    # BR $addr16
    elif rom[pc] == 0b00010100:
        flow_type = FlowTypes.UnconditionalJump
        target_address = _I16(pc + 2 + (rom[pc+1] & 0x7f) - (rom[pc+1] & 0x80))
        asm = f"BR ${{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], )

    # BC/BL, BNC/BNL, BZ/BE, BNZ/BNE $addr16
    elif (rom[pc] & 0xfc) == 0b10000000:
        flow_type = FlowTypes.ConditionalJump
        target_address = _I16(pc + 2 + (rom[pc+1] & 0x7f) - (rom[pc+1] & 0x80))
        op = ("BNZ", "BZ", "BNC", "BC")[rom[pc] & 0x3]
        asm = f"{op} ${{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], )

    # BT saddr.bit, $addr16
    elif (rom[pc] & 0xf8) == 0b01110000:
        flow_type = FlowTypes.ConditionalJump
        saddr = _I16(_saddr(rom[pc+1]))
        bit = rom[pc] & 0x07
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        asm = f"BT {{0}}.{bit:1d}, ${{1}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # BF saddr.bit, $addr16
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xe8) == 0b10100000):
        flow_type = FlowTypes.ConditionalJump
        op = ("BF", "BTCLR")[(rom[pc+1] >> 4) & 0x1]
        saddr = _I16(_saddr(rom[pc+2]))
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 4 + (rom[pc+3] & 0x7f) - (rom[pc+3] & 0x80))
        asm = f"{op} {{0}}.{bit:1d}, ${{1}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # BT or BF sfr.bit, $addr16
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xe8) == 0b10101000):
        flow_type = FlowTypes.ConditionalJump
        op = ("BF", "BT")[(rom[pc+1] >> 4) & 0x1]
        sfr = _I16(_sfr(rom[pc+2]))
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 4 + (rom[pc+3] & 0x7f) - (rom[pc+3] & 0x80))
        asm = f"{op} {{0}}.{bit:1d}, ${{1}}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # BTCLR sfr.bit, $addr16
    elif (rom[pc] == 0b00001000) and ((rom[pc+1] & 0xf8) == 0b11010000):
        flow_type = FlowTypes.ConditionalJump
        sfr = _I16(_sfr(rom[pc+2]))
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 4 + (rom[pc+3] & 0x7f) - (rom[pc+3] & 0x80))
        asm = f"BTCLR {{0}}.{bit:1d}, ${{1}}"
        asm_args = (
            (sfr, ArgumentTypes.ReferencedAddress),
            (target_address, ArgumentTypes.TargetAddress),
        )
        referenced_addresses = (sfr, )
        operands=(rom[pc+1], rom[pc+2], rom[pc+3])

    # BT or BF A.bit, $addr16 and BT X.bit, $addr16
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xe0) == 0b10100000):
        flow_type = FlowTypes.ConditionalJump
        op = ("BF", "BT")[(rom[pc+1] >> 4) & 0x1]
        arg = ("X", "A")[(rom[pc+1] >> 3) & 0x1] 
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        asm = f"{op} {arg}.{bit:1d}, {{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # BTCLR A.bit, $addr16 and BT X.bit, $addr16
    elif (rom[pc] == 0b00000011) and ((rom[pc+1] & 0xf0) == 0b11010000):
        flow_type = FlowTypes.ConditionalJump
        arg = ("X", "A")[(rom[pc+1] >> 3) & 0x1] 
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        asm = f"BTCLR {arg}.{bit:1d}, {{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # BT or BF PSW.bit, $addr16
    elif rom[pc] in (0b0000010, 0b00000010) and ((rom[pc+1] & 0xf8) == 0b10100000):
        flow_type = FlowTypes.ConditionalJump
        op = "BT" if rom[pc] == 0b00000010 else "BF"
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        asm = f"{op} PSW.{bit:1d}, ${{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # BTCLR PSW.bit, $addr16
    elif (rom[pc] == 0b0000010) and ((rom[pc+1] & 0xf8) == 0b11010000):
        flow_type = FlowTypes.ConditionalJump
        bit = rom[pc+1] & 0x07
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        asm = f"BTCLR PSW.{bit:1d}, ${{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    # DBNZ r1, $addr16
    elif (rom[pc] & 0xfe) == 0b00110010:
        flow_type = FlowTypes.ConditionalJump
        r1 = _mem1(rom[pc])
        target_address = _I16(pc + 2 + (rom[pc+1] & 0x7f) - (rom[pc+1] & 0x80))
        asm = f"DBNZ {r1}, {{0}}"
        asm_args = (
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], )

    # DBNZ saddr, $addr16
    elif rom[pc] == 0b00111011:
        flow_type = FlowTypes.ConditionalJump
        target_address = _I16(pc + 3 + (rom[pc+2] & 0x7f) - (rom[pc+2] & 0x80))
        saddr = _I16(_saddr(rom[pc+1]))
        asm = f"DBNZ {{0}}, {{1}}"
        asm_args = (
            (saddr, ArgumentTypes.ReferencedAddress),
            (target_address, ArgumentTypes.TargetAddress),
        )
        operands=(rom[pc+1], rom[pc+2])

    else:
        raise IllegalInstructionError(f"Illegal opcode 0x{rom[pc]:02x} at 0x{pc:04x}")

    inst = Instruction(asm = asm,
                       asm_args=asm_args,
                       flow_type=flow_type,
                       opcode=opcodes,
                       operands=operands)

    return inst
