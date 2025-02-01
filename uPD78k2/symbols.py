
class SymbolTable(object):
    def __init__(self, initial_symbols=None):
        if initial_symbols is None:
            initial_symbols = {}
        self.symbols = initial_symbols.copy()

    def generate(self, memory, start_address):
        self.generate_code_symbols(memory, start_address)
        self.generate_data_symbols(memory, start_address)

    def generate_code_symbols(self, memory, start_address):
        for address in range(start_address, len(memory)):
            if address not in self.symbols:
                if memory.is_call_target(address):
                    if memory.is_instruction_start(address):
                        self.symbols[address] = ('sub_%04x' % address, '')
                elif memory.is_jump_target(address) or memory.is_entry_point(address):
                    if memory.is_instruction_start(address):
                        self.symbols[address] = ('lab_%04x' % address, '')
        # XXX do not overwrite

    def generate_data_symbols(self, memory, start_address):
        data_addresses = set()

        for _, inst in memory.iter_instructions():
            addresses = getattr(inst, 'referenced_addresses', None)
            if addresses is not None:
                for address in addresses:
                    data_addresses.add(address)

        for address in data_addresses:
            if address not in self.symbols:
                self.symbols[address] = ('mem_%04x' % address, '')


NEC78K2_COMMON_SYMBOLS = {}
for i, address in enumerate(range(0x40, 0x7f, 2)):
    NEC78K2_COMMON_SYMBOLS[address] = ("callt_%d_vect" % i, "CALLT #%d" % i)

