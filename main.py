import cProfile

from nespy.bus import Bus
from nespy.cartridge import Cartridge
from nespy.operations import OPCODE_LOOKUP

def main():
    nes = Bus()
    cart = Cartridge("./roms/all_instrs.nes")
    nes.plug_cartridge(cart)
    nes.reset()

    import time
    start = time.time()
    time.sleep(0.01)

    while True:
        if (nes.cpu.clock_count & 0xFFFFF) == 0:
            print(int(nes.cpu.clock_count / (time.time() - start)), "Hz", "OP:", nes.cpu.opcode)
            pass

        nes.clock()


if __name__ == "__main__":
    main()
    #cProfile.run("main()")

