import pygame as pg
import os, requests, json, argparse
from numpy import sin, cos, pi


class GameMaster:
    def __init__(self, api_key, device_id, charging):
        # App parameters
        self._running = False
        self.size = self.width, self.height = 622, 622
        self.leds = [[0, 0, 0] for _ in range(7)]
        self.cmd = 0
        
        # Server details
        self._server_url = "http://127.0.0.1:5000"
        self._api_key = api_key
        self._device_id = device_id
        self.report_charging = charging > 0
        self.chrg_status = True if charging == 1 else False
        
        # Initialize pygame
        pg.init()
        pg.display.set_caption(f"LoveCube Emulator - {self._device_id}")
        self._display_surf = pg.display.set_mode(self.size, pg.HWSURFACE | pg.DOUBLEBUF)
        pg.time.set_timer(pg.USEREVENT + 1, 1000 * 10)          # Get status every 10 seconds
        pg.time.set_timer(pg.USEREVENT + 2, 1000 * 60 * 2)      # Post status every 2 minutes
        
        # App assets
        self.background = pg.image.load(os.path.join(os.getcwd(), 'server/static/img/lovecube.png'))
        self.id_font = pg.font.SysFont('ArialBold', 45)
        self.btn1 = pg.Rect(50, 220, 150, 150)
        self.btn2 = pg.Rect(422, 220, 150, 150)

        # Pre-startup
        self.get_status()
        self.post_status()
    
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
        elif event.type == pg.MOUSEBUTTONDOWN:
            if self.btn1.collidepoint(pg.mouse.get_pos()):
                self.btn_click(1)
            elif self.btn2.collidepoint(pg.mouse.get_pos()):
                self.btn_click(2)
        elif event.type == pg.USEREVENT + 1:
            self.get_status()
        elif event.type == pg.USEREVENT + 2:
            self.post_status()
            
    def update(self):
        self._display_surf.fill((50, 50, 50))
        self._display_surf.blit(self.background, (0, 0))
        self._display_surf.blit(self.id_font.render(self._device_id, True, (0, 0, 0)), (self.width / 2 - 60, 35))
        
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
        
        pg.draw.rect(self._display_surf, (0, 0, 255) if self.btn1.collidepoint(pg.mouse.get_pos()) else (100, 100, 255), self.btn1)
        pg.draw.rect(self._display_surf, (0, 0, 255) if self.btn2.collidepoint(pg.mouse.get_pos()) else (100, 100, 255), self.btn2)
        
        pg.display.flip()
    
    def btn_click(self, btn) -> bool:
        print(f'Button {btn} clicked -> ', end='')
        r = requests.get(f'{self._server_url}/api/v1/trigger/{self._api_key}/{self._device_id}/{btn}', timeout=5)
        if r.status_code == 200:
            print(r.json())
            if r.json()['error'] != 0:
                return False
            return True
        return False
    
    def get_status(self) -> bool:
        print('Getting status -> ', end='')
        r = requests.get(f'{self._server_url}/api/v1/get-cmd/{self._api_key}/{self._device_id}', timeout=5)
        if r.status_code == 200:
            print(r.json())
            if r.json()['error'] != 0:
                return False
            
            if r.json()['cmd'] == 1:
                self.leds = [(148, 0, 211), (75, 0, 130), (0, 0, 255), (0, 255, 0), (255, 255, 0), (255, 127, 0), (255, 0, 0)]
            else:
                self.leds = [ [(0, 0, 0), (), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255)][r.json()['cmd']] ] * 7
            return True
        return False
    
    def post_status(self) -> bool:
        if not self.report_charging:
            return True
        
        print('Posting charge status -> ', end='')
        r = requests.put(f'{self._server_url}/api/v1/state/{self._api_key}/{self._device_id}', json={'chrg_flag': self.chrg_status, 'stby_flag': not self.chrg_status}, timeout=5)
        if r.status_code == 200:
            print(r.json())
            if r.json()['error'] != 0:
                return False
            return True
        return False
    
    def cleanup(self):
        pg.quit()
    
    def quit(self):
        self._running = False
        print("Goodbye!")
            
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="LoveCube Emulator",
        description="Emulates the LoveCube hardware for testing purposes.",
        epilog="Made by Frank Fourlas for Renia with <3."
    )
    parser.add_argument(
        "-k",
        "--api-key",
        help="The API key of the device to emulate.",
        required=True
    )
    parser.add_argument(
        "-d",
        "--device-id",
        help="The ID of the device to emulate.",
        required=True
    )
    parser.add_argument(
        "-c",
        "--charging",
        help="Whether the device is sending charging status. 0 (default): Not sending, 1: Charging, 2: Charged.",
        required=False,
        default=0,
        type=int
    )
    args = parser.parse_args()
    
    gm = GameMaster(
        args.api_key,
        args.device_id,
        args.charging
    )
    gm.run()
