import time

import pandas as pd
from celery import Celery
from dash import MATCH
from dash import CeleryManager
from dash import ClientsideFunction
from dash import Dash
from dash import DiskcacheManager
from dash import dash_table
from dash import dcc
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import NoOutputTransform
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform
from redis import Redis

REDIS_URL = 'redis://127.0.0.1:6379'


def value_count(data):
    if not data:
        return 0

    return sum(map(len, data.values()))


def get_queue():
    inspect = celery_app.control.inspect()

    return {
        'active': value_count(inspect.active()),
        'reserved': value_count(inspect.reserved()),
        'scheduled': value_count(inspect.scheduled()),
    }


def get_stats():
    return celery_app.control.inspect().stats()


celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
manager = CeleryManager(celery_app)

app = DashProxy(
    __name__,
    background_callback_manager=manager,
    transforms=[ServersideOutputTransform(
        backend=RedisStore(host=REDIS_URL)
    ), NoOutputTransform()],
)

server = app.server
assert server is not None

app.layout = html.Div([
    html.Button('Start', 'start'),
    html.Progress(id='progress', value='0'),
    html.Pre(id='queue-output'),
    html.Pre(id='result'),
])


app.clientside_callback(
    ClientsideFunction(
        namespace='cx',
        function_name='pollQueue',
    ),
    Output('queue-output', 'children'),
    Input('start', 'n_clicks'),
)


@app.callback(
    Output('result', 'children'),
    Input('start', 'n_clicks'),
    background=True,
    prevent_initial_call=True,
    progress=[
        Output('progress', 'value'),
        Output('progress', 'max'),
    ],
)
def update_data(set_progress, n):
    n = n * 10

    for i in range(n + 1):
        set_progress((str(i), str(n)))
        time.sleep(1)

    return str(n)


@server.route('/celery-queue')
def celery_queue():
    return get_queue()


@server.route('/celery-stats')
def celery_stats():
    return get_stats() or {}


app.register_celery_tasks()

if __name__ == '__main__':
    app.run_server(debug=True)
