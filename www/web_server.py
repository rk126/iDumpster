import os
from flask import Flask, render_template
import json

import time

# Create a web application
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    APP_ROOT=os.path.dirname(os.path.realpath(__file__)),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def demo_dumpster_data():
  s = int(time.time() % 10)
  return json.dumps([
                      {"name": "Dumpster 1",
                       "trash_level": s,
                       "location": {"y": 1,
                                    "x": 3}},
                      {"name": "Dumpster 2",
                       "trash_level": s*2,
                       "location": {"y": 5,
                                    "x": 6}}])

def demo_truck_data():
  s = int(time.time() % 10)
  if s > 5:
    return json.dumps([
                        {"name": "Truck 1",
                         "status": "Awaiting Task",
                         "fuel_level": 0.50,
                         "trash_level": 0.2,
                         "location": {"y": 2,
                                      "x": 4}},
                        {"name": "Truck 2",
                         "status": "Discovering meaning of life",
                         "fuel_level": 0.55,
                         "trash_level": 0.21,
                         "location": {"y": 5,
                                      "x": 6}}])
  else:
    return json.dumps([
                        {"name": "Truck 1",
                         "status": "Finding Nemo",
                         "fuel_level": 0.30,
                         "trash_level": 0.5,
                         "location": {"y": 3,
                                      "x": 3}},
                        {"name": "Truck 2",
                         "status": "Calculating Pi... on first slice",
                         "fuel_level": 0.10,
                         "trash_level": 0.90,
                         "location": {"y": 7,
                                      "x": 7}}])

def demo_map_data():
  s = int(time.time() % 10)
  if s == 0:
    return '''
------------------------
-----D--#####-----------
----###-----------------
----#####---------------
-----------------T------
---###########----------
'''
  elif s == 1:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@@@@---------
----#####------@--------
----------------@T------
---###########----------
'''
  elif s == 2:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@@@@---------
----#####------@--------
----------------T-------
---###########----------
'''
  elif s == 3:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@@@@---------
----#####------T--------
------------------------
---###########----------
'''
  elif s == 4:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@@@T---------
----#####---------------
------------------------
---###########----------
'''
  elif s == 5:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@@T----------
----#####---------------
------------------------
---###########----------
'''
  elif s == 6:
    return '''
------------------------
-----D@@#####-----------
----###@@@@@T-----------
----#####---------------
------------------------
---###########----------
'''
  elif s == 7:
    return '''
------------------------
-----D@@#####-----------
----###@@@@T------------
----#####---------------
------------------------
---###########----------
'''
  elif s == 8:
    return '''
------------------------
-----D@@#####-----------
----###@@@T-------------
----#####---------------
------------------------
---###########----------
'''
  elif s == 9:
    return '''
------------------------
-----D@@#####-----------
----###@@T--------------
----#####---------------
------------------------
---###########----------
'''
  else:
    return '''You didn't say the magic word'''

_dumpster_cb = demo_dumpster_data
_truck_cb = demo_truck_data
_map_cb = demo_map_data

def start(dumpster_cb=demo_dumpster_data,
          truck_cb=demo_truck_data,
          map_cb=demo_map_data):
  global app
  global _dumpster_cb
  global _truck_cb
  global _map_cb

  _dumpster_cb = dumpster_cb
  _truck_cb = truck_cb
  _map_cb = map_cb

  print("Starting webserver with callbacks as")
  print("-------------------------------------")
  print("Dumpster: " + str(_dumpster_cb))
  print("Truck: " + str(_truck_cb))
  print("Map: " + str(_map_cb))
  print("-------------------------------------")

  app.run(host="0.0.0.0", port=80, debug=True)

@app.route('/dumpsters.json')
def get_dumpster_data():
  return _dumpster_cb()

@app.route('/trucks.json')
def get_truck_data():
  return _truck_cb()

@app.route('/map.txt')
def get_map_data():
  return _map_cb()

@app.route('/')
def show_home():
  return render_template('cover.html')

@app.route('/run')
def show_run():
  return render_template('run.html')

@app.route('/doc')
def show_doc():
  return render_template('doc.html')
