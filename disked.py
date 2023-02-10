import time

import diskcache
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
from redis import Redis

cache = diskcache.Cache()
manager = DiskcacheManager(cache)

app = DashProxy(
    __name__,
    background_callback_manager=manager,
    transforms=[NoOutputTransform()],
)

server = app.server
assert server is not None

app.layout = html.Div([
    html.Button('Start', 'start'),
    html.Progress(id='progress', value='0'),
    html.Pre(id='queue-output'),
    html.Pre(id='result'),
    dcc.Interval('interval'),
])


@app.callback(
    Output('queue-output', 'children'),
    Input('interval', 'n_intervals')
)
def poll(n):
    result = []
    for key in cache.iterkeys():
        print(cache[key])
        result.append(key)

    return result


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
    for key in cache.iterkeys():
        print(key)
    n = n * 10

    for i in range(n + 1):
        set_progress((str(i), str(n)))
        time.sleep(1)

    return str(n)


app.register_celery_tasks()

if __name__ == '__main__':
    app.run_server(debug=True)
