import os
from flask import Flask, render_template


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

@app.route('/')
def show_home():
  return render_template('cover.html')

@app.route('/run')
def show_run():
  return render_template('run.html')

@app.route('/doc')
def show_doc():
  return render_template('doc.html')
