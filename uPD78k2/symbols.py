
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
    # Static data
    0x024e: ("disp_sprite_desc[0]","Sprite descriptors (7B)"),
    0x0255: ("disp_sprite_desc[1]","Sprite descriptors (7B)"),
    0x025c: ("disp_sprite_desc[2]","Sprite descriptors (7B)"),
    0x0263: ("disp_sprite_desc[3]","Sprite descriptors (7B)"),
    0x026a: ("disp_sprite_desc[4]","Sprite descriptors (7B)"),
    0x0271: ("disp_sprite_desc[5]","Sprite descriptors (7B)"),
    0x0278: ("disp_sprite_desc[6]","Sprite descriptors (7B)"),
    0x027f: ("disp_sprite_desc[7]","Sprite descriptors (7B)"),
    0x0286: ("disp_sprite_desc[8]","Sprite descriptors (7B)"),
    # CALLF
    0x0800: ("callf_start", "CALLF area start address"),
    0x0b41: ("set_9f#32()", "Set 0x9c to 0x32 and wait for ack"),
    0x0b46: ("set_9f#0a()", "Set 0x9c to 0x0a and wait for ack"),
    0x0b4b: ("set_9f#01()", "Set 0x9c to 0x01 and wait for ack"),
    0x0b55: ("set_a1#00()", "Set 0xa1 to 0x00"),
    0x0b5b: ("set_a0#0a()", "Set 0xa0 to 0x0a"),
    0x0b61: ("getW_ext_0007()", "Get ext 0x0007 word"),
    0x0b6a: ("get_ceil(ext 0007/8)", "Get ceil(&[0x0007],8)"),
    0x0b7b: ("getW_*(*ext 0002).0xa", "Get ext word at 0xa offset of struct pointer at 0x0002"),
    0x0b8a: ("setW_*(*ext 0002).0xa(AX)", "Set ext word at 0xa offset of struct pointer at 0x0002 to A"),
    0x1000: ("INTC10_irq_handler()", "INTC10 ('tick') irq handler"),
    0x1103: ("firmware_version", "firmware version string"),
    0x10eb: ("int_unmask_INTC10", "Unmask INTC10 ('tick')"),
    0x10ef: ("int_mask_INTC10", "Mask INTC10 ('tick')"),
    0x10f7: ("int_unmask_INTP0", "Unmask INTP0 (P21/CSI CS)"),
    0x10ff: ("int_unmask_INTC11", "Unmask INTC11 (??)"),
    0x1357: ("disp_write_c1(AX, B, C)", "Write AX from cfg 1 at (B,C) to buffer/lcd"),
    0x136f: ("disp_write_c3(AX, B, C)", "Write AX from cfg 3 at (B,C) to buffer/lcd"),
    0x139f: ("disp_write_c7(AX, B, C)", "Write AX from cfg 7 at (B,C) to buffer/lcd"),
    0x13ab: ("disp_write_c8(AX, B, C)", "Write AX from cfg 8 at (B,C) to buffer/lcd"),
    0x13b7: ("disp_write(0x90:A)", "Write 0x90:A to buffer/lcd"),
    0x13d3: ("disp_write(AX)", "Write AX to buffer/lcd"),
    0x1437: ("disp_update_col_8(AX,C)","Update display column C from AX "),
    0x14c9: ("disp_update_col_16(AX,C)","Update display column C from AX"),
    0x15a8: ("disp_update_col_32(AX,BC,C)","Update display column C from AX, BC "),
    0x16f1: ("read_022a(&DE, &L)", "Read 3B at [0x022a] in L, DE"),
    0x16fe: ("read_022di(&DE, &L)", "Read 3B in L, DE"),
    0x170d: ("read_ext_cfg(A)", "Read 5B from 0x024e+7*A into AX L DE C B"),
    0x1743: ("read_ext_word(L, DE, A)", "Read word from page L at DE+A*2"),
    0x1762: ("disp_sprite_base(AX, &DE)","Compute sprite base address for AX from disp config"),
    0x179e: ("disp_read_cfg(A)", "Read display config[A] into IRAM"),
    0x17ba: ("disp_read_def", "Read default display config into IRAM"),
    0x17f5: ("disp_sprite_read_col(DE, &AX, &BC)", "Read one 32b column of sprite data"),
    0x1808: ("disp_clear()", "Fill display with 0"),
    0x180f: ("disp_fill()", "Fill display with 1"),
    0x1816: ("disp_buf_all_1()", "Fill display buffer with 1"),
    0x181b: ("disp_buf_all_0()", "Fill display buffer with 0"),
    0x182f: ("disp_lcd01_refresh()", "Update lcd display from SRAM buffer"),
    0x1932: ("disp_clear(A, X, B, C)", "Clear display from (B,C) for A, X"),
    0x1a64: ("disp_pixel_set_clr(A, B, C)", "A=1/Set, 0/Cleat pixel at position B,C"),
    0x1a8c: ("lcd_write(A, B, C)", "Write A at page B/8, column C"),
    0x1aac: ("disp_buf_write(A, B, C)", "Write char A at position B,C into buffer"),
    0x1ac4: ("set_ext_0004(A)", "Set byte at ext 0x0004"),
    0x1aca: ("get_ext_0004()", "Get byte at ext 0x0004"),
    0x1ad0: ("get_ext_06ec()", "Get byte at ext 0x06ec"),
    0x1ad8: ("set_ext_06ec(A)", "Set byte at ext 0x06ec"),
    0x1ade: ("invert_ext_0002()", "Invert byte at ext 0x0002"),
    0x1af8: ("getW_ext_0002()", "Get byte at ext 0x0002"),
    0x1b01: ("lcd_turn_on()", "Turn display on"),
    0x1b13: ("lcd_setcolumn(A)", "Set column (in the correct chip)"),
    0x1b26: ("lcd_writedata(A)", "Write display data (in the correct chip)"),
    0x1b37: ("lcd01_setRAMpage(A)", "Set RAM page address"),
    0x1cf2: ("disp_pixel_addr_mask(B,C)", "DE=buffer address for row(B)/column(C), A=bit offset/mask"),
    0x1d1f: ("Bdiv8()", "Divide B by 8"),
    0x1d2f: ("disp_get_cur_pos()", "Read cursor position"),
    0x1d3b: ("disp_set_pos(B, C)", "Write row, column from IRAM"),
    0x1d44: ("SHL_empty_nibbles(AX)", "Shift left AX until msb nibble <> 0"),
    0x1d92: ("crit_set_a2a6(0CBXA)", "Critical section;a3-a6 "),
    0x1d92: ("crit_tbd()", "Critical section; set a3-a6-> aa-ad, wait on ad, restore"),
    0x1e17: ("save_C+2B+2_aeaf", "Store B+2, C+2 in IRAM[0xae-0xaf]"),
    0x1e26: ("dec4_acad_b0b1", "IRAM[b0]=IRAM[ac]-4, IRAM[b1]=IRAM[ad]-4"),
    0x1e37: ("lcd0_ctrl(A)", "Write ctrl byte A to lcd chip#0"),
    0x1e49: ("lcd1_ctrl(A)", "Write ctrl byte A to lcd chip#1"),
    0x1e5b: ("lcd01_ctrl(A)", "Write ctrl byte A to both lcd chips"),
    0x1e6f: ("lcd0_data(A)", "Write data byte A to lcd chip#0"),
    0x1e89: ("lcd1_data(A)", "Write data byte A to lcd chip#1"),
    0x1ea1: ("read_ext_byte(L, DE)", "Read byte at DE from page L"),
    0x1eb0: ("read_ext_word(L, DE)", "Read word at DE from page L"),
    0x1ee8: ("Set_P6_low(L)", "Set P6.3-0 to L"),
    0x1ef3: ("WaitFor57.1(X)", "Wait for IRAM[0x57].1 for x ms"),
    0x1f1c: ("waitms(A)", "Wait for A ms"),
    0x1f29: ("buzzer_on(0x0a)", "Enable buzzer for 0x0a tick cycles"),
    0x1f37: ("buzzer_on(0x32)", "Enable buzzer for 0x32 tick cycles"),
    0x1f45: ("buzzer_on(0x0a,0x05)", "Enable buzzer for 0x05 * 0x0a tick cycles"),
    0x1f56: ("buzzer_wait_off()", "Wait for buzzer off"),
    0x1f5c: ("getBCD(AX)", "Convert AX to BCD"),
    0x1f7f: ("mult24(AX, BC)", "C_AX = AX * BX"),
    0x1fbb: ("dec_DE_with_Z()", "DE--, set Z"),
    0x1fcb: ("inc_DE_with_Z()", "DE--, set Z"),
    0x1fd3: ("get_version()", "get firmware version"),
    0x1fdb: ("check_Prom(0)", "Return sum mod 2**16 of rom[0x0000-0xfcff] in AX"),
    0x25b5: ("cartridge_cfg_low()", "0xa0000.3-0=L & 0x0f "),
    0x25ce: ("cartridge_cfg_high()", "0xa0000.7-4=L & 0xf0 "),
    0x25e7: ("cartridge_is_skip()", "Check cartrige presence"),
    0x25eb: ("cartridge_check()", "Check cartrige presence"),
    0x2617: ("cartridge_boot()", "Boot cartrige code"),
    0x2cac: ("uart_txchar", "Tx one byte to uart"),
    0x2d0a: ("hex(A)", "Return hex code for A"),
    0x2d18: ("ascii(A)", "Return ASCII code for A"),
    0x2d23: ("p0_irq_handler", "P0(P2.1) interrupt handler"),
    0x2daa: ("p0_irq_handler_exit", "P0(P2.1) interrupt handler exit"),
    0x2db2: ("csi_irq_handler", "CSI interrupt handler"),
    0x2f1b: ("shared_irq_handler_exit", "Shared CSI/P0(P2.1) interrupt handler exit"),
    0x3234: ("program_start", "Reset entry point"),
    0x328c: ("memset_iram_0", "Clear IRAM"),
    0x32b7: ("spin_forever()", "Spin forever"),
    0x33a5: ("main_loop?()", "Main loop ?"),
    0x4102: ("disp_clear_coffee_cup()", "Clear Display with a centered coffee cup"),
    0x410f: ("disp_coffee_cup()", "Display a coffe cup at 0 or 3/fe66.3,82"),
    0x412e: ("disp_coffee_cup(B, C)", "Display a coffe cup at B,C"),
    0x52db: ("disp_clear_area(A,X)","Clear upper right window from A/column to X/row"),
    0x6e3f: ("draw_pixel()", "draw pixel at the cursor position"),
    0xce65: ("readW_addr(AX, B)", "Read [AX+2*B]"),
    0xce75: ("disp_init_error?()", "Display init error ???"),
    0xd657: ("disp_get_cfg(0)", "Restore display cfg[0]"),
    0xd65f: ("disp_get_cfg(1)", "Restore display cfg[1]"),
    0xd667: ("disp_get_cfg(2)", "Restore display cfg[2]"),
    0xd66f: ("disp_get_cfg(3)", "Restore display cfg[3]"),
    0xd677: ("disp_get_cfg(4)", "Restore display cfg[4]"),
    0xd67f: ("disp_get_cfg(5)", "Restore display cfg[5]"),
    0xd687: ("disp_get_cfg(6)", "Restore display cfg[6]"),
    0xd68f: ("disp_get_cfg(7)", "Restore display cfg[7]"),
    0xd697: ("disp_get_cfg(8)", "Restore display cfg[8]"),
    0xd6b4: ("keyb_wait_release()", "Wait for key release"),
    0xd6e8: ("scan_inputs()", "Scan all keypad and P2 port"),
    0xd742: ("keyb_scan_arrows()", "Scan P2.5/4/1/0 inputs (arrow pad)"),
    0xd797: ("keyb_scan_1x4()", "Scan right keypad column"),
    0xd7ec: ("keyb_scan_3x4()", "Scan right keypad column"),
    0xd876: ("keyb_read_row()", "Read keypad row"),
    0xe0b7: ("test_prom()", "PROM test"),
    0xe11c: ("prom_check(L, DE)", "Check PROM for bank L, msg DE"),
    0xe137: ("prom_bank_sum()", "Sum PROM bank mod 2**16"),
    0xe154: ("prom_error()", "PROM checksum error msg"),
    0xe252: ("test_key()", "KEY test"),
    0xe48e: ("test_sram()", "SRAM test"),
    0xe520: ("print(char *DE)", "Print string"),
    0xe53b: ("print(sStr *DE)", "Print string struct"),
    0xe547: ("print(DE, B, C)", "Print *DE at B,C ?"),
    0xe554: ("printChar(A, B, C)", "Print A at B,C ?"),
    0xe5b5: ("print(AX, B, C)", "Print AX (ASCII)"),
    0xe862: ("menu_test", "Display test menu"),
    0xe8fd: ("wait_for_keyb", "Wait for keypad input"),
    # Data
    0xe4cb: ("string_machine_table", "char* machine[]"),
    0xe5c8: ("string_table", "2 uint8_t + string"),
    0xe6c2: ("strings", ""),
    0xe71c: ("strings_machine", ""),
    0xed1c: ("is_input(&A)", "Clr CY upon input change"),
    0xed33: ("wait_ISR_ack_0a()","Wait for ISR to ack 0x0a in 0x9c"),
    0xed41: ("wait_ISR_ack_32()","Wait for ISR to ack 0x32 in 0x9c"),
    # PRAM
    0xfd00: ("pram_start", "PRAM start address"),
    # IRAM
    0xfe00: ("iram_start", "IRAM start address"),
    0xfeaa: ("cursor_col", "Cursor's column"),
    0xfeab: ("cursor_row", "Cursor's row"),
    0xfeac: ("sprite_height", "Sprite height"),
    0xfead: ("sprite_width", "Sprite width"),
    0xfeb6: ("sprite_base_add_h", "Sprite base address High"),
    0xfeb7: ("sprite_base_add_l", "Sprite base address Low"),
    0xfeb8: ("sprite_offset_add_h", "Sprite offset address High"),
    0xfeb9: ("sprite_offset_add_l", "Sprite offset address High"),
    0xfebb: ("disp_cfg_id", "Display configuration ID"),
    0xfebc: ("disp_flags", "Display flags"),
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
