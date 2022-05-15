import json

from flask import Flask, request

from api import Api

import env

app = Flask(__name__)


@app.route('/api/lives', methods=['POST'])
def live_page():
    return Api.lives(request.data)


@app.route('/api/info', methods=['GET'])
def info():
    data = json.loads(open('information.json').read())
    return {
        'content': data,
        'success': True,
        'message': ''
    }


@app.route('/api/live', methods=['POST'])
def live():
    return Api.live(request.data)
