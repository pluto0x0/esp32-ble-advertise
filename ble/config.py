ws_port = 55555
method = 'wlan'   # 'ap' or 'wlan'
test_internet = True

wlan_zju = {
    'ssid': 'ZJUWLAN',
    'passwd': None,
    'config': {
        'hostname': 'esp32',
        'mac': bytes.fromhex('4074E06CE1D4'),
    },
    'ifconfig': (
        '10.107.38.232',
        '255.255.128.0',
        '10.107.0.1',
        '10.105.1.124'
    )
}

wlan_ap = {
    'ssid': "esp32wlan",
    'passwd': 'qwedsazxc',
    'config': {
        'hostname': 'esp32',
    }
}

wlan = wlan_ap

ap = {
    'ssid': 'ESP32AP',
    'passwd': '12345678',
    'config': {
        'hostname': 'esp32',
        'mac': bytes.fromhex('4074E06CE1D4'),
    }
}
