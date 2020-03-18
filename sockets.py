#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, request, redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import json


app = Flask(__name__)
sockets = Sockets(app)
app.debug = True


# Obtained from https://github.com/uofa-cmput404/cmput404-slides/blob/master/examples/WebSocketsExamples/chat.py
# Author: Abram Hindle & Hazel
class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()


class World:
    def __init__(self):
        self.clear()

    def set(self, entity, data):
        self.space[entity] = data

    def update(self, entity, key, value):
        entry = self.space.get(entity, dict())
        entry[key] = value
        self.space[entity] = entry

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity, dict())

    def world(self):
        return self.space


# Obtained from https://github.com/uofa-cmput404/cmput404-slides/blob/master/examples/WebSocketsExamples/chat.py
# Author: Abram Hindle & Hazel
def send_all(msg):
    for client in clients:
        client.put(msg)


# Obtained from https://github.com/uofa-cmput404/cmput404-slides/blob/master/examples/WebSocketsExamples/chat.py
# Author: Abram Hindle & Hazel
def send_all_json(obj):
    send_all(json.dumps(obj))


def generate_OK_json_response(data):
    response = app.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json')
    return response


# I give this to you, this is how you get the raw body/data portion of a post
# in flask this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json is not None):
        return request.json
    elif (request.data is not None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])


myWorld = World()
clients = list()


@app.route('/')
def hello():
    '''Redirect to /static/index.html '''
    return redirect("/static/index.html")


# Obtained from https://github.com/uofa-cmput404/cmput404-slides/blob/master/examples/WebSocketsExamples/chat.py
# Author: Abram Hindle & Hazel
def read_ws(ws, client):
    '''A greenlet function to read from the websocket and updates the world'''
    try:
        while True:
            msg = ws.receive()
            if (msg is not None):
                packet = json.loads(msg)
                send_all_json(packet)
                for entity in packet:
                    myWorld.set(entity, packet[entity])
            else:
                break
    except Exception as e:
        '''Done'''
        print("Error: %s" % e)


# Obtained from https://github.com/uofa-cmput404/cmput404-slides/blob/master/examples/WebSocketsExamples/chat.py
# Author: Abram Hindle & Hazel
@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    client = Client()
    clients.append(client)
    g = gevent.spawn(read_ws, ws, client)
    try:
        # current_world = json.dumps(myWorld.world())
        # ws.send(current_world)
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:  # WebSocketError as e:
        print("WS Error %s" % e)
    finally:
        clients.remove(client)
        gevent.kill(g)


@app.route("/entity/<entity>", methods=['POST', 'PUT'])
def update(entity):
    '''update the entities via this interface'''
    data = flask_post_json()
    for key in data:
        myWorld.update(entity, key, data[key])
    return generate_OK_json_response(data)


@app.route("/world", methods=['POST', 'GET'])
def world():
    '''you should probably return the world here'''
    data = myWorld.world()
    return generate_OK_json_response(data)


@app.route("/entity/<entity>")
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation
    of the entity'''
    data = myWorld.get(entity)
    return generate_OK_json_response(data)


@app.route("/clear", methods=['POST', 'GET'])
def clear():
    '''Clear the world out!'''
    data = dict()
    myWorld.clear()
    send_all_json({})
    return generate_OK_json_response(data)


if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
