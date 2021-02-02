import eventlet

eventlet.monkey_patch()

import threading
import time
from contextlib import closing
import yaml
import os
from typing import List, Tuple, Dict

from flask import Flask, render_template
from flask_socketio import SocketIO

from flighttracker import utils
from flighttracker.database import DB

app = Flask(__name__)
logger = utils.setup_logging()
socketio = SocketIO(app, async_mode='eventlet', logger=True, engineio_logger=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/about', methods=['GET'])
def about():
    return render_template("about.html")


@app.route('/contacts', methods=['GET'])
def contacts():
    return render_template("contacts.html")


@socketio.on("connect")
def connect() -> None:
    print("connected")
    logger.info("A client has been connected to the server")


@socketio.on("disconnect")
def disconnect() -> None:
    print("disconnected")
    logger.info("A client has been disconnected from the server")


states_memo = None


def fetch_vectors(dbname, user, password, host, port) -> None:
    with closing(DB(dbname=dbname, user=user, password=password, host=host, port=port)) as db:
        while True:
            logger.info("Fetching from DB has started")
            vectors, quantity = db.get_last_inserted_state()
            global states_memo
            states_memo = vectors
            logger.info(
                f"Quantity of state vectors fetched from the DB for the time {vectors[0][0]}: "
                f"{quantity}"
            )
            time.sleep(4)


def make_object(vectors: List[Tuple] or None) -> List[Dict] or None:
    if vectors is None:
        return None
    objects = []
    for i in range(0, len(vectors)):
        vector_object = {'requestTime': vectors[i][0], 'icao24': vectors[i][1], 'callsign': vectors[i][2],
                         'originCountry': vectors[i][3], 'timePosition': vectors[i][4], 'lastContact': vectors[i][5],
                         'longitude': vectors[i][6], 'latitude': vectors[i][7], 'baroAltitude': vectors[i][8],
                         'onGround': vectors[i][9], 'velocity': vectors[i][10], 'trueTrack': vectors[i][11],
                         'verticalRate': vectors[i][12], 'sensors': vectors[i][13], 'geoAltitude': vectors[i][14],
                         'squawk': vectors[i][15], 'spi': vectors[i][16], 'positionSource': vectors[i][17]}

        objects.append(vector_object)
    return objects


def broadcast_vectors() -> None:
    while True:
        vector_object = make_object(states_memo)
        socketio.send(vector_object)
        eventlet.sleep(3)
        time.sleep(1)


def start_app() -> None:
    socketio.run(app, host='0.0.0.0', log_output=True)
    eventlet.sleep(0.1)


def start_webapp() -> None:
    script_dir = os.path.abspath(__file__ + "/../../../")
    rel_path = 'config/config.yaml'
    path = os.path.join(script_dir, rel_path)

    with open(path, 'r') as cnf:
        parsed_yaml_file = yaml.load(cnf, Loader=yaml.FullLoader)
        dbname = parsed_yaml_file['postgres']['pg_dbname']
        user_name = parsed_yaml_file['postgres']['pg_username']
        password = parsed_yaml_file['postgres']['pg_password']
        hostname = parsed_yaml_file['postgres']['pg_hostname']
        port_number = parsed_yaml_file['postgres']['pg_port_number']

    fetching_thread = threading.Thread(target=fetch_vectors, daemon=True,
                                       args=(dbname, user_name, password, hostname, port_number))
    fetching_thread.start()
    broadcasting_greenthread = eventlet.spawn(broadcast_vectors)
    app_launch_greenthread = eventlet.spawn(start_app)
    app_launch_greenthread.wait()
    broadcasting_greenthread.wait()
    fetching_thread.join()


if __name__ == "__main__":
    start_webapp()
