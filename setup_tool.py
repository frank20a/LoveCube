from serial import Serial
from serial.tools import list_ports
import struct, time


class Tool:
    def __init__(self):
        print("""
        =========================================================================

        | |                        /  __ \       | |                       /  | 
        | |      ___  __   __  ___ | /  \/ _   _ | |__    ___      __   __ `| | 
        | |     / _ \ \ \ / / / _ \| |    | | | || '_ \  / _ \     \ \ / /  | | 
        | |____| (_) | \ V / |  __/| \__/\| |_| || |_) ||  __/      \ V /  _| |_
        \_____/ \___/   \_/   \___| \____/ \__,_||_.__/  \___|       \_/(_)\___/

        =========================================================================""")
        print("Welcome to the setup tool for your LoveCube v.1\n\n")

        # Select the serial port
        print("Available serial ports:")
        print('\n'.join([f'\t{i+1}) {port.device} - {port.description}' for i, port in enumerate(list_ports.comports())]))
        self.ser = Serial(list_ports.comports()[int(input("Select the serial port: ")) - 1].device, 115200, timeout=1)
        
        # Connect to the cube
        time.sleep(1)
        while self.ser.in_waiting > 0:
            self.ser.read()
        r, _ = self.send_cmd(0x00)
        if r == 0x01:
            print("Connection established!")
        else:
            raise Exception("Connection error")
        
    def main(self):
        cmd = ' '
        while cmd != 'q':
            cmd = input(
"""\nOptions:
    1) Reconfigure
    2) Get Device UID
    3) Get Charging Status
    4) Get Local IP Address
    q) Quit
    * Option under construction
What do you want to do? """)
            
            if cmd < '1' or cmd > '4':
                continue
            
            try:
                resp, data = self.send_cmd(int(cmd))
                print(f"Devices responeded with \"{hex(resp)}\" containing the following data:\n{data}")
            except Exception as e:
                print(e)
                continue
    
    def send_cmd(self, cmd: int, arg1: int = 0, arg2: int = 0):
        # Send command
        msg = struct.pack('>BBBB', cmd, arg1, arg2, (cmd + arg1 + arg2) % 256)
        self.ser.write(msg)
        self.ser.flush()
        
        # Get response
        _msg = self.ser.read(9)
        try:
            msg = struct.unpack('>BBBBBBBBB', _msg)
            _cmd = msg[0]
            _resp = msg[1]
            _data = msg[2:8]
            _checksum = msg[8]
        except struct.error:
            print(f"Invalid response format... Got {_msg}")
            return
        
        # Check Errors
        if _checksum != (sum(_data) + _resp + _cmd) % 256:
            raise Exception("Checksum error")
        if _resp == 0xFD:
            raise Exception("Invalid command")
        if _resp == 0xFE:
            raise Exception("Communication error")
        if _resp == 0xFF:
            raise Exception("Unknown error")
        if _cmd != cmd:
            raise Exception("Command error")
        
        # Return response
        return _resp, _data


if __name__ == '__main__':
    tool = Tool()
    tool.main()
