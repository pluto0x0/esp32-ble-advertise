import network
import urequests


def do_ap(ssid, passwd, **kwargs):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    if passwd:
        ap.config(essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK,
                  password=passwd)
    else:
        ap.config(essid=ssid)
    set_configs(ap, kwargs)
    print(f'Please connect {ssid} ({passwd or "no password"})')
    print_config(ap)


def do_wlan(ssid, passwd, **kwargs):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print(f'Connecting to wlan "{ssid}"...')
        wlan.active(True)
        set_configs(wlan, kwargs)
        wlan.connect(ssid, passwd)
        while not wlan.isconnected():
            pass
    print_config(wlan)


def print_config(dev):
    print('============ INFO ============')
    mac_address = ':'.join(['%02x' % b for b in dev.config('mac')])
    hostname = dev.config('hostname')
    print('ifconfig:', dev.ifconfig())
    print('MAC:', mac_address)
    print('hostname:', hostname)
    print('==============================')


def set_configs(dev, kwargs):
    if 'config' in kwargs:
        config = kwargs['config']
        for k, v in config.items():
            print(f'[config] {k}: {v}')
            dev.config(**{k: v})
    if 'ifconfig' in kwargs:
        ifconfig = kwargs['ifconfig']
        assert isinstance(ifconfig, tuple)
        print('[ifconfig]', ifconfig)
        dev.ifconfig(ifconfig)


def check_internet():
    try:
        # 向httpbin发送请求，并附带自定义GET参数
        url = 'http://httpbin.org/get'
        k, v = 'birthday', '19260817'
        response = urequests.get(f'{url}?{k}={v}')

        # 检查是否返回200 OK
        if response.status_code != 200:
            return False, 'Code != 200'

        # 打印返回的内容，检查GET参数是否正确返回
        content = response.json()

        # 验证返回的参数是否与我们发送的参数一致
        if content['args'].get(k) == v:
            return True

        # 如果参数不匹配，说明可能被劫持或出现其他问题
        return False, 'Wrong return data'

    except:
        # 发生异常，表示没有连接到互联网或请求失败
        return False, 'Error'

    finally:
        # 确保关闭连接
        try:
            response.close()
        except:
            pass
