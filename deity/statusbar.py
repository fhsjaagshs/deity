import sys
import json
from enum import Enum
from uuid import uuid4
from threading import Thread
from time import sleep

class Color(Enum):
  POSITIVE = 1
  NEUTRAL = 2
  NEGATIVE = 3

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

class StatusBar(object):
  def __init__(self,
               clicks_enabled = True,
               refresh_interval = 3.0,
               positive_color = "#FFFFFF",
               neutral_color = "#AAAAAA",
               negative_color = "#B87A84",
               items = []):
    super().__init__()
    self.items = items
    self.refresh_interval = refresh_interval
    self.clicks_enabled = clicks_enabled
    self.positive_color = positive_color
    self.neutral_color = neutral_color
    self.negative_color = negative_color

  def header(self):
    if self.clicks_enabled:
      return "{\"version\":1,\"click_events\":true}\n"
    return "{\"version\":1}\n"

  def to_dict(self, item):
    c = item.color()
    chex = None
    if c == Color.POSITIVE:
      chex = self.positive_color
    elif c == Color.NEUTRAL:
      chex = self.neutral_color
    elif c == Color.NEGATIVE:
      chex = self.negative_color

    return {
      "instance": item.guid,
      "color": chex or "#FFFFFF",
      "full_text": str(item.full_text()),
      "markup": "pango" if item.is_markup() else "none"
    }

  def __str__(self):
    return json.dumps(list(map(self.to_dict, self.items)))

  def print(self):
    sys.stdout.write(str(self) + ",\n")
    sys.stdout.flush()

  def run(self):
    sys.stdout.write(self.header() + "[\n")
    sys.stdout.flush()

    if self.clicks_enabled:
      t = Thread(target=self.read_clicks)
      t.daemon = True # no point in reading clicks for a nonexistant statusbar.
      t.start()

    self.print()
    sleep(self.refresh_interval) 
    while True:
      self.print()
      sleep(self.refresh_interval)

  def read_clicks(self):
    while True:
      for s in sys.stdin:
        j = s.strip()

        if s is not None and len(s) > 0:
          if j == "[":
            pass
          else:
            v = json.loads(s)
            instance = str(v["instance"])
            button = int(v["button"])
            if button == 1:
              for i in self.items:
                if i.guid == instance:
                  i.on_click()
    
class StatusItem(object):
  def __init__(self, **kwargs):
    super().__init__()
    self.guid = str(uuid4())

  def is_markup(self):
    return False

  def full_text(self):
    return ""

  def color(self):
    return Color.POSITIVE

  def on_click(self):
    pass
