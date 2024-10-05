import network
from machine import Pin


def ap(ssid, passwd, **kwargs):
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(hostname='esp32')
    ap_if.config(essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK,
                 password=passwd)
    if 'mac' in kwargs:
        wlan.config(mac=bytes.fromhex(kwargs['mac']))
    if 'hostname' in kwargs:
        wlan.config(hostname='esp32')
    print(f'Please connect {ssid} ({passwd})')
    print_config(ap_if)


def wlan(ssid, passwd, **kwargs):
    led = Pin(2, Pin.OUT)
    led.off()
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        led.on()
        print(f'Connecting to wlan "{ssid}"...')
        wlan.active(True)
        if 'mac' in kwargs:
            wlan.config(mac=bytes.fromhex(kwargs['mac']))
        if 'hostname' in kwargs:
            wlan.config(hostname='esp32')
        wlan.connect(ssid, passwd)
        while not wlan.isconnected():
            pass
        led.off()
    print_config(wlan)


def print_config(dev):
    mac_address = ':'.join(['%02x' % b for b in dev.config('mac')])
    hostname = dev.config('hostname')
    print('ifconfig:', dev.ifconfig())
    print('MAC:', mac_address)
    print('hostname:', hostname)
