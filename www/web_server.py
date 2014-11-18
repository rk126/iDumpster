import os
from flask import Flask, render_template
import json


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

@app.route('/dumpsters.json')
def get_dumpster_data():
  return json.dumps([
                      {"name": "Dumpster 1",
                       "value": 100,
                       "location": "(1, 3)"},
                      {"name": "Dumpster 2",
                       "value": 50,
                       "location": "(5, 7)"}])

@app.route('/trucks.json')
def get_truck_data():
  return json.dumps([
                      {"name": "Truck 1",
                       "status": "Awaiting Task",
                       "location": "(6, 3)"},
                      {"name": "Truck 2",
                       "status": "Discovering the meaning of life",
                       "location": "(7, 7)"}])

@app.route('/')
def show_home():
  return render_template('cover.html')

@app.route('/run')
def show_run():
  return render_template('run.html')

@app.route('/doc')
def show_doc():
  return render_template('doc.html')
