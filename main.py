import cProfile

import pygame as pg
import numpy as np

from nespy.bus import Bus
from nespy.cartridge import Cartridge
from nespy.operations import OPCODE_LOOKUP

pg.display.set_caption("NESPY")
pg.display.set_icon(pg.Surface((16,16)))

def main():
    nes = Bus()
    cart = Cartridge("./roms/zelda.nes")
    nes.plug_cartridge(cart)
    nes.reset()

    clock = pg.time.Clock()

    import time
    start = time.time()
    time.sleep(0.01)

    print(cart.mapper)

    screen = pg.Surface((256, 240), pg.HWSURFACE|pg.HWACCEL)
    display = pg.display.set_mode((256*4, 240*4), pg.HWSURFACE|pg.HWACCEL|pg.DOUBLEBUF)

    while True:
        nes.clock()

        if nes.ppu.frame_complete:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit()

            keys = pg.key.get_pressed()
            
            nes.controllers = (
                keys[pg.K_RIGHT] | (keys[pg.K_LEFT] << 1) | (keys[pg.K_DOWN] << 2) | (keys[pg.K_UP] << 3) | (keys[pg.K_s] << 4) | (keys[pg.K_a] << 5) | (keys[pg.K_x] << 6) | (keys[pg.K_z] << 7),
                0x00
            )

            pg.surfarray.blit_array(screen, np.array(nes.ppu.spr_screen))
            pg.transform.scale_by(screen, 4, display)
            pg.display.flip()

            clock.tick(60)

            print(int(clock.get_fps()), "FPS")

            nes.ppu.frame_complete = False

if __name__ == "__main__":
    #main()
    cProfile.run("main()")

