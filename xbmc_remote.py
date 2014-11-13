import json
import logging

# noinspection PyUnresolvedReferences
import requests
from yoctopuce.yocto_anbutton import *
from yoctopuce.yocto_api import *
from yoctopuce.yocto_display import *
from yoctopuce.yocto_colorled import *

display_list = []


class SimpleXMBC(object):
    def __init__(self, host, port, user, password):
        self._password = password
        self._user = user
        self._port = port
        self._host = host
        self._id = 1
        self._url = 'http://%s:%d/jsonrpc' % (self._host, self._port)

    def json_rpc_request(self, method, params):
        headers = {'content-type': 'application/json'}
        # Example echo method
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0,
        }
        response = requests.post(
            self._url, data=json.dumps(payload), headers=headers).json()
        if 'error' in response:
            print(response['error'])
        return response

    def get_info_to_display(self):

        res = self.json_rpc_request('Player.GetActivePlayers', {})
        if 'result' in res and len(res['result']) > 0:
            player_id = res['result'][0]['playerid']
            player_type = res['result'][0]['type']
        else:
            return 0, "not playing anything"

        params = {"playerid": player_id, "properties": ["percentage"]}
        res = self.json_rpc_request('Player.GetProperties', params)
        if 'result' in res:
            percentage = res['result']['percentage']
        else:
            percentage = 0

        params = {"playerid": player_id,
                  "properties": ["title", "album", "artist", "season", "episode", "duration", "showtitle", "tvshowid",
                                 "thumbnail", "file", "fanart", "streamdetails"]}
        res = self.json_rpc_request('Player.GetItem', params)
        if 'result' in res:
            if player_type == "audio":
                info = res['result']['item']['title'] + " (" + res['result']['item']['artist'][0] + ")"
            else:
                info = res['result']['item']['label']
        else:
            info = "not playing anything"
        return percentage, info

    def up(self):
        self.json_rpc_request('Input.Up', {})
        print("up)")

    def down(self):
        self.json_rpc_request('Input.down', {})
        print('down')

    def left(self):
        self.json_rpc_request('Input.Left', json.loads('{}'))
        print('left')

    def right(self):
        self.json_rpc_request('Input.Right', json.loads('{}'))
        print('right')

    def ok(self):
        print('ok')
        self.json_rpc_request('Input.Select', json.loads('{}'))

    def back(self):
        self.json_rpc_request('Input.Back', json.loads('{}'))
        print('back')


xbmc_interface = SimpleXMBC('localhost', 8080, 'xbmc', '')


def init_screen(ydisplay):
    """
    :type ydisplay: YDisplay
    """
    ydisplay.resetAll()
    w = ydisplay.get_displayWidth()
    h = ydisplay.get_displayHeight()
    layer1 = ydisplay.get_displayLayer(1)
    layer1.selectGrayPen(0)
    layer1.drawBar(0, 0, w - 1, h - 1)
    layer1.selectGrayPen(255)
    layer1.drawText(w / 2, h / 2, YDisplayLayer.ALIGN.CENTER, "detected!")


def an_button_callback(anbutton, value):
    """
    :type value: str
    :type anbutton: YAnButton
    """
    if (anbutton.get_isPressed() == YAnButton.ISPRESSED_TRUE):
        last = anbutton.get_userData()
        if last == YAnButton.ISPRESSED_FALSE:
            print("send command for " + anbutton.get_friendlyName())
            funcid = anbutton.get_functionId()
            if funcid == 'anButton1':
                xbmc_interface.up()
            elif funcid == 'anButton2':
                xbmc_interface.down()
            elif funcid == 'anButton3':
                xbmc_interface.left()
            elif funcid == 'anButton4':
                xbmc_interface.right()
            elif funcid == 'anButton5':
                xbmc_interface.ok()
            elif funcid == 'anButton6':
                xbmc_interface.back()
    anbutton.set_userData(anbutton.get_isPressed())


def device_arrival(module):
    """
    :type module: YModule
    """
    serial_number = module.get_serialNumber()
    print("plug of " + serial_number)
    product = module.get_productName()
    if (product == "Yocto-MaxiDisplay") or product == "Yocto-Display":
        display = YDisplay.FindDisplay(serial_number + ".display")
        init_screen(display)
        display_list.append(display)
        for i in range(1, 7):
            button = YAnButton.FindAnButton("%s.anButton%d" % (serial_number, i))
            button.set_userData(button.get_isPressed())
            button.registerValueCallback(an_button_callback)


def device_removal(module):
    print("unplug of " + module.get_serialNumber())


def main():
    errmsg = YRefParam()
    YAPI.InitAPI(0, errmsg)
    YAPI.RegisterDeviceArrivalCallback(device_arrival)
    YAPI.RegisterDeviceRemovalCallback(device_removal)

    if YAPI.RegisterHub("usb", errmsg) < 0:
        print("Unable register usb :" + str(errmsg))
        return -1

    try:
        while True:
            progress, title = xbmc_interface.get_info_to_display()
            for display in display_list:
                w = display.get_displayWidth()
                h = display.get_displayHeight()
                layer0 = display.get_displayLayer(0)
                layer0.selectGrayPen(0)
                layer0.drawBar(0, 0, w - 1, h - 1)
                layer0.selectGrayPen(255)
                layer0.drawText(w / 2, h / 2, YDisplayLayer.ALIGN.CENTER, title)
                if progress > 0:
                    layer0.drawBar(0, h - 1, int(progress * w / 100), h - 1)
                display.swapLayerContent(0, 1)
            YAPI.UpdateDeviceList()
            YAPI.Sleep(1000)

    except KeyboardInterrupt:
        print("exit with Ctrl-C")
        return -1


if __name__ == '__main__':
    main()