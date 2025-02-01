# Work derived from https://github.com/mnaberez/k0dasm
import argparse
import logging
import sys

from memory import Memory
from trace import Tracer
from listing import Printer
from uPD78k2.disassemble import disassemble
from uPD78k2.symbols import SymbolTable, uPD78213_SYMBOLS

ROM_FILENAME = 'rom.bin'
def _vector(address):
    return address[0] + (address[1] >> 8)

if __name__ == '__main__':
    # Parse command line
    parser = argparse.ArgumentParser(description="NEC 78K Disassembler.")
    parser.add_argument("-f", type=str, help=f"ROM file ({ROM_FILENAME})", nargs="?", default=ROM_FILENAME)
    parser.add_argument("-d",           help="Set loglevel to debug", action="store_true")

    args = parser.parse_args()

    # Setup logger
    loglevel = logging.DEBUG if args.d else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=loglevel)

    logger = logging.getLogger("Disassembler")

    try:
      with open(args.f, 'rb') as f:
         rom = bytearray(f.read())
    except :
        logger.error(f"Unable to open {args.f}")
        sys.exit(1)

    memory = Memory(rom)

    hardware_vectors = [
        0x0000, # RST
        0x0002, # NMI
        0x0004, # (unused)
        0x0006, # INTP0
        0x0008, # INTP1
        0x000a, # INTP2
        0x000c, # INTP3
        0x000e, # INTP4/INTC30
        0x0010, # INTP5/INTAD
        0x0012, # INTP6/INTC20
        0x0014, # INTC00
        0x0016, # INTC01
        0x0018, # INTC10
        0x001a, # INTC11
        0x001c, # INTC21
        0x001e, # (unused)
        0x0020, # INTSER
        0x0022, # INTSR
        0x0024, # INTST
        0x0026, # INTCSI
        0x0028, # INTEER
#        0x002a, # INTEPW
        0x002c, # (unused)
        0x002e, # (unused)
        0x0030, # (unused)
        0x0032, # (unused)
        0x0034, # (unused)
        0x0036, # (unused)
        0x0038, # (unused)
        0x003a, # (unused)
        0x003c, # (unused)
        0x003e,  # BRK
    ]
    #callt_vectors = list(range(0x40, 0x7f, 2))
    callt_vectors = list(range(0x42, 0x7f, 2))
    all_vectors = hardware_vectors + callt_vectors

    entry_points = []

    start_address = 0
    #traceable_range = range(start_address, start_address + len(rom) + 1)
    traceable_range = range(start_address, 0xffff)
    tracer = Tracer(memory, entry_points, all_vectors, traceable_range)
    tracer.trace(disassemble)

    symbol_table = SymbolTable(uPD78213_SYMBOLS)
    symbol_table.generate(memory, start_address) # xxx should pass traceable_range

    printer = Printer(memory,
                      start_address,
                      traceable_range[-1] - 1,
                      symbol_table
                      )
    printer.print_listing()
