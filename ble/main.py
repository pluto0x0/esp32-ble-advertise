import connect
from ubluetooth import BLE
import json
import machine
import ubinascii
from websocket_server import (
    ClientClosedError,
    WebSocketServer,
    WebSocketClient
)
import config
from machine import Pin
from utils import deepcopy


class BLEControl:
    def __init__(self):
        self.ble = BLE()
        self.ble.active(False)
        self.status = 'idle'             # idle, scanning, advertising
        self.handler = print

    def advertise(self, adv_data, gap=100):
        self.status = 'advertising'
        self.ble.active(True)
        if isinstance(adv_data, str):
            adv_data = bytes.fromhex(adv_data)
        self.ble.gap_advertise(gap, adv_data=adv_data)

    def irq(self, event, data):
        if event == 5:
            addr_type, addr, connectable, rssi, adv_data = data
            addr_str = ':'. join(f'{byte:02x}' for byte in addr)
            self.handler(addr_type, addr_str, connectable, rssi, adv_data)

    def set_handler(self, handler):
        self.handler = handler

    def scan(self, duration=10000, frac=0.1):
        self.status = 'scanning'
        self.ble.active(True)
        self.ble.irq(self.irq)
        interval = 128000
        window = int(interval * frac)
        print(frac)
        self.ble.gap_scan(duration, interval, window)

    def stop(self):
        self.ble.gap_advertise(None, None)
        self.ble.active(False)
        self.status = 'idle'


class ConfigControl:
    def __init__(self, filename):
        self.filename = filename
        self.load()

    def load(self):
        try:
            with open(self.filename, encoding='utf-8') as file:
                data = json.load(file)
                self._scanned = data['scanned']
                self._stored = data['stored']
        except BaseException:
            self._scanned = {}
            self._stored = []

    def dump(self):
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump({'scanned': self._scanned, 'stored': self._stored}, file)

    def scanned(self, value=None):
        if value is not None:
            self._scanned = value
            self.dump()
        return self._scanned

    def stored(self, value=None):
        if value is not None:
            self._stored = value
            self.dump()
        return self._stored


debug = True


class WSClient(WebSocketClient):
    ble = BLEControl()
    config = ConfigControl('ble.json')
    todo_dev = []
    buffer = ''

    def __init__(self, conn):
        super().__init__(conn)

    def process(self):
        try:
            data = self.connection.read()
            if not data:
                return
            data = data.decode("utf-8")
            self.buffer += data
            msgs = self.buffer.split('\r\n')
            for msg in msgs[:-1]:
                items = msg.split(" ")
                cmd = items[0]
                method = f'cmd_{cmd}'
                ret = f'Command not found: "{cmd}"'
                if debug:
                    print(f'command: {items}')
                if hasattr(self, method):
                    ret = getattr(self, method)(*items[1:]) or 'ok'
                self.connection.write(ret)
                if debug:
                    print(f'return: {ret}')
            self.buffer = msgs[-1]
        except ClientClosedError:
            if self.ble.status == 'scanning':
                self.ble.stop()
            self.todo_dev.clear()
            self.connection.close()

    def cmd_scan(self, duration=10, frac=0.1):
        duration = int(duration)
        frac = float(frac)

        def handler(addr_type, addr, connectable, rssi, adv_data):
            adv_data = adv_data.hex()
            self.todo_dev.append((addr, rssi, adv_data))
            print('new device!')

        self.ble.set_handler(handler)
        self.ble.scan(duration * 1000, frac)
        return self.cmd_status()
 
    def cmd_simulate(self, data):
        self.ble.advertise(data)
        return self.cmd_status()

    def cmd_stop(self):
        self.ble.stop()
        return self.cmd_status()

    def cmd_status(self):
        return f'status {self.ble.status}'

    def cmd_store(self, data=None):
        if data is None:
            ret = self.config.stored()
            # encode with base64, then dump json
            ret = ubinascii.b2a_base64(json.dumps(ret).encode('utf-8')).decode('utf-8')
            return f'stored-devices {ret}'
        if isinstance(data, str):
            # decode base64, then load json
            data = json.loads(ubinascii.a2b_base64(data).decode('utf-8'))
        self.config.stored(data)

    def loop(self):
        if not self.todo_dev:
            return
        
        state = machine.disable_irq()       # critical section
        temp = deepcopy(self.todo_dev)      # deep copy
        self.todo_dev.clear()
        machine.enable_irq(state)

        for addr, rssi, adv_data in temp:
            # self.config.scanned(self.config.scanned() | {
            #     addr: {'rssi': rssi, 'data': adv_data}})      # no need to do this
            self.connection.write(f'new-device {addr} {rssi} {adv_data}')
        

class WSServer(WebSocketServer):
    def __init__(self):
        super().__init__("index.html", 5)

    def _make_client(self, conn):
        return WSClient(conn)

    def process_all(self):
        self._check_new_connections(self._accept_conn)
        for client in self._clients:
            client.process()
            client.loop()


def main():
    led = Pin(2, Pin.OUT)
    led.on()
    if config.method == 'ap':
        connect.do_ap(**config.ap)
    elif config.method == 'wlan':
        connect.do_wlan(**config.wlan)
    if config.test_internet:
        print('Internet connection:', connect.check_internet())
    app = WSServer()
    app.start(port=config.ws_port)
    led.off()

    try:
        while True:
            app.process_all()
    except KeyboardInterrupt:
        pass
    app.stop()


if __name__ == '__main__':
    main()