uPD78213_SYMBOLS = NEC78K2_COMMON_SYMBOLS.copy()
uPD78213_SYMBOLS.update(
{
    # hardware vectors
    0x0000: ("rst_vect", "RST"),
    0x0002: ("nmi_vect", "NMI"),
    0x0004: ("unused0_vect", "(unused)"),
    0x0006: ("intp0_vect", "INTP0"),
    0x0008: ("intp1_vect", "INTP1"),
    0x000a: ("intp2_vect", "INTP2"),
    0x000c: ("intp3_vect", "INTP3"),
    0x000e: ("intp4_vect", "INTP4/INTC30"),
    0x0010: ("intp5_vect", "INTP5/INAD"),
    0x0012: ("intp6_vect", "INTP6/INTC20"),
    0x0014: ("intc00_vect", "INTC00"),
    0x0016: ("intc01_vect", "INTC01"),
    0x0018: ("intc10_vect", "INTC10"),
    0x001a: ("intc11_vect", "INTC11"),
    0x001c: ("intc21_vect", "INTC21"),
    0x001e: ("unused1_vect", "(unused)"),
    0x0020: ("intser_vect", "INTSER"),
    0x0022: ("intsr_vect", "INTSR"),
    0x0024: ("intst_vect", "INTST"),
    0x0026: ("intcsi_vect", "INTCSI"),
    0x0028: ("interr_vect", "INTERR"),
    0x002a: ("intepw_vect", "INTEPW"),
    0x002c: ("unused2_vect", "(unused)"),
    0x002e: ("unused3_vect", "(unused)"),
    0x0030: ("unused4_vect", "(unused)"),
    0x0032: ("unused5_vect", "(unused)"),
    0x0034: ("unused6_vect", "(unused)"),
    0x0036: ("unused7_vect", "(unused)"),
    0x0038: ("unused8_vect", "(unused)"),
    0x003a: ("unused9_vect", "(unused)"),
    0x003c: ("unused10_vect", "(unused)"),
    0x003e: ("brk_vect", "BRK"),
    # CALLT
    0x0040: ("callt_start", "CALLT area start address"),
    # CALLF
    0x0800: ("callf_start", "CALLF area start address"),
    # PRAM
    0xfd00: ("pram_start", "IRAM start address"),
    # IRAM
    0xfe00: ("iram_start", "IRAM start address"),
    # General registers
    0xfee0: ('A3', 'A bank3'),
    0xfee1: ('X3', 'X bank3'),
    0xfee2: ('B3', 'B bank3'),
    0xfee3: ('C3', 'C bank3'),
    0xfee4: ('D3', 'D bank3'),
    0xfee5: ('E3', 'E bank3'),
    0xfee6: ('H3', 'H bank3'),
    0xfee7: ('L3', 'L bank3'),
    0xfee8: ('A2', 'A bank2'),
    0xfee9: ('X2', 'X bank2'),
    0xfeea: ('B2', 'B bank2'),
    0xfeeb: ('C2', 'C bank2'),
    0xfeec: ('D2', 'D bank2'),
    0xfeed: ('E2', 'E bank2'),
    0xfeee: ('H2', 'H bank2'),
    0xfeef: ('L2', 'L bank2'),
    0xfef0: ('A1', 'A bank1'),
    0xfef1: ('X1', 'X bank1'),
    0xfef2: ('B1', 'B bank1'),
    0xfef3: ('C1', 'C bank1'),
    0xfef4: ('D1', 'D bank1'),
    0xfef5: ('E1', 'E bank1'),
    0xfef6: ('H1', 'H bank1'),
    0xfef7: ('L1', 'L bank1'),
    0xfef8: ('A0', 'A bank0'),
    0xfef9: ('X0', 'X bank0'),
    0xfefa: ('B0', 'B bank0'),
    0xfefb: ('C0', 'C bank0'),
    0xfefc: ('D0', 'D bank0'),
    0xfefd: ('E0', 'E bank0'),
    0xfefe: ('H0', 'H bank0'),
    0xfeff: ('L0', 'L bank0'),
    # special function registers
    0xff00: ('P0', 'Port 0'),
    0xff02: ('P2', 'Port 2'),
    0xff03: ('P3', 'Port 3'),
    0xff04: ('P4', 'Port 4'),
    0xff05: ('P5', 'Port 5'),
    0xff06: ('P6', 'Port 6'),
    0xff07: ('P7', 'Port 7'),
    0xff0a: ('P0l', 'Port 0 buffer register low'),
    0xff0b: ('P0h', 'Port 0 buffer register high'),
    0xff0c: ('RTPC', 'Real-time output port control register'),
    0xff10: ('CR00l', '16-bit timer/counter compare register 0L'),
    0xff11: ('CR00h', '16-bit timer/counter compare register 0H'),
    0xff12: ('CR01l', '16-bit timer/counter compare register 1L'),
    0xff13: ('CR01h', '16-bit timer/counter compare register 1H'),
    0xff14: ('CR10', '8-bit timer/counter 1 compare register'),
    0xff15: ('CR20', '8-bit timer/counter 2 compare register'),
    0xff16: ('CR21', '8-bit timer/counter 2 compare register'),
    0xff17: ('CR30', '8-bit timer/counter 3 compare register'),
    0xff18: ('CR02l', '16-bit timer/counter capture register L'),
    0xff19: ('CR02h', '16-bit timer/counter capture register H'),
    0xff1a: ('CR22', '8-bit timer/counter 2 capture register'),
    0xff1c: ('CR11', '8-bit timer/counter 1 capture register'),
    0xff20: ('PM0', 'Port mode register 0'),
    0xff23: ('PM3', 'Port mode register 3'),
    0xff25: ('PM5', 'Port mode register 5'),
    0xff26: ('PM6', 'Port mode register 6'),
    0xff30: ('CRC0', 'Capture/compare control register 0'),
    0xff31: ('TOC', 'Timer output control register 0'),
    0xff32: ('CRC1', 'Capture/compare control register 1'),
    0xff34: ('CRC2', 'Capture/compare control register 2'),
    0xff40: ('PUO', 'Pull-up resistor option register'),
    0xff43: ('PMC3', 'Port 3 mode control register'),
    0xff50: ('TM0l', '16-bit timer register 0L'),
    0xff51: ('TM0h', '16-bit timer register 0H'),
    0xff52: ('TM1', '8-bit timer register 1'),
    0xff54: ('TM2', '8-bit timer register 2'),
    0xff56: ('TM3', '8-bit timer register 3'),
    0xff5c: ('PRM0', 'Prescaler mode register 0'),
    0xff5d: ('TMC0', 'Timer control register 0'),
    0xff5e: ('PRM1', 'Prescaler mode register 1'),
    0xff5f: ('TMC1', 'Timer control register 1'),
    0xff68: ('ADM', 'A/D converter mode register'),
    0xff6a: ('ADCR', 'A/D conversion result register'),
    0xff80: ('CSIM', 'Clock synchronous serial interface mode register'),
    0xff82: ('SBIC', 'Serial bus interface control register'),
    0xff86: ('SIO', 'Serial shift register'),
    0xff88: ('ASIM', 'Asynchronous serial interface mode register'),
    0xff8a: ('ASIS', 'Asynchronous serial interface status register'),
    0xff8c: ('RXB', 'Serial reception buffer: UART'),
    0xff8e: ('TXS', 'Serial transmission shift register: UART'),
    0xff90: ('BRGC', 'Baud rate generator control register'),
    0xffc0: ('STBC', 'Standby control register'),
    0xffc4: ('MM', 'Memory expansion mode register'),
    0xffc5: ('PW', 'Programmable weight control register'),
    0xffc6: ('STBC', 'Refresh mode register'),
    0xffd0: ('FFD0', 'FFD0 (External Access Area)'),
    0xffd1: ('FFD1', 'FFD1 (External Access Area'),
    0xffd2: ('FFD2', 'FFD2 (External Access Area'),
    0xffd3: ('FFD3', 'FFD3 (External Access Area'),
    0xffd4: ('FFD4', 'FFD4 (External Access Area'),
    0xffd5: ('FFD5', 'FFD5 (External Access Area'),
    0xffd6: ('FFD6', 'FFD6 (External Access Area'),
    0xffd7: ('FFD7', 'FFD7 (External Access Area'),
    0xffd8: ('FFD8', 'FFD8 (External Access Area'),
    0xffd9: ('FFD9', 'FFD9 (External Access Area'),
    0xffda: ('FFDa', 'FFDA (External Access Area'),
    0xffdb: ('FFDb', 'FFDB (External Access Area'),
    0xffdc: ('FFDc', 'FFDC (External Access Area'),
    0xffdd: ('FFDd', 'FFDD (External Access Area'),
    0xffde: ('FFDe', 'FFDE (External Access Area'),
    0xffdf: ('FFDf', 'FFDF (External Access Area'),
    0xffe0: ('IF0l', 'Interrupt request flag register L'),
    0xffe1: ('IF0h', 'Interrupt request flag register H'),
    0xffe4: ('MK0l', 'Interrupt mask flag register L'),
    0xffe5: ('MK0h', 'Interrupt mask flag register H'),
    0xffe8: ('PR0l', 'Priority designation flag register L'),
    0xffe9: ('PR0h', 'Priority designation flag register H'),
    0xffec: ('ISM0l', 'Interrupt service mode register L'),
    0xffed: ('ISM0h', 'Interrupt service mode register H'),
    0xfff4: ('INTM0', 'External interrupt mode register 0'),
    0xfff5: ('INTM1', 'External interrupt mode register 1'),
    0xfff8: ('ISR', 'Interrupt status register 1'),
})
