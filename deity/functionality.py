from .hardware.audio import Audio, Input, Output, Stream
from time import sleep
import json
from deity.statusitems.date import Date
from deity.statusitems.volume import Volume
from deity.statusitems.network import Network
from deity.statusitems.brightness import Brightness
from deity.statusitems.battery import Battery
from deity.statusbar import StatusBar

# TODO: call IPC when any of these change values.
# { "command": "i3bar", "kwargs": {} }
# will update the statusbar

def Functionality(key):
  print(key)
  return {
    "audio": AudioFunctionality,
    "brightness": BrightnessFunctionality,
    "screenshot": ScreenshotFunctionality,
    "i3bar": i3barFunctionality
  }.get(key, i3barFunctionality)()

class AudioFunctionality(object):
  def go(self,
         list_outputs = False, toggle_mute = False,
         output = None, input = None,
         adjust_volume = None, sanitize = False):
    with Audio("desktop.py") as a:
      if list_outputs:
        for o in a.outputs:
          print(str(o))

      if toggle_mute:
        a.output.muted = not a.output.muted

      if output != None:
        a.output = output

      if adjust_volume != None:
        a.output.volume = a.output.volume + int(adjust_volume)

      if args.sanitize:
        a.collect_streams()
        for o in a.outputs():
          if o != a.output:
            o.suspend()
        for i in a.inputs():
          if i != a.input:
            i.suspend()

class BrightnessFunctionality(object):
  def go(self,
         backlight = "intel_backlight",
         backlight_class = "backlight",
         set = None, adjust = None
         ):
    if aset is not None:
      set_brightness(backlight, set, backlight_class)
    else:
      b = get_brightness(backlight, backlight_class)
      if b is not None:
        if adjust is not None:
          set_brightness(backlight, b + adjust, backlight_class)
        else:
          sys.stdout.write(str(b) + '%\n')
      else:
        sys.stdout.write("failed to read brightness.\n")
      sys.stdout.flush()

class ScreenshotFunctionality(object):
  def go(self, destination = "~/Pictures/screenshots"):
    os.system("mkdir -p " + destination)
    os.system("swaygrab " + destination.rstrip('/') + time.strftime("/%-m-%-d-%y_%-H:%M:%S.png"))

statusbar = None

class i3barFunctionality(object):
  def go(self, **kwargs):
    global statusbar
    if not statusbar: 
      statusbar = StatusBar(items = [
        Brightness(backlight = kwargs.get("backlight", "intel_backlight"),
                   backlight_class = kwargs.get("backlight_class", "backlight")),
        Volume(**kwargs),
        Battery(**kwargs),
        Network(text = "WiFi", interface = kwargs.get("wifi_iface", "wlp3s0")),
        Network(text = "VPN", interface = kwargs.get("vpn_iface", "tun0")),
        Date(**kwargs)
      ], **kwargs)
      statusbar.run()
    else:
      statusbar.print()

