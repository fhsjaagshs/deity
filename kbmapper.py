#!/usr/bin/env python3

# IDEA:
# Use evdev and the system locale to bind key combinations to
# arbitrary shell commands.

# Configuration:
# 
# Typical GLib key-value config format. Each section represents
# a stimulus:
# 
# - `lid_open`
# - `lid_close`
# - `headphones_in`
# - `headphones_out`
# - XKB keysyms composed together with `+`
#
# For each section, there is a single key, `Exec`. When this
# stimulus is activated, the command specified by `Exec` will
# be executed.
#
# Config is either stored in /etc/kbmapper/kbmapper.conf
# or in separate files /etc/kbmapper/kbmapper.d/*.conf
#
# Typical linux config precendence follows.

# TODO: 
# 1. Stop event propagation if an event is recognized
# 2. Detect new devices (hotplug)
# 3. Multitouch gestures for trackpads

import configparser
import atexit
import asyncio
import evdev
from xkbcommon import xkb
import sys
import os
import signal

#
## XKB Keysyms
#

ctx = xkb.Context()
keymap = ctx.keymap_new_from_names()
state = keymap.state_new()

def map_keycode(keycode):
  if type(keycode) is str:
    return keycode
  
  raw = xkb.keysym_get_name(state.key_get_one_sym(keycode + keymap.min_keycode() - 1))
  if raw == "NoSymbol":
    return None
  elif '_' in raw:
    return raw.split('_')[0]
  else:
    return raw

#
## Configuration
#

def ls(direc):
  xs = []
  for dpth, _, fnames in os.walk(direc):
    for f in fnames:
      xs.append(os.path.abspath(os.path.join(dpth, f)))
  return xs

def load_config(f):
  c = configparser.ConfigParser()
  c.read(f)
  return c

paths = ls("/etc/kbmapper/kbmapper.d/")
paths.append("/etc/kbmapper/kbmapper.conf")
configs = list(map(load_config, paths))

#
## Event Handling
#

# TODO: order-independent config matching
def emit(keysym):
  for cfg in configs:
    if keysym in cfg:
      v = cfg[keysym]
      cmd = v.get("Exec", None) # Command to execute on event
      if cmd is not None:
        user = v.get("User", None) # User to execute command as
        workdir = v.get("WorkingDirectory", None) # Directory to execute command in
        print(os.system(cmd))
        return True
  return False

#
## Event Implementation
#

keystack = []

def handle_event(code, typ, value):
  global keystack
  print(code, typ, value)
  if typ is 1: # Key action
    if value is 1: # press down
      if code not in keystack:
        keystack.append(code)
    elif value is 0: # lift up
      if code in keystack:
        if emit('+'.join(list(map(map_keycode,keystack)))):
          keystack = []
        else:
          keystack.remove(code)
  elif typ is 5:
    if code is 0: # lid event
      emit("LidOpen" if value is 0 else "LidClose")
    elif code is 2: # headphone jack event
      emit("HeadphonesIn" if value is 1 else "HeadphonesOut")

@asyncio.coroutine
def listen_events(d):
  cur_ev = None
  while True:
    events = yield from d.async_read()
    for e in events:
      if e.type is 0: # EV_SYN
        if cur_ev is not None:
          # TODO: handle EV_SYN behavior
          handle_event(cur_ev.code, cur_ev.type, cur_ev.value)
          cur_ev = None
      else:
        cur_ev = e

#
## Main
#

def main(args):
  for fn in evdev.list_devices():
    d = evdev.InputDevice(fn)
    c = d.capabilities()
    if 1 in c or 5 in c: # 1 is EV_KEY and 5 is EV_SW
      asyncio.async(listen_events((d)))

  loop = asyncio.get_event_loop()
  
  def signal_handler(signal, frame):
    loop.stop()
    sys.exit(0)

  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  loop.run_forever()

main(sys.argv)
