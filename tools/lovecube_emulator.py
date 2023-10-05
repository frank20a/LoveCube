import pygame as pg
import os, requests, json
from numpy import sin, cos, pi


class GameMaster:
    def __init__(self):
        # App parameters
        self._running = False
        self.size = self.width, self.height = 622, 622
        self.leds = [[0, 0, 0] for _ in range(7)]
        
        # App assets
        self.background = pg.image.load(os.path.join(os.getcwd(), 'server/static/img/lovecube.png'))
        
        # Server details
        self._server_url = "http://127.0.0.1:5000"
        self._api_key = ""
        self._device_id = "ABCDEF"
        
        # Initialize pygame
        pg.init()
        self._display_surf = pg.display.set_mode(self.size, pg.HWSURFACE | pg.DOUBLEBUF)
    
    def run(self):
        self._running = True
        while self._running:
            for event in pg.event.get():
                self.handle_event(event)
            self.update()
        self.cleanup()
            
    def handle_event(self, event):
        if event.type == pg.QUIT:
            self.quit()
            
    def update(self):
        self._display_surf.fill((50, 50, 50))
        self._display_surf.blit(self.background, (0, 0))
        
        for i in range(7):
            pg.draw.circle(
                self._display_surf,
                self.leds[i],
                (
                    self.width / 2 + 295 * sin(2 * (i + 5) * pi / 8),
                    self.height / 2 + 295 * cos(2 * (i + 5) * pi / 8)
                ),
                15
            )
        
        pg.display.flip()
    
    def cleanup(self):
        pg.quit()
    
    def quit(self):
        self._running = False
        print("Goodbye!")
            
            
if __name__ == "__main__":
    gm = GameMaster()
    gm.run()
