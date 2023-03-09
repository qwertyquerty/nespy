import cProfile

import pygame as pg

from nespy.bus import Bus
from nespy.cartridge import Cartridge
from nespy.operations import OPCODE_LOOKUP

pg.display.set_caption("NESPY")
pg.display.set_icon(pg.Surface((16,16)))

def main():
    nes = Bus()
    cart = Cartridge("./roms/cpu.nes")
    nes.plug_cartridge(cart)
    nes.reset()

    import time
    start = time.time()
    time.sleep(0.01)

    print(cart.mapper)

    while True:
        if (nes.cpu.clock_count & 0xFFFF) == 0:
            print(int(nes.cpu.clock_count / (time.time() - start)), "Hz", "OP:", nes.cpu.opcode)
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit()

        nes.clock()


if __name__ == "__main__":
    main()
    #cProfile.run("main()")

